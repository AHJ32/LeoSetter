# Legacy Prototype (pygeosetter/)

The code under this directory represents an earlier, experimental prototype with a large
surface area (map widget, batch dialogs, clipboard, complex window state, etc.).

It is kept for reference only and is not the supported app. For a stable, minimal
Linux clone of GeoSetter, use the MVP in `mvp/` and the entrypoint `run_mvp.py`.

## Why legacy?
- The main window (`pygeosetter/app.py`) mixes many responsibilities and contains
  structural issues (duplicate UI setup, references to undefined attributes like
  `self.tab_widget`).
- Heavy dependencies (QtWebEngine/Folium) add complexity you requested to avoid.
- The MVP focuses only on the fields and workflows you need now.

## Recommended path
- Use `run_mvp.py` to run the supported app.
- When migrating a feature from here to the MVP, port it in small, well-tested
  steps with clear boundaries.

## Deletion
We intentionally do not delete this directory so you can still inspect or copy
parts over if needed. When you are comfortable, we can remove this folder in a
separate cleanup commit.
