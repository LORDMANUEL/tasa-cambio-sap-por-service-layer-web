"""Background scheduler lifecycle isolated from the FastAPI route module."""
from __future__ import annotations

import threading

from app.sync_engine import run_due_schedules


class SchedulerService:
    def __init__(self, settings, store, config_getter, summary_sender, logger, interval_seconds: int=30):
        self.settings=settings
        self.store=store
        self.config_getter=config_getter
        self.summary_sender=summary_sender
        self.log=logger
        self.interval_seconds=max(1,int(interval_seconds))
        self._stop=threading.Event()
        self._thread=None

    def run_once(self):
        results=run_due_schedules(self.settings,self.store)
        if results:
            self.log.info("V5 scheduler executed companies=%s",len(results))
            self.summary_sender(self.store,results)
        cfg=self.config_getter()
        self.store.cleanup(int(cfg.get("log_retention_days","30")))
        return results

    def _loop(self):
        while not self._stop.wait(self.interval_seconds):
            try:
                self.run_once()
            except Exception:
                self.log.exception("V5 scheduler failed")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread=threading.Thread(
            target=self._loop,
            name="sap-fx-v5-scheduler",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float=2.0):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
