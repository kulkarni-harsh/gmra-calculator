import logging

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class JobLogHandler(logging.Handler):
    """
    In-memory handler that captures every log record emitted during a job run.

    Attach to the root logger for the duration of a job, then read back
    the full log text and per-level counts:

        handler = JobLogHandler()
        logging.getLogger().addHandler(handler)
        try:
            ...  # job work
        finally:
            logging.getLogger().removeHandler(handler)
            text    = handler.get_text()   # full newline-joined log
            summary = handler.summary      # {"INFO": n, "WARNING": n, ...}
    """

    _TRACKED_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.setFormatter(logging.Formatter(_LOG_FORMAT))
        self._lines: list[str] = []
        self._counts: dict[str, int] = {lvl: 0 for lvl in self._TRACKED_LEVELS}

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._lines.append(self.format(record))
            key = record.levelname if record.levelname in self._counts else "DEBUG"
            self._counts[key] += 1
        except Exception:
            self.handleError(record)

    def get_text(self) -> str:
        """Return all captured log lines joined by newlines."""
        return "\n".join(self._lines)

    @property
    def summary(self) -> dict[str, int]:
        """Return a copy of per-level counts."""
        return dict(self._counts)
