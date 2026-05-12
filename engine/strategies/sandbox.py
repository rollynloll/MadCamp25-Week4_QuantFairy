from __future__ import annotations

import ast
import hashlib
import math
import statistics
import traceback
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from engine.strategies.base import StrategySignal, StrategyContext
from engine.strategies.spec import PythonBody


# 사용자가 제출하는 Python 전략의 엔트리포인트 식별자.
# 이 문자열이 전략 entrypoint로 지정되면 샌드박스를 통해 실행된다.
PYTHON_ENTRYPOINT = "__python__"
PYTHON_META_KEY = "__python__"
MAX_CODE_SIZE = 200_000    # 코드 최대 길이 (200KB). 과도하게 큰 코드 차단
DEFAULT_TIMEOUT_SEC = 12.0  # 전략 실행 기본 타임아웃 (초)


# 샌드박스 실행 중 발생하는 모든 오류를 표현하는 예외.
# AST 검증 실패, 금지된 내장 함수 사용, 실행 타임아웃 등을 포함한다.
class StrategySandboxError(Exception):
    pass


# 샌드박스 내에서 사용자 코드에 노출되는 안전한 pandas 래퍼.
# pd.read_csv, pd.read_excel 등 파일/네트워크 접근 함수는 노출하지 않는다.
# 데이터 분석에 필요한 핵심 타입과 유틸리티 함수만 제공한다.
class SafePandas:
    Series = pd.Series
    DataFrame = pd.DataFrame
    Timestamp = pd.Timestamp
    NA = pd.NA
    to_datetime = staticmethod(pd.to_datetime)
    isna = staticmethod(pd.isna)
    notna = staticmethod(pd.notna)


# 사용자 코드의 __builtins__로 주입되는 허용된 내장 함수 목록.
# 이 목록에 없는 내장 함수는 사용자 코드에서 접근 불가능하다.
SAFE_BUILTINS: Dict[str, Any] = {
    "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
    "range": range, "enumerate": enumerate, "zip": zip, "sorted": sorted,
    "float": float, "int": int, "str": str, "bool": bool,
    "dict": dict, "list": list, "set": set, "tuple": tuple,
}

# 이름으로 직접 사용을 금지하는 내장 식별자 목록.
# __import__, eval, exec 등은 샌드박스 탈출에 사용될 수 있다.
_BANNED_NAMES = {
    "__import__", "eval", "exec", "open", "compile", "input",
    "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr",
    "help", "type", "object", "super", "memoryview",
    "classmethod", "staticmethod", "breakpoint",
}

# 허용되는 AST 노드 타입 화이트리스트.
# 이 목록에 없는 AST 노드(예: Import, While, AsyncDef)는 즉시 거부된다.
# 반복문은 for만 허용하고, while은 무한 루프 위험이 있으므로 금지한다.
_ALLOWED_NODES = (
    ast.Module, ast.FunctionDef, ast.arguments, ast.arg,
    ast.Return, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Pass,
    ast.Name, ast.Load, ast.Store, ast.Constant,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.If, ast.For, ast.Break, ast.Continue,
    ast.Call, ast.Attribute, ast.Subscript, ast.Slice,
    ast.List, ast.Tuple, ast.Dict, ast.Set,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
    ast.comprehension, ast.IfExp,
)


