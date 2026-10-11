"""Supplemental isolated verification of the MCP-generated, saved native CAD.

Run: freecad.cmd /absolute/repo/src/check_spine_headless.py
No GUI document writes. The live application must already have saved neutral.
"""
import sys
from pathlib import Path
import FreeCAD as App
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
import verify_flexor
doc=App.openDocument(str(root/'cad/flexor_r02_spine.FCStd'))
doc.recompute()
verify_flexor.native_checks(doc)
data,placements,motion=verify_flexor.sweep_snapshot(doc)
verify_flexor.sweep(data,placements,motion,1)
App.closeDocument(doc.Name)
