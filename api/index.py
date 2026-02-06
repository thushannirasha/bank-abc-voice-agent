from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_PATH = ROOT / "backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

os.environ.setdefault("PYTHONPATH", str(BACKEND_PATH))

from app.main import app  # noqa: E402

# Vercel expects a module-level `app` variable for ASGI.
