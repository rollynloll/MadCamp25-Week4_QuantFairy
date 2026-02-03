from __future__ import annotations

import ast
import hashlib
import math
import statistics
import traceback
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from app.strategies.base import StrategySignal, StrategyContext
from app.strategies.spec import PythonBody


PYTHON_ENTRYPOINT = "__python__"
PYTHON_META_KEY = "__python__"
MAX_CODE_SIZE = 200_000
DEFAULT_TIMEOUT_SEC = 12.0


class StrategySandboxError(Exception):
    pass


class SafePandas:
    Series = pd.Series
    DataFrame = pd.DataFrame
    Timestamp = pd.Timestamp
    NA = pd.NA
    to_datetime = staticmethod(pd.to_datetime)
    isna = staticmethod(pd.isna)
    notna = staticmethod(pd.notna)


SAFE_BUILTINS: Dict[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "sorted": sorted,
    "float": float,
    "int": int,
    "str": str,
    "bool": bool,
    "dict": dict,
    "list": list,
    "set": set,
    "tuple": tuple,
}

_BANNED_NAMES = {
    "__import__",
    "eval",
    "exec",
    "open",
    "compile",
    "input",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "help",
    "type",
    "object",
    "super",
    "memoryview",
    "classmethod",
    "staticmethod",
    "breakpoint",
}


_ALLOWED_NODES = (
    ast.Module,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Return,
    ast.Assign,
    ast.AnnAssign,
    ast.AugAssign,
    ast.Expr,
    ast.Pass,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.If,
    ast.For,
    ast.Break,
    ast.Continue,
    ast.Call,
    ast.Attribute,
    ast.Subscript,
    ast.Slice,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.comprehension,
    ast.IfExp,
)


class _StrategyAstValidator(ast.NodeVisitor):
    def generic_visit(self, node: ast.AST) -> None:
        if not isinstance(node, _ALLOWED_NODES):
            raise StrategySandboxError(f"Unsupported syntax: {type(node).__name__}")
        super().generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: D401
        raise StrategySandboxError("Import statements are not allowed")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: D401
        raise StrategySandboxError("Import statements are not allowed")

    def visit_While(self, node: ast.While) -> None:  # noqa: D401
        raise StrategySandboxError("While loops are not allowed")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_"):
            raise StrategySandboxError("Private attributes are not allowed")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _BANNED_NAMES:
            raise StrategySandboxError(f"Use of '{node.id}' is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id in _BANNED_NAMES:
            raise StrategySandboxError(f"Use of '{func.id}' is not allowed")
        if isinstance(func, ast.Attribute) and func.attr in _BANNED_NAMES:
            raise StrategySandboxError(f"Use of '{func.attr}' is not allowed")
        self.generic_visit(node)


def validate_python_strategy(code: str, entrypoint: str) -> None:
    if not code or not code.strip():
        raise StrategySandboxError("Python code is empty")
    if len(code) > MAX_CODE_SIZE:
        raise StrategySandboxError("Python code is too large")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise StrategySandboxError(f"Syntax error: {exc.msg}") from exc

    defined = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    if entrypoint not in defined:
        raise StrategySandboxError(f"Entrypoint '{entrypoint}' is not defined")

    validator = _StrategyAstValidator()
    validator.visit(tree)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:12]


def extract_python_body(params: Dict[str, Any]) -> Tuple[Dict[str, Any], PythonBody | None]:
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
    safe_globals: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "pd": SafePandas(),
        "math": math,
        "statistics": statistics,
        "StrategySignal": StrategySignal,
    }
    safe_locals: Dict[str, Any] = {}
    exec(compile(code, "<strategy>", "exec"), safe_globals, safe_locals)
    return {**safe_globals, **safe_locals}


def _normalize_signals(items: Iterable[Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, StrategySignal):
            results.append({"date": item.date, "target_weights": item.target_weights})
            continue
        if isinstance(item, dict) and "date" in item and "target_weights" in item:
            results.append(
                {"date": str(item["date"]), "target_weights": item["target_weights"]}
            )
            continue
        if isinstance(item, (list, tuple)) and len(item) == 2:
            results.append({"date": str(item[0]), "target_weights": item[1]})
            continue
        raise StrategySandboxError("Signals must be StrategySignal or {date, target_weights}")
    return results


def _child_worker(conn, payload: Dict[str, Any]) -> None:
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
            output = fn(prices, ctx, universe)
            signals = _normalize_signals(output or [])
        else:
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
    import multiprocessing as mp

    mode = "signals" if entrypoint == "generate_signals" else "weights"
    timeout_s = timeout_s or DEFAULT_TIMEOUT_SEC

    parent_conn, child_conn = mp.Pipe(duplex=False)
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
    proc.join(timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(1)
        raise StrategySandboxError("Python strategy execution timed out")
    if not parent_conn.poll():
        raise StrategySandboxError("Python strategy execution failed")
    result = parent_conn.recv()
    if not result.get("ok"):
        raise StrategySandboxError(result.get("error") or "Python strategy error")
    return result.get("signals") or []
