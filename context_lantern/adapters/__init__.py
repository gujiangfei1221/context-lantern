"""Adapter package.

Re-exports registry functions and triggers adapter auto-import.
"""

from context_lantern.adapters._registry import (
    register_adapter,
    get_adapter,
    list_adapters,
)

__all__ = [
    "register_adapter",
    "get_adapter",
    "list_adapters",
]
