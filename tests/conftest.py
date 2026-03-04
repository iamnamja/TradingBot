import sys
from pathlib import Path

# Ensure <repo>/src is on sys.path when running tests from the repo root.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
