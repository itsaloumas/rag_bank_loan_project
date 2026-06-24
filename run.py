"""
run.py
One-command launcher for the Bank Loan RAG Evaluation System.

Starts the FastAPI backend (port 8000) and the Streamlit UI (port 8501)
together, waits for the backend to finish loading, and shuts both processes
down on Ctrl+C.

from the project root, inside the project's Python environment:
    python run.py
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "src" / "bankingragdemo" / "api.py"
FRONTEND = ROOT / "src" / "bankingragdemo" / "app.py"
HEALTH_URL = "http://localhost:8000/api/health"


def wait_for_backend(proc, timeout=180):
    # Poll the health endpoint until the backend responds, the process exits, or the timeout elapses. Returns True only when the backend is reachable.
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main():
    processes = []
    try:
        print("Starting backend (FastAPI on http://localhost:8000) ...")
        backend = subprocess.Popen([sys.executable, str(BACKEND)], cwd=ROOT)
        processes.append(backend)

        print("Waiting for the backend to load models and connect to Groq "
              "(this can take a minute on the first run) ...")
        if wait_for_backend(backend):
            print("Backend is ready.")
        elif backend.poll() is not None:
            print("ERROR: the backend exited during startup. "
                  "Check that the .env file and dependencies are in place.")
            return
        else:
            print("WARNING: the backend did not report healthy in time "
                  "starting the UI anyway.")

        print("Starting frontend (Streamlit on http://localhost:8501) ...")
        frontend = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(FRONTEND)],
            cwd=ROOT,
        )
        processes.append(frontend)

        frontend.wait()
    except KeyboardInterrupt:
        print("\nShutting down ...")
    finally:
        for proc in processes:
            proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    main()
