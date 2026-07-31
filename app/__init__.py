"""kosha FastAPI service package (compatibility entry point).

`app/` deliberately stays where it is — `uvicorn app.main:app` is the
documented way to run the service and every runbook and test says so. The
installable package lives in `src/kosha/` (W0B / H1944); this shim is what lets
the two coexist in a checkout that has not been `pip install`-ed.

Importing this package puts the checkout's `src/` on `sys.path`, so
`from kosha.settings import get_settings` resolves. When kosha IS installed the
insert is redundant and harmless — the import would have resolved anyway.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if (_SRC / "kosha" / "__init__.py").is_file() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
