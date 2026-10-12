// Reproducible diagnostic backend. No FreeCAD document or geometry mutation.
#include <BRepTools.hxx>
#include <BRep_Builder.hxx>
#include <BRepGProp.hxx>
#include <GProp_GProps.hxx>
#include <TopoDS_Shape.hxx>
#include <Standard_Version.hxx>
#include <cmath>
#include <cstddef>

extern "C" const char* occt_volume_version() { return OCC_VERSION_COMPLETE; }

// algorithm=0: adaptive Gauss; algorithm=1: adaptive Gauss-Kronrod + spans.
// Return 0 only when every file was read and every numerical result was finite.
extern "C" int occt_volume_batch(const char* const* paths, std::size_t count,
    double eps, int algorithm, double* volumes, double* errors,
    std::size_t* failed_index) {
    if (!paths || !volumes || !errors || !failed_index || count == 0 ||
        !(eps > 0 && eps <= 0.001) || (algorithm != 0 && algorithm != 1)) return 1;
    for (std::size_t i=0; i<count; ++i) {
        *failed_index=i;
        try {
            TopoDS_Shape shape; BRep_Builder builder;
            if (!BRepTools::Read(shape, paths[i], builder) || shape.IsNull()) return 2;
            GProp_GProps properties;
            errors[i] = algorithm == 1
                ? BRepGProp::VolumePropertiesGK(shape, properties, eps, true, true, false, false, false)
                : BRepGProp::VolumeProperties(shape, properties, eps, true, false);
            volumes[i] = properties.Mass();
            if (!std::isfinite(volumes[i]) || volumes[i] <= 0 ||
                !std::isfinite(errors[i]) || errors[i] < 0) return 3;
        } catch (...) { return 4; }
    }
    *failed_index=count;
    return 0;
}

// Numerical domain subdivision over UNCHANGED input faces; no topology repair.
// Uses public OCCT BRepGProp_TFunction (oriented volume boundary integrand).
#include <BRepTools.hxx>
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepCheck_Shell.hxx>
#include <BRepGProp_Face.hxx>
#include <BRepGProp_Domain.hxx>
#include <BRepGProp_TFunction.hxx>
#include <math_KronrodSingleIntegration.hxx>
#include <TopoDS.hxx>
#include <TopExp_Explorer.hxx>
#include <TColStd_HArray1OfReal.hxx>
#include <cmath>
extern "C" int occt_volume_domain(const char* path,int subdivisions,int order,double eps,double* volume,double* error,int* pieces) {
 if(!path||!volume||!error||!pieces||subdivisions<1||subdivisions>32||order<3||order>63||order%2!=1||!(eps>0&&eps<=.001))return 8;
 try {
  TopoDS_Shape s;BRep_Builder builder;
  if(!BRepTools::Read(s,path,builder)||!BRepCheck_Analyzer(s).IsValid())return 1;
  int solids=0,shells=0;
  for(TopExp_Explorer x(s,TopAbs_SOLID);x.More();x.Next())++solids;
  if(solids!=1)return 9;
  for(TopExp_Explorer x(s,TopAbs_SHELL);x.More();x.Next()){++shells;BRepCheck_Shell check(TopoDS::Shell(x.Current()));if(check.Closed(false)!=BRepCheck_NoError)return 10;}
  if(!shells)return 10;
  gp_XYZ sum(0,0,0);int count=0;
  for(TopExp_Explorer x(s,TopAbs_VERTEX);x.More();x.Next()){sum+=BRep_Tool::Pnt(TopoDS::Vertex(x.Current())).XYZ();++count;}
  if(!count)return 2;sum/=count;gp_Pnt origin(sum);
  long double mass=0,err=0;*pieces=0;double shift[3]={0,0,0};
  for(TopExp_Explorer x(s,TopAbs_FACE);x.More();x.Next()){
   auto face=TopoDS::Face(x.Current());
   if(face.Orientation()!=TopAbs_FORWARD && face.Orientation()!=TopAbs_REVERSED)return 3;
   BRepGProp_Face surface(true);surface.Load(face);double u0,u1,v0,v1;surface.Bounds(u0,u1,v0,v1);
   BRepGProp_Domain boundary(face);
   if(!boundary.More())return 7;
   for(boundary.Init();boundary.More();boundary.Next()){
    surface.Load(boundary.Value());Handle(TColStd_HArray1OfReal) knots;
    surface.GetTKnots(surface.FirstParameter(),surface.LastParameter(),knots);
    for(int k=knots->Lower();k<knots->Upper();++k){
     double left=knots->Value(k),right=knots->Value(k+1);
     for(int j=0;j<subdivisions;++j){
      double a=left+(right-left)*j/subdivisions,b=left+(right-left)*(j+1)/subdivisions;
      if(!(b>a))continue;
      BRepGProp_TFunction integrand(surface,origin,true,shift,u0,eps*.1/(b-a));
      integrand.SetValueType(GProp_Mass);integrand.SetNbKronrodPoints(order);integrand.Init();
      math_KronrodSingleIntegration quad(integrand,a,b,order,eps*.9,1000);
      if(!quad.IsDone())return 4;
      mass+=quad.Value();err+=std::abs(quad.AbsolutError())+std::abs(integrand.AbsolutError())*(b-a);++*pieces;
     }
    }
   }
  }
  *volume=(double)mass;*error=(double)(err/std::abs(mass));
  return std::isfinite(*volume)&&*volume>0&&std::isfinite(*error)?0:5;
 }catch(...){return 6;}
}