class _StrategyAstValidator(ast.NodeVisitor):
    # AST를 순회하며 허용되지 않은 패턴을 검사하는 방문자 클래스.
    # generic_visit에서 화이트리스트 외 노드를 모두 거부한다.

    def generic_visit(self, node: ast.AST) -> None:
        # 모든 노드가 이 메서드를 통과한다.
        # _ALLOWED_NODES에 없는 노드 타입이면 즉시 오류를 발생시킨다.
        if not isinstance(node, _ALLOWED_NODES):
            raise StrategySandboxError(f"Unsupported syntax: {type(node).__name__}")
        super().generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        # import 문은 외부 패키지를 로드하여 샌드박스를 우회할 수 있으므로 전면 금지
        raise StrategySandboxError("Import statements are not allowed")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # from ... import 문도 동일하게 금지
        raise StrategySandboxError("Import statements are not allowed")

    def visit_While(self, node: ast.While) -> None:
        # while 루프는 무한 루프로 타임아웃 없이 서버를 점유할 수 있으므로 금지
        raise StrategySandboxError("While loops are not allowed")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # 언더스코어로 시작하는 속성(예: __class__, __dict__)은 내부 구조 접근이므로 금지
        if node.attr.startswith("_"):
            raise StrategySandboxError("Private attributes are not allowed")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # 금지된 내장 함수 이름을 변수명으로 사용하는 것도 차단
        if node.id in _BANNED_NAMES:
            raise StrategySandboxError(f"Use of '{node.id}' is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # 함수 호출에서 금지된 이름이 사용되는지 검사
        func = node.func
        if isinstance(func, ast.Name) and func.id in _BANNED_NAMES:
            raise StrategySandboxError(f"Use of '{func.id}' is not allowed")
        if isinstance(func, ast.Attribute) and func.attr in _BANNED_NAMES:
            raise StrategySandboxError(f"Use of '{func.attr}' is not allowed")
        self.generic_visit(node)


def validate_python_strategy(code: str, entrypoint: str) -> None:
    # 사용자 제출 코드를 AST 레벨에서 검증한다.
    # 1. 코드 크기 제한 확인
    # 2. 파이썬 문법 오류 확인 (ast.parse)
    # 3. entrypoint 함수가 정의되어 있는지 확인
    # 4. AST 노드 화이트리스트 검사 (_StrategyAstValidator)
    # 이 함수가 통과하면 코드를 실행해도 안전하다고 판단한다.
    if not code or not code.strip():
        raise StrategySandboxError("Python code is empty")
    if len(code) > MAX_CODE_SIZE:
        raise StrategySandboxError("Python code is too large")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise StrategySandboxError(f"Syntax error: {exc.msg}") from exc

    # 코드 최상위 레벨에서 정의된 함수 이름 목록을 추출
    defined = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    if entrypoint not in defined:
        raise StrategySandboxError(f"Entrypoint '{entrypoint}' is not defined")

    validator = _StrategyAstValidator()
    validator.visit(tree)


def hash_code(code: str) -> str:
    # 코드 문자열의 SHA-256 해시 앞 12자리를 반환한다.
    # 코드 변경 여부를 빠르게 감지하는 데 사용한다 (버전 추적).
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:12]


def extract_python_body(params: Dict[str, Any]) -> Tuple[Dict[str, Any], PythonBody | None]:
    # params 딕셔너리에서 Python 전략 메타데이터를 추출하고 PythonBody 객체로 변환한다.
    # PYTHON_META_KEY("__python__")가 params에 있으면 해당 값을 PythonBody로 파싱한다.
    # 나머지 params는 정리된 딕셔너리로 반환하며, PYTHON_META_KEY 항목은 제거한다.
    # 반환: (정리된 params, PythonBody | None)
    if not params:
        return {}, None
    raw = params.get(PYTHON_META_KEY)
    if not isinstance(raw, dict):
        return dict(params), None
    body = PythonBody.model_validate(raw)
    cleaned = dict(params)
    cleaned.pop(PYTHON_META_KEY, None)
    return cleaned, body


def _safe_exec(code: str) -> Dict[str, Any]:
    # 검증된 코드를 제한된 글로벌 네임스페이스에서 실행한다.
    # __builtins__를 SAFE_BUILTINS로 대체하여 위험한 내장 함수를 차단한다.
    # 실행 결과(함수 정의 포함)를 딕셔너리로 반환한다.
    safe_globals: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "pd": SafePandas(),      # 안전한 pandas 서브셋
        "math": math,            # math 모듈 전체 허용 (파일/네트워크 접근 없음)
        "statistics": statistics, # statistics 모듈 허용
        "StrategySignal": StrategySignal,  # 신호 반환을 위한 클래스
    }
    safe_locals: Dict[str, Any] = {}
    exec(compile(code, "<strategy>", "exec"), safe_globals, safe_locals)
    return {**safe_globals, **safe_locals}


def _normalize_signals(items: Iterable[Any]) -> List[Dict[str, Any]]:
    # 전략 함수가 반환한 신호를 표준 딕셔너리 형식으로 정규화한다.
    # 입력으로 허용되는 형식:
    #   1. StrategySignal 객체
    #   2. {"date": ..., "target_weights": ...} 딕셔너리
    #   3. (date, target_weights) 튜플 또는 리스트
    # 지원하지 않는 형식이 들어오면 StrategySandboxError를 발생시킨다.
    results: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, StrategySignal):
            results.append({"date": item.date, "target_weights": item.target_weights})
            continue
        if isinstance(item, dict) and "date" in item and "target_weights" in item:
            results.append({"date": str(item["date"]), "target_weights": item["target_weights"]})
            continue
        if isinstance(item, (list, tuple)) and len(item) == 2:
            results.append({"date": str(item[0]), "target_weights": item[1]})
            continue
        raise StrategySandboxError("Signals must be StrategySignal or {date, target_weights}")
    return results


