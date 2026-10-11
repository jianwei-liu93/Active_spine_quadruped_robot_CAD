"""Outer fixed A/slider journal stack recovered from Fig 1A and Movie S2.

The contoured plates are native features in refine_flexor. This module
extends their stationary journals and captures both inner and outer supports.
All numeric shaft/fit/axial dimensions remain engineering assumptions.
"""
import FreeCAD as App,json
import cad_common as cc
from kinematics import spine
from retain_flexor import grooves,clip_source

def apply(b):
    doc=b.doc
    if 'SliderPlateRecovery' in doc.PoseController.PropertiesList:return b
    p=b.p;s=spine(doc.PoseController.SpinePhaseRad,p)
    length=p['guide_fixed_journal_length_mm'];center=p['guide_fixed_journal_center_y_mm']
    shaft=b.ring('A_FIXED_JOURNAL_D1p9_L15p8_GROOVED',1.9,0,length)
    grooves(b,shaft,length);shaft.PartNumber='A_FIXED_JOURNAL_D1p9_L15p8_GROOVED'
    shaft.Process='turned grooved stationary journal; supports inner frame and outer A/slider plate; provisional fit'
    bearing=b.sources['BRG_2x4x1p2_PROVISIONAL'];clip=clip_source(b)
    for side in [-1,1]:
        for i,layer in [(1,32.4),(2,30.6)]:
            prefix=f'A{i}_'+str(side).replace('-','_')
            pin=doc.getObject(prefix+'_Pin');pin.setLink(shaft)
            pin.LinkPlacement=cc.hardware_place(s[f'A{i}'],side*center,length)
            ret=doc.getObject(prefix+('_Retainer0' if side==-1 else '_Retainer1'))
            ret.LinkPlacement=cc.hardware_place(s[f'A{i}'],side*p['guide_fixed_outer_clip_y_mm'],.6)
            b.add(bearing,prefix+'_OuterBearing',cc.hardware_place(s[f'A{i}'],side*40.2,1.2),'SpineHardware')
            gap=39.6-(layer+.6);spacer=b.ring('A_OUTER_SPACER_L'+str(round(gap,1)),3,2.05,gap)
            b.add(spacer,prefix+'_OuterSpacer',cc.hardware_place(s[f'A{i}'],side*((layer+.6+39.6)/2),gap),'SpineHardware')
    # Source render shows a broad cap overlapping each guide opening. Capture
    # washers prevent the moving journal pulling through the 4.2mm-wide slot.
    cl=p['guide_slider_journal_length_mm'];cy=p['guide_slider_journal_center_y_mm'];wy=p['guide_capture_washer_center_y_mm'];wt=p['guide_capture_washer_thickness_mm']
    cshaft=b.ring('C_SLIDER_JOURNAL_D1p9_L10p2_GROOVED',1.9,0,cl)
    grooves(b,cshaft,cl);cshaft.PartNumber='C_SLIDER_JOURNAL_D1p9_L10p2_GROOVED'
    washer=b.ring('C_SLOT_CAPTURE_WASHER_D6_T0p6',p['guide_capture_washer_od_mm'],2.05,wt)
    mm=json.loads(doc.PoseController.MotionMap)
    for side in [-1,1]:
        for i in [1,2]:
            prefix=f'C{i}_'+str(side).replace('-','_');P=s[f'C{i}']
            pin=doc.getObject(prefix+'_Pin');pin.setLink(cshaft)
            pin.LinkPlacement=cc.hardware_place(P,side*cy,cl)
            mm[pin.Name].update(y=side*cy,length=cl)
            ret=doc.getObject(prefix+('_Retainer0' if side==-1 else '_Retainer1'))
            ret.LinkPlacement=cc.hardware_place(P,side*p['guide_slider_outer_clip_y_mm'],.6)
            mm[ret.Name].update(y=side*p['guide_slider_outer_clip_y_mm'],length=.6)
            b.add(washer,prefix+'_CaptureWasher',cc.hardware_place(P,side*wy,wt),'SpineHardware',
                  {'kind':'point','point':f'C{i}','y':side*wy,'length':wt})
    # b.add updates b.motion; preserve those additions and the changed placements.
    for name,m in b.motion.items():
        if name not in mm:mm[name]=m
    doc.PoseController.MotionMap=json.dumps(mm);b.motion=mm
    doc.PoseController.addProperty('App::PropertyString','SliderPlateRecovery')
    doc.PoseController.SliderPlateRecovery='C1/A2 and C2/A1 tall contoured fixed plates; Fig1A/MovieS2; dimensions provisional'
    used={o.LinkedObject.Name for o in doc.Objects if o.TypeId=='App::Link'}
    b.sources={k:v for k,v in b.sources.items() if v.Name in used}
    for old in list(b.library.Group):
        if old.Name in used:continue
        if old.TypeId=='PartDesign::Body':
            for ch in reversed(list(old.Group)):doc.removeObject(ch.Name)
        doc.removeObject(old.Name)
    b.library.Visibility=False
    for src in b.sources.values():src.Visibility=False
    doc.recompute()
    return b
