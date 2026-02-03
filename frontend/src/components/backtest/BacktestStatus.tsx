import type { BacktestJob } from "@/types/backtest";

type Props = {
  error?: string | null;
  job?: BacktestJob | null;
  tr: (en: string, ko: string) => string;
};

export default function BacktestStatus({ error, job, tr }: Props) {
  const isRunning = job?.status === "queued" || job?.status === "running";
  const progressLabel =
    job?.progress !== undefined && job?.progress !== null
      ? `${job.progress}%`
      : "";
  const remainingLabel =
    job?.progress !== undefined && job?.progress !== null
      ? `${Math.max(0, 100 - job.progress)}% left`
      : "";
  const progressMessage = job?.progress_message || job?.progress_stage || "";
  const recentLogs = job?.progress_log?.slice(-4) ?? [];
  const jobError = job?.error;

  if (!error && !job) return null;

  return (
    <>
      {error && (
        <div className="text-sm text-red-400">{error}</div>
      )}
      {isRunning && (
        <div className="text-sm text-gray-400 space-y-1">
          <div>
            {tr("Backtest", "백테스트")} {job?.status}
            {progressLabel && ` ? ${progressLabel}`}
            {remainingLabel && ` ? ${tr(remainingLabel, "??")}`}
          </div>
          {progressMessage && (
            <div className="text-xs text-gray-500">{progressMessage}</div>
          )}
          {recentLogs.length ? (
            <div className="text-xs text-gray-500 space-y-0.5">
              {recentLogs.map((entry) => {
                const timeLabel = new Date(entry.at).toLocaleTimeString("ko-KR", {
                  hour: "2-digit",
                  minute: "2-digit"
                });
                return (
                  <div key={`${entry.at}-${entry.stage}-${entry.message}`}>
                    {timeLabel} ? {entry.message}
                    {entry.progress !== undefined ? ` (${entry.progress}%)` : ""}
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>
      )}
      {job?.status === "failed" && (
        <div className="text-sm text-red-400 space-y-1">
          <div>
            {tr("Backtest failed", "백테스트에 실패하였습니다.")}{jobError?.message ? `: ${jobError.message}` : "."}
          </div>
          {jobError?.detail && (
            <div className="text-xs text-red-300">{jobError.detail}</div>
          )}
          {jobError?.details?.length ? (
            <div className="text-xs text-red-300">
              {jobError.details.map((d) => `${d.field}: ${d.reason}`).join(" ? ")}
            </div>
          ) : null}
        </div>
      )}
      {job?.status === "canceled" && (
        <div className="text-sm text-gray-400">
          {tr("Backtest canceled.", "백테스트가 취소되었습니다.")}
        </div>
      )}
    </>
  );
}
