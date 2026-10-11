# Leg, cable, and spring mechanics

**Status:** implementation specification, not a completed or validated CAD model. Use [project specification](00_project_specification.md), [reference evidence](01_reference_evidence.md), and [spine coordinates](02_spine_kinematics.md).

**[P]** denotes the main paper; **[S]** the supplement with PDF page numbers; **[M]** denotes verified component data collected in [components and manufacturing](04_components_and_manufacturing.md). Unreported geometry and constitutive parameters remain UNKNOWN until sourced or explicitly designed.

## 1. Reference architecture and dimensional interpretation

Use three physical segments per leg. Proximal shoulder/hip joints are directly actuated; foreleg elbow buffering is passive. Hind-leg knee/ankle motion uses a parallelogram, extension and compression springs, and cable actuation. FLEXOR-F uses one additional motor for both hind knees. This does not guarantee equal loaded knee angles. [P, pp. 4-5, 16; S, pp. 13-17, Figs. S6, S17-S19]

The paper gives a 90 mm summed hind-leg segment length and 60 mm standing height. Supplement Fig. S16 labels hip-to-foot distances for different poses/geometries; these are not interchangeable with total segment length. Preserve the distinction among pivot-to-pivot lengths, contact-point offsets, standing leg reach, and whole-robot height. [P, pp. 4, 16; S, Fig. S16, Table S1]

The biological metatarsal/femur ratio 1.07 is a design reference, not sufficient information to infer every manufactured pivot position. Do not invent segment lengths, spring rates, preload, cable diameter or pulley groove radii.

## 2. Full three-segment kinematics

Use each shoulder/hip mounting frame B and planar coordinates (x,z), with the angle and 3D embedding conventions in [spine kinematics](02_spine_kinematics.md). Let a_1,a_2,a_3 be positive lengths, and q_h,q_k,q_a be signed relative angles. Define

$$
\alpha_1=q_h,\qquad \alpha_2=q_h+q_k,\qquad
\alpha_3=q_h+q_k+q_a,\qquad
e(\alpha)=(\cos\alpha,\sin\alpha).
$$

Then the endpoint and foot orientation are

$$
p_F^B=\sum_{i=1}^{3}a_i e(\alpha_i),\qquad
\alpha_F=\alpha_3.
$$

Add a rigid contact offset R_2(alpha_F)c_F if the actual pad contact is not that endpoint. For a 3D point, embed as `(x,0,z)` in the shoulder/hip frame, plus any actual part-local lateral offset. Put the leg's mounting translation, including its left/right lateral position, in `T_SB` exactly once. Use the torso-dependent transform

$$
\bar p_F^W=T_{WS}\,T_{SB}\,\bar p_F^B,\qquad
T_{WS}=T_{WC}T_{CS}(\theta),
$$

where C is the central spine, S is the relevant front/rear torso, and bars indicate homogeneous coordinates. T_WC carries the whole robot's position and orientation; spine phase alone does not determine the world pose. CAD and simulation must use the same joint centers and contact geometry.

With J e(alpha)=(-sin(alpha),cos(alpha)), endpoint Jacobian column j is

$$
\frac{\partial p_F^B}{\partial q_j}
=\sum_{i=j}^{3}a_i J e(\alpha_i),
\qquad (q_1,q_2,q_3)=(q_h,q_k,q_a).
$$

Include the contact-offset derivative when present. Reflection between left/right hardware does not itself reverse the geometric sagittal angle; record each servo's mounting sign and zero separately.

The supplement's S32 includes three segments, whereas its S34 omits the third term and S35 introduces a_1+a_3 without a consistent explicit reduction. Consequently implement the full transform above and verify any reduction from the actual linkage. [S, p. 14, Eqs. S32-S35]

## 3. Derive ankle coupling from the assembled parallelogram

Name the four-bar vertices P_0,P_1,P_2,P_3 and identify which rigid bodies carry each pivot. Attach points to their parent bodies with fixed local offsets. Solve the actual loop using the intersection and branch methods in [spine kinematics](02_spine_kinematics.md).

For an ideal uncrossed parallelogram,

$$
P_1-P_0=P_2-P_3,\qquad
P_3-P_0=P_2-P_1.
$$

These equalities establish parallel opposite members. Only after mapping the thigh and distal segment to those members may one conclude that their absolute orientations differ by a fixed kappa:

$$
\alpha_3-\alpha_1=\kappa
\quad\Longrightarrow\quad q_a=\kappa-q_k.
$$

The sign and kappa depend on attachment orientation. Crossed assembly branches, offset levers, or a compliant member may invalidate this relation. For a more general scalar closure c(q_h,q_k,q_a)=0,