def _child_worker(conn, payload: Dict[str, Any]) -> None:
    # 별도 프로세스에서 실행되는 전략 실행 함수.
    # 코드 검증 → 실행 → 신호 수집 → 결과를 Pipe로 부모 프로세스에 전송한다.
    # 오류 발생 시에도 결과를 Pipe로 전송하여 부모가 오류를 감지할 수 있게 한다.
    # 모든 예외를 잡아 {"ok": False, "error": ...} 형태로 전송한다.
    try:
        code = payload["code"]
        entrypoint = payload["entrypoint"]
        prices = payload["prices"]
        ctx = payload["ctx"]
        universe = payload["universe"]
        dates = payload["dates"]
        mode = payload["mode"]

        validate_python_strategy(code, entrypoint)
        scope = _safe_exec(code)
        fn = scope.get(entrypoint)
        if not callable(fn):
            raise StrategySandboxError("Entrypoint is not callable")

        if mode == "signals":
            # generate_signals 방식: 함수가 전체 기간 신호를 한 번에 반환
            output = fn(prices, ctx, universe)
            signals = _normalize_signals(output or [])
        else:
            # compute_target_weights 방식: 리밸런싱 날짜마다 함수를 호출
            signals = []
            for dt in dates:
                weights = fn(prices, ctx, universe, dt)
                if weights is None:
                    continue
                signals.append({"date": str(dt.date()), "target_weights": weights})

        conn.send({"ok": True, "signals": signals})
    except Exception as exc:  # noqa: BLE001
        conn.send({"ok": False, "error": str(exc), "trace": traceback.format_exc()})
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_python_strategy_for_dates(
    *,
    code: str,
    entrypoint: str,
    prices: pd.DataFrame,
    ctx: StrategyContext,
    universe: List[str],
    rebalance_dates: List[pd.Timestamp],
    timeout_s: float | None = None,
) -> List[Dict[str, Any]]:
    # 사용자 Python 전략을 격리된 자식 프로세스에서 실행하고 신호 목록을 반환한다.
    #
    # 격리 방법:
    #   - multiprocessing.Process로 별도 프로세스를 생성 ("spawn" 방식 — fork 없이 깨끗한 시작)
    #   - 부모↔자식 통신은 multiprocessing.Pipe를 사용
    #   - timeout_s 이내에 완료하지 않으면 프로세스를 강제 종료(terminate)
    #
    # "spawn" 컨텍스트를 사용하는 이유:
    #   - "fork"는 부모 프로세스의 파일 디스크립터, 락 등을 복사하여 위험할 수 있다
    #   - "spawn"은 완전히 새로운 Python 인터프리터를 시작하여 더 안전하다
    import multiprocessing as mp

    # entrypoint 이름으로 실행 모드를 결정한다
    mode = "signals" if entrypoint == "generate_signals" else "weights"
    timeout_s = timeout_s or DEFAULT_TIMEOUT_SEC

    parent_conn, child_conn = mp.Pipe(duplex=False)  # 단방향 파이프: 자식 → 부모
    payload = {
        "code": code,
        "entrypoint": entrypoint,
        "prices": prices,
        "ctx": ctx,
        "universe": universe,
        "dates": rebalance_dates,
        "mode": mode,
    }
    proc = mp.get_context("spawn").Process(target=_child_worker, args=(child_conn, payload))
    proc.start()
    proc.join(timeout_s)   # timeout_s초 동안 자식 프로세스 완료를 대기

    if proc.is_alive():
        # 타임아웃 초과: 자식 프로세스를 강제 종료
        proc.terminate()
        proc.join(1)
        raise StrategySandboxError("Python strategy execution timed out")

    if not parent_conn.poll():
        # 자식 프로세스가 결과를 Pipe에 보내지 않고 종료됨 (크래시 등)
        raise StrategySandboxError("Python strategy execution failed")

    result = parent_conn.recv()
    if not result.get("ok"):
        raise StrategySandboxError(result.get("error") or "Python strategy error")

    return result.get("signals") or []
