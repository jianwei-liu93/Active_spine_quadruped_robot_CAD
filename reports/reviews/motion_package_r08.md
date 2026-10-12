# r08 motion package verification

Status: PREPARED; CAD checks NOT_RUN pending explicit lead native SHA freeze.

`src/verify_motion_package_r08.py` is revision-isolated from the preserved r07 verifier. Inputs are `cad/flexor_r08_robot.FCStd` and `parameters/assembly_r08.json`. It requires a frozen native SHA, configuration SHA, and source dependency SHA set before reading CAD. Canonical native sources and placements are fingerprinted before/after; native file and freeze inputs are checked after each run. Qualified exact compression BRep reuse remains subject to the r07 helper's generator/length/BRep hash checks and shape validation. No spring envelope substitutes, pair exemptions, or canonical writes are used.

The unchanged trajectory manifests contain 105 coarse states and 985 full states. Full trajectories include one-coordinate leg ±10 degree ranges, wheel 0..90 degrees, both coordinated/asymmetric directions subdivided so every coordinate increment is at most one degree, and adverse fore/hind combined spine gait over 0..360 degrees. Coverage is finite and is not a full coordinate-product, continuous-clearance, loaded-equilibrium, or fabrication-release claim.

Generated isolated CLI wrappers live in `reports/tmp/motion_package_r08`. Coarse launcher uses six workers; full launcher uses 24 workers and may run only after coarse PASS. JSON partitions and summaries live in `reports/verification/r08_motion_partitions` and record actual coverage, source/config/native hashes, raw overlaps, guide warnings, errors, safety-pair distances, and native immutability evidence.

A separate bounded `cage_spine_361.py` wrapper checks the actual two half-cage BReps against all physical instances at each integer spine angle 0..360 inclusive, with neutral leg and wheel states. It checks 969 distinct pairs per angle (including the two cages against each other), uses only AABB-disjoint broadphase pruning and exact common volume, and records worst pair and angle without exceptions. It does not certify the 985-state combined trajectory scope.

Preparation checks actually executed: Python compilation; manifest generation and pose-descriptor math validation for all 105/985 states; full maximum coordinate increment 1.0000000000000395 degrees (floating-point tolerance 1e-9). Native CAD checks remain NOT_RUN.
