import os
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, send_file


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, "data_updater.py")
VOLATILITY_CSV_PATH = os.path.join(BASE_DIR, "data", "volatility_markets.csv")
ALL_MARKETS_CSV_PATH = os.path.join(BASE_DIR, "data", "all_markets.csv")
FULL_MARKETS_CSV_PATH = os.path.join(BASE_DIR, "data", "full_markets.csv")

# Allow overrides through env vars while keeping sensible defaults.
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", 15 * 60))
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", 8000))


class Scheduler:
    """Simple background scheduler that re-runs data_updater every REFRESH_SECONDS."""

    def __init__(self, interval_seconds: int):
        self.interval_seconds = max(60, interval_seconds)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

        self.last_run_started: datetime | None = None
        self.last_run_succeeded: datetime | None = None
        self.last_error: str | None = None

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=5)

    def _run_loop(self):
        while not self._stop_event.is_set():
            self.last_run_started = datetime.now(timezone.utc)
            try:
                subprocess.run(
                    ["python", SCRIPT_PATH],
                    cwd=BASE_DIR,
                    check=True,
                    capture_output=False,
                )
                self.last_run_succeeded = datetime.now(timezone.utc)
                self.last_error = None
            except subprocess.CalledProcessError as exc:
                self.last_error = f"Exit code {exc.returncode}"
            except Exception as exc:  # pragma: no cover
                self.last_error = str(exc)

            # Wait for the next run or exit sooner if signaled.
            self._stop_event.wait(self.interval_seconds)


scheduler = Scheduler(REFRESH_SECONDS)
# Start the scheduler as soon as the module is imported so it also runs
scheduler.start()
app = Flask(__name__)


@app.route("/volatility")
def serve_volatility_csv():
    if not os.path.exists(VOLATILITY_CSV_PATH):
        return (
            jsonify(
                {
                    "error": "volatility_markets.csv not found yet",
                    "csv_path": VOLATILITY_CSV_PATH,
                    "last_success": format_dt(scheduler.last_run_succeeded),
                }
            ),
            404,
        )

    return send_file(
        VOLATILITY_CSV_PATH,
        mimetype="text/csv",
        as_attachment=False,
        download_name="volatility_markets.csv",
    )


@app.route("/all_markets")
def serve_all_markets_csv():
    if not os.path.exists(ALL_MARKETS_CSV_PATH):
        return (
            jsonify(
                {
                    "error": "all_markets.csv not found yet",
                    "csv_path": ALL_MARKETS_CSV_PATH,
                    "last_success": format_dt(scheduler.last_run_succeeded),
                }
            ),
            404,
        )

    return send_file(
        ALL_MARKETS_CSV_PATH,
        mimetype="text/csv",
        as_attachment=False,
        download_name="all_markets.csv",
    )


@app.route("/full_markets")
def serve_full_markets_csv():
    if not os.path.exists(FULL_MARKETS_CSV_PATH):
        return (
            jsonify(
                {
                    "error": "full_markets.csv not found yet",
                    "csv_path": FULL_MARKETS_CSV_PATH,
                    "last_success": format_dt(scheduler.last_run_succeeded),
                }
            ),
            404,
        )

    return send_file(
        FULL_MARKETS_CSV_PATH,
        mimetype="text/csv",
        as_attachment=False,
        download_name="full_markets.csv",
    )


@app.route("/status")
def status():
    return jsonify(
        {
            "script_path": SCRIPT_PATH,
            "volatility_csv_path": VOLATILITY_CSV_PATH,
            "all_markets_csv_path": ALL_MARKETS_CSV_PATH,
            "full_markets_csv_path": FULL_MARKETS_CSV_PATH,
            "refresh_seconds": scheduler.interval_seconds,
            "last_run_started": format_dt(scheduler.last_run_started),
            "last_run_succeeded": format_dt(scheduler.last_run_succeeded),
            "last_error": scheduler.last_error,
        }
    )


def format_dt(dt: datetime | None):
    return dt.isoformat() if dt else None


def _graceful_shutdown(*_):
    scheduler.stop()
    # Flask's reloader spawns extra processes; only exit in the main process.
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)
    scheduler.start()
    app.run(host=HOST, port=PORT)