$$
\frac{\partial q_a}{\partial q_j}
=-\frac{c_{q_j}}{c_{q_a}},\qquad j\in\{h,k\},
$$

where the denominator must be nonzero. For additional passive coordinates use a matrix implicit solve. A slider or extensible element must retain its own coordinate.

As a checkable special case only, if kappa=0 and the foot has no extra offset:

$$
p_F=(a_1+a_3)e(q_h)+a_2e(q_h+q_k).
$$

Writing A=a_1+a_3 and rho squared=x squared+z squared,

$$
\cos q_k=\frac{\rho^2-A^2-a_2^2}{2Aa_2},\quad
q_k=\pm\arccos(\cos q_k),\quad
q_h=\operatorname{atan2}(z,x)
-\operatorname{atan2}(a_2\sin q_k,A+a_2\cos q_k).
$$

Select a feasible, continuous branch and enforce physical limits. Clamp an acos argument only for roundoff; values materially outside [-1,1] are unreachable. If kappa differs from zero, use the unreduced FK or derive a new reduction.

## 4. Cable paths, tangent points and winding

A cable path is an ordered list of anchors, guides, pulleys and spool contacts. Each point belongs to a named body. Record cable-centerline radii and the side/wrap sense of every contact. Straight segments through solid pulleys are invalid.

The geometric length is

$$
\ell(q)=\sum_j\|v_{j+1}-v_j\|
+\sum_k r_k\Omega_k+\ell_{\rm fixed},
$$

where Omega is a positive physical wrap angle, continued on the chosen routing branch. Model out-of-plane segments in 3D; planar formulas apply only within a common pulley plane.

For an external point P and pulley center C, radius r, let d=||P-C||>r, beta=atan2(P_z-C_z,P_x-C_x). Tangency candidates are

$$
T_\pm=C+r e\!\left(\beta\pm\arccos(r/d)\right).
$$

Reject anchors inside a pulley. At d=r the tangent degenerates and needs explicit treatment.

For two circles, let u=(C_2-C_1)/d and choose s=+1 for an external common tangent or s=-1 for an internal tangent. With

$$
c=(r_1-sr_2)/d,\qquad
n_\pm=c u\pm\sqrt{1-c^2}\,Ju,
$$

the contact points are T_1=C_1+r_1 n and T_2=C_2+s r_2 n. Require |c|<=1. Select the physically routed branch; do not choose a crossing tangent merely because it is shortest.

Compute arcs from contact polar angles and the declared wrap sense. Use winding-count continuity to avoid artificial 2 pi jumps. Multi-turn spools require a winding model, not repeated selection of a minimum arc.

The source reports a **13 mm outer-diameter nylon winding wheel**. Its effective cable radius is not automatically 6.5 mm: groove depth, cable diameter, hole placement and changing winding layers matter. The reported 31 mm underactuated and 317 mm active cable lengths apply to the paper geometry; recompute lengths for this design. [S, pp. 14-17, Eqs. S36-S43, Figs. S18-S19]

For an ideal constant-radius, positively taking-up drum,

$$
\lambda_b(u)=\lambda_{b0}-\sigma_b r_b u,\qquad \sigma_b=\pm1.
$$

Lambda is available unstretched free-path length after accounting for the wound portion. Do not count the same winding both in lambda and in the geometric path. A moving hole anchor can initially generate a chord-length change instead of r times angle; explicitly model that regime and its transition to wrap contact.

## 5. Bilateral routing and slack

The source's nominal factor-of-two path formula does not establish how length is constrained under asymmetric loading. [S, p. 15, Eq. S38] Resolve the hardware topology:

| Routing | Mechanical constraint | Consequence |
|---|---|---|
| Two independently secured branches on a common drum | Each branch has its own lambda_b(u), fixed by its anchor/winding | One motor coordinates take-up; passive compliance can still produce unequal knee angles |
| One continuous freely redistributing cable | Only total path length is fixed | Differential motion is possible; ideal frictionless routing equalizes tension, not knee angles |

Specify actual terminations or locks before choosing a model. Until verified, document both alternatives and mark any selected topology as a design decision. Friction can invalidate equal-tension assumptions; geometry alone cannot establish a capstan coefficient or hysteresis.

For an ideal inextensible, tension-only branch:

$$
g_b=\lambda_b(u)-\ell_b(q)\ge0,\qquad
T_b\ge0,\qquad T_b g_b=0.
$$

Positive g means available slack; a taut branch satisfies equality. Negative g is infeasible unless cable extension or another compliant coordinate is modeled. The cable force on generalized leg coordinates is

