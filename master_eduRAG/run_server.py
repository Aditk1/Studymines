import os
import sys
import webbrowser
from pathlib import Path

import uvicorn


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main() -> None:
    root = _project_root()
    os.chdir(root)

    host = os.getenv("EDURAG_HOST", "127.0.0.1")
    port = int(os.getenv("EDURAG_PORT", "8000"))
    url = f"http://{host}:{port}/docs"

    if os.getenv("EDURAG_OPEN_BROWSER", "1").lower() not in {"0", "false", "no"}:
        webbrowser.open(url)

    uvicorn.run("app.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
