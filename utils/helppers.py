import os
import sys
from pathlib import Path

def resource_path(relative_path):
    """Return an absolute path to a bundled resource or a source-tree resource."""
    bundle_path = getattr(sys, "_MEIPASS", None)
    base_path = Path(bundle_path) if bundle_path else Path(__file__).resolve().parent.parent
    return str(base_path / relative_path)


def user_data_path(relative_path):
    """Return a path in the current user's application data directory."""
    if sys.platform == "darwin":
        base_path = Path.home() / "Library" / "Application Support" / "OurMoney"
    elif os.name == "nt":
        base_path = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "OurMoney"
    else:
        base_path = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "ourmoney"

    return str(base_path / relative_path)
