from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional


class BacktestStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._results: Dict[str, Dict[str, Any]] = {}

    def create_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._jobs[job["backtest_id"]] = job
        return job

    def update_job(self, backtest_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(backtest_id)
            if not job:
                return None
            job.update(updates)
            self._jobs[backtest_id] = job
            return job

    def get_job(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._jobs.get(backtest_id)

    def list_jobs(
        self, user_id: str, filters: Dict[str, Any], sort: str, order: str
    ) -> List[Dict[str, Any]]:
        with self._lock:
            items = [job for job in self._jobs.values() if job.get("user_id") == user_id]

        if filters.get("status"):
            items = [job for job in items if job.get("status") == filters["status"]]
        if filters.get("mode"):
            items = [job for job in items if job.get("mode") == filters["mode"]]

        reverse = order == "desc"
        items.sort(key=lambda j: j.get(sort, ""), reverse=reverse)
        return items

    def set_results(self, backtest_id: str, results: Dict[str, Any]) -> None:
        with self._lock:
            self._results[backtest_id] = results

    def get_results(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._results.get(backtest_id)

    def delete(self, backtest_id: str) -> None:
        with self._lock:
            self._jobs.pop(backtest_id, None)
            self._results.pop(backtest_id, None)


STORE = BacktestStore()
