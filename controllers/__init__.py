"""
Controllers package - Application layer orchestration.

Sits between the UI (`ui_pyside6/`) and the domain layer (`domain/`, `file_io/`).
Controllers own no widgets and know nothing about layouts or styling, but they
do use Qt's signal/slot mechanism so results and progress can be reported back
to whatever UI is listening without it having to reach into domain internals
or block its own thread while doing so.

Modules:
- `snapshot_loader.SnapshotLoader` — a `QThread` that drives `Snapshot`'s
  phase-by-phase parsing pipeline (header detection, PID extraction, unit
  conversion, etc.) off the UI thread, emitting `progress`, `finished_loading`,
  `partial_loading`, and `error` signals as each phase completes. Re-exported
  here because multiple call sites construct it directly.
- `app_controller.AppController` — a `QObject` that owns a `SnapshotLoader`,
  connects to its signals, tracks the currently-loaded `Snapshot`, and re-emits
  simplified signals (`snapshot_loaded`, `error_occurred`, ...) for
  `MainWindow` to consume. Imported directly via `controllers.app_controller`
  since it's the one caller that needs it.
- `ui_loader.UILoader` — a `QThread` meant to defer heavy PySide6/domain
  imports until after a splash screen is shown. Not currently wired up
  anywhere (`main.py` builds its splash screen inline instead); kept for
  reference rather than deleted outright.

Only `SnapshotLoader` is part of this package's public surface (`__all__`);
the other modules are imported by their own module path where needed.
"""

from controllers.snapshot_loader import SnapshotLoader

__all__ = ["SnapshotLoader"]
