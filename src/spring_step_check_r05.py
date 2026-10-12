import os
if os.environ.get("SPRING_READ_RESULT"):
 print(open("/tmp/spring_step_check_r05.json").read(),flush=True)
else:
 """Isolated read-only native/STEP geometry diagnostic; run in FreeCAD CLI."""
 import FreeCAD as App, Part, MeshPart, json, math, os
 from collections import Counter
 root='/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD'
 doc=App.openDocument(root+'/cad/flexor_r05_robot.FCStd')
 name='LEG_r02_foreL_COMPRESSION_WIRE_L24p73863375'
 a=doc.getObject(name).Shape.copy()
 b=Part.read(root+'/reports/tmp/step_part_diagnostics/'+name+'.step')
 if os.environ.get('SPRING_SURFACES'):
  for label,shape in [('native',a),('step',b)]:
   print(label,'edges',[e.Length for e in shape.Edges],flush=True)
  sa=[f.Surface for f in a.Faces if type(f.Surface).__name__=='BSplineSurface'][0]
  sb=[f.Surface for f in b.Faces if type(f.Surface).__name__=='BSplineSurface'][0]
  print('degrees',sa.UDegree,sa.VDegree,sb.UDegree,sb.VDegree,flush=True)
  print('knot max deltas',max(abs(x-y) for x,y in zip(sa.getUKnots(),sb.getUKnots())),max(abs(x-y) for x,y in zip(sa.getVKnots(),sb.getVKnots())),flush=True)
  print('multiplicities',sa.getUMultiplicities()==sb.getUMultiplicities(),sa.getVMultiplicities()==sb.getVMultiplicities(),flush=True)
  print('weight max delta',max(abs(x-y) for ra,rb in zip(sa.getWeights(),sb.getWeights()) for x,y in zip(ra,rb)),flush=True)
  print('knots',sa.getUKnots()==sb.getUKnots(),sa.getVKnots()==sb.getVKnots(),flush=True)
  pa,pb=sa.getPoles(),sb.getPoles()
  print('poles dims',len(pa),len(pa[0]),len(pb),len(pb[0]),flush=True)
  if len(pa)==len(pb) and len(pa[0])==len(pb[0]):
   print('pole maximum difference',max((x-y).Length for ra,rb in zip(pa,pb) for x,y in zip(ra,rb)),flush=True)
  os._exit(0)
 r={'name':name,'native_volume':a.Volume,'step_volume':b.Volume,'methods':[x for x in dir(a) if 'mass' in x.lower() or 'volume' in x.lower()]}
 for label,s in [('native',a),('step',b)]:
  r[label]={'valid':s.isValid(),'faces':len(s.Faces),'edges':len(s.Edges),'vertices':len(s.Vertexes),'surfaces':dict(Counter(type(f.Surface).__name__ for f in s.Faces)),'area':s.Area,'meshes':[]}
  for d in [0.02,0.005,0.001]:
   mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=d,AngularDeflection=0.08,Relative=False)
   points,facets=mesh.Topology
   v=math.fsum(points[i].dot(points[j].cross(points[k]))/6 for i,j,k in facets)
   r[label]['meshes'].append({'deflection':d,'facets':len(facets),'signed_volume':v,'mesh_volume':mesh.Volume,'solid':mesh.isSolid()})
   print(label,d,len(facets),v,flush=True)
   with open('/tmp/spring_step_check_r05.json','w') as f: json.dump(r,f,indent=2)
 # surface point samples from each triangle mesh, subsampled <= 1500 per direction
 for label,s,t in [('native_to_step',a,b),('step_to_native',b,a)]:
  points,facets=s.tessellate(0.01)
  stride=max(1,len(points)//1500)
  distances=[Part.Vertex(p).distToShape(t)[0] for p in points[::stride]]
  r[label]={'sample_count':len(distances),'maximum_distance_mm':max(distances),'rms_distance_mm':math.sqrt(math.fsum(x*x for x in distances)/len(distances))}
  print(label,r[label],flush=True)
 with open('/tmp/spring_step_check_r05.json','w') as f: json.dump(r,f,indent=2)
 App.closeDocument(doc.Name)
