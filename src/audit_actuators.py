"""Count actual native motor instances by authoritative manufacturer PartNumber."""
import json
from collections import Counter
from pathlib import Path
EXPECTED={'DYNAMIXEL_XL330_M077_T':2,'DYNAMIXEL_XC330_M181_T':5}

def run(doc,root,revision='r04'):
    rows=[{'instance':o.Name,'manufacturer_model':o.LinkedObject.PartNumber,'nominal_mass_g':o.LinkedObject.PurchasedMass_g,'source_definition':o.LinkedObject.Name} for o in doc.Objects if o.TypeId=='App::Link' and o.LinkedObject.MaterialName=='motor']
    actual=Counter(r['manufacturer_model'] for r in rows)
    r={'revision':revision,'status':'PASS' if dict(actual)==EXPECTED else 'FAIL','scope':'Actual installed native motor instances; complete FLEXOR-F architecture requires two XL and five XC','expected':EXPECTED,'actual':dict(actual),'instances':rows,'paper_names':{'XL330–077-T':'XL330-M077-T','XC-M181-T':'XC330-M181-T'},'limits':'Case envelopes and nominal catalog masses do not verify shaft/spline, mounting datums, control calibration or electrical power budget.'}
    Path(root,f'reports/verification/{revision}_actuators.json').write_text(json.dumps(r,indent=2)+'\n');return r
