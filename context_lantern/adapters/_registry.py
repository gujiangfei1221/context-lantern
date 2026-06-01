"""Adapter registry — separate module to avoid circular imports.

Adapters import register_adapter from here.
The __init__.py re-exports and triggers auto-import.
"""

from __future__ import annotations

import sys
from typing import Any


# --- Registry ---

_ADAPTERS: dict[str, type[Any]] = {}


def register_adapter(cls: type[Any]) -> type[Any]:
    """Decorator to register an adapter class."""
    instance = cls()
    _ADAPTERS[instance.host_name] = cls
    return cls


def get_adapter(name: str) -> Any:
    """Get an adapter instance by host name.

    Raises KeyError if the adapter is not registered.
    """
    _ensure_loaded()
    if name not in _ADAPTERS:
        available = ", ".join(sorted(_ADAPTERS.keys())) or "(none)"
        raise KeyError(f"Unknown adapter '{name}'. Available: {available}")
    return _ADAPTERS[name]()


def list_adapters() -> list[str]:
    """List all registered adapter names."""
    _ensure_loaded()
    return sorted(_ADAPTERS.keys())


# --- Lazy auto-import ---

_loaded = False


def _ensure_loaded() -> None:
    """Import all adapter modules so their @register_adapter decorators run."""
    global _loaded
    if _loaded:
        return
    _loaded = True

    import importlib

    adapter_modules = [
        "context_lantern.adapters.codex_stop",
        "context_lantern.adapters.cursor_stop",
        "context_lantern.adapters.windsurf_stop",
        "context_lantern.adapters.copilot_stop",
    ]
    for mod_name in adapter_modules:
        try:
            importlib.import_module(mod_name)
        except ImportError:
            pass
