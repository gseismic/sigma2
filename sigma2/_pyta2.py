from __future__ import annotations

import importlib
import sys
from pathlib import Path


def ensure_pyta2_importable() -> None:
    """确保安装包布局和本地软链接布局都能导入 pyta2。"""

    if _can_import_pyta2():
        return

    _clear_pyta2_modules()
    package_root = Path(__file__).resolve().parent.parent
    candidates = (
        package_root / "pyta2",
        package_root.parent / "pyta2",
    )
    for candidate in candidates:
        if _looks_like_pyta2_repo(candidate):
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            importlib.invalidate_caches()
            _clear_pyta2_modules()
            if _can_import_pyta2():
                return

    raise ModuleNotFoundError(
        "sigma2 requires pyta2. Install pyta2 or expose the local pyta2 repo "
        "on PYTHONPATH."
    )


def _can_import_pyta2() -> bool:
    try:
        importlib.import_module("pyta2.base.schema")
        importlib.import_module("pyta2.utils.deque")
    except ModuleNotFoundError:
        return False
    return True


def _clear_pyta2_modules() -> None:
    for name in list(sys.modules):
        if name == "pyta2" or name.startswith("pyta2."):
            del sys.modules[name]


def _looks_like_pyta2_repo(path: Path) -> bool:
    return (path / "pyta2" / "base" / "schema.py").is_file()
