"""PyInstaller entry point.

A standalone top-level script (not cleaner_app/__main__.py) is used here
because a frozen PyInstaller build treats its entry point as a plain script,
not as a package module — a relative import (`from .cli import main`) would
fail in that context, so this imports the package absolutely instead.
"""
from cleaner_app.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
