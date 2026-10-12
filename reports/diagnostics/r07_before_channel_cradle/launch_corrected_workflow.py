import sys,subprocess,json
from pathlib import Path
root=Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD');sys.path.insert(0,str(root/'src'))
from verify_motion_package_r07 import prepare_launch,collect
subprocess.run([sys.executable,str(root/'reports/tmp/motion_package_r07/launch_coarse.py')],check=True)
s=collect('coarse',12);print('CORRECTED_COARSE',s['status'],s['records_found'],flush=True)
if s['status']=='PASS':
 launcher=prepare_launch('full',24);print('FULL_LAUNCHED',24,flush=True);subprocess.run([sys.executable,str(launcher)],check=True)
 s=collect('full',24);print('FULL_FINISHED',s['status'],s['records_found'],flush=True)
else: print('FULL_NOT_RUN_COARSE_GATE',flush=True)
