"""Import this FIRST in every KiCad-Python script (before `import pcbnew`).

KiCad 9's Windows build turns wxWidgets debug asserts into a modal
"wxWidgets Debug Alert" pop-up. Some harmless asserts fire inside KiCad itself,
e.g. SHAPE_POLY_SET::AddOutline "non-closed outline" while ExportSpecctraDSN
converts rule areas into keepouts. The export still succeeds.
wx.DisableAsserts() removes the assert handler for the whole process (the wx
DLLs are shared with _pcbnew), so no dialog can appear and nothing waits on a click.
"""
import sys

try:
    import wx
    wx.DisableAsserts()
except Exception as exc:  # never let the guard itself break a script
    sys.stderr.write(f"kicad_quiet: could not disable wx asserts ({exc})\n")

import pcbnew  # noqa: E402,F401  (re-exported for convenience: `from kicad_quiet import pcbnew`)
