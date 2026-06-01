"""Host installation recipes.

Each host has an install recipe that knows:
- Where to put the hook script
- What hooks.json should look like
- Whether a .cmd wrapper is needed (Windows)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_lantern.transports.windows_cmd import (
    generate_cmd_wrapper,
    is_windows,
    resolve_python_path,
)


# --- Install recipes per host ---

INSTALL_RECIPES: dict[str, dict] = {
    "codex": {
        "display_name": "OpenAI Codex",
        "unix": {
            "hook_dir": Path.home() / ".codex" / "hooks",
            "hooks_json": Path.home() / ".codex" / "hooks.json",
            "command_template": "{python_path} -m context_lantern run --adapter codex --threshold {threshold}",
            "event": "Stop",
            "timeout": 5,
        },
        "windows": {
            "hook_dir": Path.home() / ".codex" / "hooks",
            "hooks_json": Path.home() / ".codex" / "hooks.json",
            "cmd_wrapper": True,
            "event": "Stop",
            "timeout": 10,
        },
    },
    "cursor": {
        "display_name": "Cursor",
        "unix": {
            "hook_dir": Path.home() / ".cursor" / "hooks",
            "hooks_json": Path.home() / ".cursor" / "hooks.json",
            "command_template": "{python_path} -m context_lantern run --adapter cursor --threshold {threshold}",
            "event": "stop",
            "timeout": 5,
        },
        "windows": {
            "hook_dir": Path.home() / ".cursor" / "hooks",
            "hooks_json": Path.home() / ".cursor" / "hooks.json",
            "cmd_wrapper": True,
            "event": "stop",
            "timeout": 10,
        },
    },
    # windsurf and copilot recipes to be added when researched
}


def run_install(args: argparse.Namespace) -> int:
    """Generate and optionally execute install steps for a host."""
    adapter_name = args.adapter
    dry_run = args.dry_run

    recipe = INSTALL_RECIPES.get(adapter_name)
    if recipe is None:
        print(
            f"No install recipe for '{adapter_name}'. "
            f"Available: {', '.join(INSTALL_RECIPES.keys())}",
            file=sys.stderr,
        )
        return 1

    platform_key = "windows" if is_windows() else "unix"
    platform_recipe = recipe.get(platform_key)

    if platform_recipe is None:
        print(f"No {platform_key} recipe for '{adapter_name}'.", file=sys.stderr)
        return 1

    hook_dir = platform_recipe["hook_dir"]
    hooks_json = platform_recipe["hooks_json"]
    threshold = getattr(args, "threshold", 120_000)
    python_path = resolve_python_path()

    print(f"Install recipe for {recipe['display_name']} ({platform_key})")
    print(f"  Hook dir:  {hook_dir}")
    print(f"  Config:    {hooks_json}")
    print()

    # Step 1: Create hook directory
    print(f"  mkdir -p {hook_dir}")
    if not dry_run:
        hook_dir.mkdir(parents=True, exist_ok=True)

    # Step 2: Generate command
    if platform_recipe.get("cmd_wrapper"):
        # Windows: generate .cmd wrapper
        cmd_content = generate_cmd_wrapper(
            adapter=adapter_name,
            python_path=python_path,
            extra_args=f"--threshold {threshold}",
        )
        cmd_path = hook_dir / f"context_lantern_{adapter_name}.cmd"
        print(f"  Write .cmd wrapper -> {cmd_path}")
        if not dry_run:
            cmd_path.write_text(cmd_content, encoding="utf-8")
        command = str(cmd_path)
    else:
        # Unix: direct command
        command = platform_recipe["command_template"].format(
            python_path=python_path,
            threshold=threshold,
        )
        print(f"  Command: {command}")

    # Step 3: Generate hooks.json
    hooks_config = {
        "hooks": {
            platform_recipe["event"]: [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "timeout": platform_recipe["timeout"],
                        }
                    ]
                }
            ]
        }
    }

    print(f"\n  hooks.json content:")
    print(f"  {json.dumps(hooks_config, indent=2)}")

    if not dry_run:
        hooks_json.parent.mkdir(parents=True, exist_ok=True)
        hooks_json.write_text(
            json.dumps(hooks_config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n  Written -> {hooks_json}")
    else:
        print(f"\n  [dry-run] Would write -> {hooks_json}")

    print("\nDone." if not dry_run else "\n[dry-run] No files were modified.")
    return 0
