"""Capture detached inputs on GUI thread before a background read-only sweep."""
from types import SimpleNamespace

class FrozenDocument:
    def getObject(self,name):return self._objects.get(name)

def capture(doc):
    import FreeCAD as App
    frozen=FrozenDocument();frozen.Name=doc.Name;frozen.FileName=doc.FileName
    frozen._objects={o.Name:SimpleNamespace(Name=o.Name,TypeId=o.TypeId) for o in doc.Objects}
    sources={o.LinkedObject.Name for o in doc.Objects if o.TypeId=='App::Link'}
    for obj in doc.Objects:
        target=frozen._objects[obj.Name]
        if obj.Name in ('PoseController','DesignParameters') or obj.Name in sources:
            target.PropertiesList=list(obj.PropertiesList)
            for key in obj.PropertiesList:
                value=getattr(obj,key)
                if isinstance(value,(str,int,float,bool)):setattr(target,key,value)
                elif hasattr(value,'Value') and isinstance(value.Value,(int,float)):
                    setattr(target,key,float(value.Value))
            target.PropertiesList=[key for key in obj.PropertiesList if hasattr(target,key)]
        if obj.TypeId=='App::Link':
            target.LinkPlacement=App.Placement(obj.LinkPlacement)
            target.LinkedObject=frozen._objects[obj.LinkedObject.Name]
            target.Shape=obj.Shape.copy(copyGeom=True,copyMesh=False)
        if obj.Name in sources:
            target.Shape=obj.Shape.copy(copyGeom=True,copyMesh=False)
            target.Placement=App.Placement(obj.Placement)
    frozen.Objects=[frozen._objects[o.Name] for o in doc.Objects]
    frozen.PoseController=frozen.getObject('PoseController')
    return frozen
