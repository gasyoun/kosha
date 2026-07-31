"""Repo-root pytest configuration.

Puts the checkout's `src/` on `sys.path` so tests can `import kosha` without a
prior `pip install -e .`, mirroring what `app/__init__.py` does for the running
service. Also registers the `fixture` marker's meaning in one place: a test
marked `fixture` must pass against the committed fixture pack alone, with no
local 1.7 GB `data/db/kosha.db` present — that subset is what CI runs.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if (_SRC / "kosha" / "__init__.py").is_file() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
