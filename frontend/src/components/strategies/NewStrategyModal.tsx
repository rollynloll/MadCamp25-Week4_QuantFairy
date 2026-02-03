import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

interface NewStrategyModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (body: { 
    name: string;
    params: Record<string, any>;
    note?: string;
    python?: {
      entrypoint: string;
      code: string;
    };
  }) => void;
  loading?: boolean;
  error?: string | null;
}

export default function NewStrategyModal({
  open,
  onClose,
  onSubmit,
  loading = false,
  error = null
}: NewStrategyModalProps) {
  const [name, setName] = useState("");
  const [paramsText, setParamsText] = useState("{\n \n}");
  const [note, setNote] = useState("");
  const [entrypoint, setEntrypoint] = useState("compute_target_weights");
  const [code, setCode] = useState(
    "def compute_target_weights(prices, ctx, universe, dt):\n"
      + "    # prices: MultiIndex DataFrame (date, symbol)\n"
      + "    # ctx.params: your params dict\n"
      + "    # universe: list of symbols\n"
      + "    # dt: pandas Timestamp\n"
      + "    return {}\n"
  );
  const { tr } = useLanguage();
  const templates = [
    {
      id: "momentum",
      label: tr("Momentum Top-K", "모멘텀 Top-K"),
      description: tr("Buy top performers by lookback return.", "최근 수익률 상위 종목을 매수합니다."),
      params: { lookback_days: 126, top_k: 10 },
      code:
        "def compute_target_weights(prices, ctx, universe, dt):\n"
          + "    lookback = int(ctx.params.get(\"lookback_days\", 126))\n"
          + "    top_k = int(ctx.params.get(\"top_k\", 10))\n"
          + "    matrix = prices.reset_index().pivot(index=\"date\", columns=\"symbol\", values=\"adj_close\")\n"
          + "    window = matrix.tail(lookback + 1)\n"
          + "    if len(window) < lookback + 1:\n"
          + "        return {}\n"
          + "    returns = (window.iloc[-1] / window.iloc[0] - 1).dropna()\n"
          + "    top = returns.sort_values(ascending=False).head(top_k).index.tolist()\n"
          + "    if not top:\n"
          + "        return {}\n"
          + "    w = 1.0 / len(top)\n"
          + "    return {sym: w for sym in top}\n",
    },
    {
      id: "rsi",
      label: tr("RSI Mean Reversion", "RSI 평균회귀"),
      description: tr("Buy when RSI is low, exit when RSI is high.", "RSI가 낮으면 매수, 높으면 청산합니다."),
      params: { symbol: "SPY", rsi_window: 14, entry_rsi: 30, exit_rsi: 50 },
      code:
        "def compute_target_weights(prices, ctx, universe, dt):\n"
          + "    symbol = str(ctx.params.get(\"symbol\", \"SPY\")).upper()\n"
          + "    window = int(ctx.params.get(\"rsi_window\", 14))\n"
          + "    entry = float(ctx.params.get(\"entry_rsi\", 30))\n"
          + "    exit = float(ctx.params.get(\"exit_rsi\", 50))\n"
          + "    series = prices.xs(symbol, level=1)[\"adj_close\"].dropna()\n"
          + "    if len(series) < window + 1:\n"
          + "        return {}\n"
          + "    delta = series.diff()\n"
          + "    gain = delta.clip(lower=0).rolling(window).mean()\n"
          + "    loss = (-delta.clip(upper=0)).rolling(window).mean()\n"
          + "    rs = gain / loss.replace(0, pd.NA)\n"
          + "    rsi = 100 - (100 / (1 + rs))\n"
          + "    if pd.isna(rsi.iloc[-1]):\n"
          + "        return {}\n"
          + "    if rsi.iloc[-1] < entry:\n"
          + "        return {symbol: 1.0}\n"
          + "    if rsi.iloc[-1] > exit:\n"
          + "        return {}\n"
          + "    return {}\n",
    },
    {
      id: "trend",
      label: tr("Trend SMA200", "추세 SMA200"),
      description: tr("Risk-on if price above SMA.", "가격이 SMA 위면 위험자산, 아니면 현금."),
      params: { benchmark_symbol: "SPY", sma_window: 200 },
      code:
        "def compute_target_weights(prices, ctx, universe, dt):\n"
          + "    symbol = str(ctx.params.get(\"benchmark_symbol\", \"SPY\")).upper()\n"
          + "    window = int(ctx.params.get(\"sma_window\", 200))\n"
          + "    series = prices.xs(symbol, level=1)[\"adj_close\"].dropna()\n"
          + "    sma = series.rolling(window).mean()\n"
          + "    if len(sma) == 0 or pd.isna(sma.iloc[-1]):\n"
          + "        return {}\n"
          + "    return {symbol: 1.0} if series.iloc[-1] > sma.iloc[-1] else {}\n",
    },
    {
      id: "low_vol",
      label: tr("Low Volatility", "저변동성"),
      description: tr("Select low-vol assets, inverse-vol weights.", "저변동성 종목을 선택합니다."),
      params: { lookback_days: 60, top_k: 10, weighting: "inverse_vol" },
      code:
        "def compute_target_weights(prices, ctx, universe, dt):\n"
          + "    lookback = int(ctx.params.get(\"lookback_days\", 60))\n"
          + "    top_k = int(ctx.params.get(\"top_k\", 10))\n"
          + "    weighting = str(ctx.params.get(\"weighting\", \"inverse_vol\"))\n"
          + "    matrix = prices.reset_index().pivot(index=\"date\", columns=\"symbol\", values=\"adj_close\")\n"
          + "    window = matrix.tail(lookback + 1)\n"
          + "    if len(window) < lookback + 1:\n"
          + "        return {}\n"
          + "    vol = window.pct_change().std().dropna()\n"
          + "    selected = vol.sort_values().head(top_k)\n"
          + "    if selected.empty:\n"
          + "        return {}\n"
          + "    if weighting == \"inverse_vol\":\n"
          + "        inv = 1 / selected\n"
          + "        total = float(inv.sum())\n"
          + "        return {sym: float(inv[sym] / total) for sym in selected.index}\n"
          + "    w = 1.0 / len(selected)\n"
          + "    return {sym: w for sym in selected.index}\n",
    },
    {
      id: "vol_adj_mom",
      label: tr("Vol-Adjusted Momentum", "변동성 조정 모멘텀"),
      description: tr("Rank returns divided by vol.", "수익률/변동성으로 랭킹합니다."),
      params: { lookback_days: 126, vol_window: 60, top_k: 10 },
      code:
        "def compute_target_weights(prices, ctx, universe, dt):\n"
          + "    lookback = int(ctx.params.get(\"lookback_days\", 126))\n"
          + "    vol_window = int(ctx.params.get(\"vol_window\", 60))\n"
          + "    top_k = int(ctx.params.get(\"top_k\", 10))\n"
          + "    matrix = prices.reset_index().pivot(index=\"date\", columns=\"symbol\", values=\"adj_close\")\n"
          + "    window = matrix.tail(lookback + 1)\n"
          + "    if len(window) < lookback + 1:\n"
          + "        return {}\n"
          + "    returns = (window.iloc[-1] / window.iloc[0] - 1).dropna()\n"
          + "    vol = matrix.pct_change().tail(vol_window).std().dropna()\n"
          + "    score = (returns / vol).replace([pd.NA], 0).dropna()\n"
          + "    top = score.sort_values(ascending=False).head(top_k).index.tolist()\n"
          + "    if not top:\n"
          + "        return {}\n"
          + "    w = 1.0 / len(top)\n"
          + "    return {sym: w for sym in top}\n",
    },
    {
      id: "risk_on_off",
      label: tr("Risk-On / Risk-Off", "리스크 온/오프"),
      description: tr("Use SMA regime to switch risk-on/off.", "SMA 기준으로 위험자산/현금 전환."),
      params: { benchmark_symbol: "SPY", sma_window: 200, lookback_days: 126, top_k: 10 },
      code:
        "def compute_target_weights(prices, ctx, universe, dt):\n"
          + "    bench = str(ctx.params.get(\"benchmark_symbol\", \"SPY\")).upper()\n"
          + "    sma_window = int(ctx.params.get(\"sma_window\", 200))\n"
          + "    lookback = int(ctx.params.get(\"lookback_days\", 126))\n"
          + "    top_k = int(ctx.params.get(\"top_k\", 10))\n"
          + "    bench_series = prices.xs(bench, level=1)[\"adj_close\"].dropna()\n"
          + "    sma = bench_series.rolling(sma_window).mean()\n"
          + "    if len(sma) == 0 or pd.isna(sma.iloc[-1]):\n"
          + "        return {}\n"
          + "    risk_on = bench_series.iloc[-1] > sma.iloc[-1]\n"
          + "    if not risk_on:\n"
          + "        return {}\n"
          + "    matrix = prices.reset_index().pivot(index=\"date\", columns=\"symbol\", values=\"adj_close\")\n"
          + "    window = matrix.tail(lookback + 1)\n"
          + "    if len(window) < lookback + 1:\n"
          + "        return {}\n"
          + "    returns = (window.iloc[-1] / window.iloc[0] - 1).dropna()\n"
          + "    top = returns.sort_values(ascending=False).head(top_k).index.tolist()\n"
          + "    if not top:\n"
          + "        return {}\n"
          + "    w = 1.0 / len(top)\n"
          + "    return {sym: w for sym in top}\n",
    },
  ];
  const [templateId, setTemplateId] = useState(templates[0].id);
  const selectedTemplate = templates.find((t) => t.id === templateId) ?? templates[0];

  const applyTemplate = () => {
    setEntrypoint("compute_target_weights");
    setCode(selectedTemplate.code);
    setParamsText(JSON.stringify(selectedTemplate.params, null, 2));
    if (!name.trim()) {
      setName(selectedTemplate.label);
    }
  };

  if (!open) return null;

  const handleSubmit = () => {
    let params: Record<string, any> = {};
    try {
      params = paramsText.trim() ? JSON.parse(paramsText) : {};
    } catch {
      alert(tr("Params must be valid JSON.", "파라미터는 올바른 JSON이어야 합니다."));
      return;
    }
    if (!name.trim()) {
      alert(tr("Name is required.", "이름을 입력해주세요."));
      return;
    }
    if (!code.trim()) {
      alert(tr("Python code is required.", "Python 코드를 입력해주세요."));
      return;
    }
    onSubmit({
      name: name.trim(),
      params,
      note: note.trim() || undefined,
      python: {
        entrypoint: entrypoint.trim() || "compute_target_weights",
        code
      }
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 p-6" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-xl border border-gray-800 bg-[#0d1117] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
          <h2 className="text-lg font-semibold">{tr("New Strategy", "새 전략")}</h2>
          <button className="text-sm text-gray-400 hover:text-gray-200" onClick={onClose}>
            {tr("Close", "닫기")}
          </button>
        </div>

        <div className="px-6 py-5 space-y-4 text-sm">
          {error && <div className="text-red-400">{error}</div>}

          <div className="rounded-lg border border-gray-800 bg-gray-900/20 p-3 text-xs text-gray-400 space-y-2">
            <div className="font-semibold text-gray-300">{tr("Quick Start", "빠른 시작")}</div>
            <div className="text-[11px] text-gray-500">
              {tr(
                "Pick a template, apply it, then tweak params and code.",
                "템플릿을 선택해 적용한 뒤 파라미터와 코드를 조정하세요."
              )}
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <select
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="bg-[#0a0d14] border border-gray-800 rounded px-2 py-1 text-xs text-gray-200"
              >
                {templates.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {tpl.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={applyTemplate}
                className="inline-flex items-center rounded border border-gray-700 px-2 py-1 text-[11px] text-gray-300 hover:text-white hover:border-gray-600"
              >
                {tr("Apply template", "템플릿 적용")}
              </button>
            </div>
            <div className="text-[11px] text-gray-500">{selectedTemplate.description}</div>
            <div>
              <span className="text-gray-500">{tr("Function", "함수")}:</span>{" "}
              <span className="font-mono text-gray-300">compute_target_weights(prices, ctx, universe, dt)</span>
            </div>
            <div className="grid gap-1 sm:grid-cols-2">
              <div>
                <span className="text-gray-500">prices</span>{" "}
                {tr("= price dataframe", "= 가격 데이터프레임")}
              </div>
              <div>
                <span className="text-gray-500">ctx.params</span>{" "}
                {tr("= params JSON", "= 파라미터 JSON")}
              </div>
              <div>
                <span className="text-gray-500">universe</span>{" "}
                {tr("= tickers list", "= 종목 리스트")}
              </div>
              <div>
                <span className="text-gray-500">dt</span>{" "}
                {tr("= rebalance date", "= 리밸런스 날짜")}
              </div>
            </div>
            <div>
              {tr("Return", "반환값")}:{" "}
              <span className="font-mono text-gray-300">{`{"AAPL": 0.5, "MSFT": 0.5}`}</span>
            </div>
            <div className="text-[11px] text-gray-500">
              {tr(
                "Sandboxed: no imports, no file/network access. Allowed: math, statistics, pd (safe subset).",
                "샌드박스 실행: import/파일/네트워크 불가. 허용: math, statistics, pd(안전 subset)."
              )}
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">{tr("Name", "이름")}</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2"
              placeholder={tr("My Custom Strategy", "내 커스텀 전략")}
            />
          </div>

          <>
            <div>
              <label className="text-xs text-gray-400 mb-2 block">{tr("Entrypoint", "엔트리포인트")}</label>
              <input
                value={entrypoint}
                onChange={(e) => setEntrypoint(e.target.value)}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 font-mono text-xs"
                placeholder="compute_target_weights"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-2 block">{tr("Python Code", "Python 코드")}</label>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full h-48 bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 font-mono text-xs"
              />
            </div>
          </>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">{tr("Params (JSON)", "파라미터 (JSON)")}</label>
            <textarea
              value={paramsText}
              onChange={(e) => setParamsText(e.target.value)}
              className="w-full h-40 bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 font-mono text-xs"
            />
            <div className="mt-2 text-[11px] text-gray-500">
              {tr("Access via ctx.params (e.g. ctx.params.get('lookback_days')).", "ctx.params로 접근 (예: ctx.params.get('lookback_days')).")}
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">{tr("Note (optional)", "메모 (선택)")}</label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2"
              placeholder={tr("Memo...", "메모...")}
            />
          </div>
        </div>

        <div className="flex gap-3 border-t border-gray-800 px-6 py-4">
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium"
            type="button"
          >
            {tr("Cancel", "취소")}
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium disabled:opacity-60"
            type="button"
            disabled={loading}
          >
            {loading ? tr("Saving...", "저장 중...") : tr("Save", "저장")}
          </button>
        </div>
      </div>
    </div>
  );
}