$$
Q_q^{\rm cable}=-\sum_b T_b\,\nabla_q\ell_b.
$$

For a freely redistributing loop apply complementarity to its total path, not to two fictitious separately fixed halves.

If cable stretch is intentionally modeled, a simple identified law is

$$
T_b=k_{cb}[\ell_b-\lambda_b]_+,\qquad
U_{cb}=\tfrac12 k_{cb}[\ell_b-\lambda_b]_+^2.
$$

Here [x]_+=max(x,0). Do not invent k_cb, double-count a physical series spring as cable stiffness, or allow damping to generate negative tension. Slack-to-taut transitions are nonsmooth events.

## 6. Separate extension and compression springs

Each leg has extension and compression springs in the reference. Their anchor locations and constitutive data are required; decorative spring geometry is insufficient. [S, pp. 16-17]

For anchors A(q),B(q), let

$$
L=\|B-A\|,\qquad \hat d=(B-A)/L.
$$

An **extension spring** pulls its anchors together. For opened coils, extension x=L-L_f>0, spring rate k_e and verified initial tension F_i:

$$
F_e=F_i+k_e x,\qquad
U_e=F_i x+\tfrac12 k_e x^2,\qquad
Q_q^e=-F_e\nabla_q L.
$$

Closed coils, relaxed hooks and slack require a separate unilateral state; the opened-coil law must not produce compression. A zero initial-tension model is allowed only as an explicit assumption or verified property. Installed preload is determined by the actual installed extension and initial tension, not an unexplained additional force offset.

A **compression spring** pushes its seats apart. With free length L_f and compression c=[L_f-L]_+:

$$
F_c=k_c c,\qquad
U_c=\tfrac12 k_c c^2,\qquad
Q_q^c=+F_c\nabla_q L.
$$

Installed compression already accounts for preload. Require L>=L_solid+margin over the motion range, with positive margin specified in the manufacturing design. Define seat retention, guide alignment and maximum allowable deflection; a linear force law cannot certify coil-bind, buckling or fatigue limits.

Forces on anchor B are -F_e hat d for extension and +F_c hat d for compression; A receives the opposite. These signs provide a direct implementation sanity check. Use measured/manufacturer spring data [M]. If unavailable, keep spring sizing parametric and withhold load-capacity claims.

## 7. Moment arms, actuator work and passive states

For a tensile path, signed moment arm about q_j is

$$
r_j(q)=-\frac{d\ell}{dq_j},\qquad \tau_j=T r_j.
$$

Use the **total derivative** after ankle/parallelogram constraints and passive-coordinate elimination, not the partial derivative holding a dependent ankle fixed. A length derivative in mm/rad yields N mm when multiplied by tension.

The resisting cable torque on the drum is T_b lambda_b'(u), so ideal driving demand is

$$
\tau_u=-\sum_b T_b\lambda_b'(u).
$$

For positive constant-radius take-up this becomes sum sigma_b r_b T_b. Check signed power balance: cable work on the legs is -sum T_b dot(ell_b); a taut inextensible path has dot(ell_b)=dot(lambda_b). Include stored spring energy, gravity, friction and inertia when interpreting total motor work.

A compliant mechanism's loaded pose generally cannot be determined from drum angle alone. Solve passive coordinates using equilibrium or dynamics, for example

$$
M(q)\ddot q+h(q,\dot q)
=Q_{\rm motor}+Q_{\rm cable}+Q_{\rm springs}
+J_F^\top F_{\rm contact},
$$

together with cable complementarity. This equation uses independent generalized coordinates after rigid-loop elimination. If redundant body or joint coordinates are retained instead, include the rigid-constraint reaction term `J_c(q)^T * lambda_c` and impose `c(q)=0` with consistent velocity/acceleration constraints. For a quasistatic demonstration set accelerations to zero and state applied loads. Do not present a geometrically assigned knee trajectory as a simulated spring response.

## 8. Required checks and integration

Before acceptance, verify full FK against CAD pivot locations; reconstruct every four-bar closure; compare path derivatives and moment arms with finite differences away from routing/slack transitions; test zero-work and energy signs; and check extreme poses, cable contact transitions, spring travel, anchors, fasteners and swept clearances. Include asymmetric hind-leg loading for the chosen bilateral topology.

Record required inputs, unresolved interfaces, branch seeds and declared load cases in the reproducible model. Missing spring or cable properties prevent physical-performance certification but do not prevent geometric progress.

Use [FreeCAD workflow](05_freecad_mcp_workflow.md), [acceptance](06_verification_and_acceptance.md), [development plan](07_development_plan.md), and [orchestration](08_agent_orchestration.md). These are required future checks, not claims that tests or CAD builds have already run.
