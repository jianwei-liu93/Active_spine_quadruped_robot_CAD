# Spine geometry, kinematics, and transmission

**Status:** implementation specification; no CAD mechanism or physical validation has been completed by this document. Follow [project scope](00_project_specification.md), [evidence register](01_reference_evidence.md), and [verification gates](06_verification_and_acceptance.md).

Source notation: **[P]** = attached main paper; **[S]** = attached supplement, using PDF page numbers; **[M]** = [components and manufacturing](04_components_and_manufacturing.md), which must link each manufacturer claim to its actual source. Equations below are project derivations unless identified as reported. Record unresolved geometry as UNKNOWN or a versioned DESIGN_ASSUMPTION.

## 1. Mechanism and units

The reference has three torso segments and two coupled sagittal outputs. Two servos redundantly drive one spine phase; the physical left/right linkage copies are synchronized by shafts. Neither the two outputs nor the two motors create two independent spine commands. [P, pp. 4-5, 16; S, pp. 7, 16-17, Fig. S9]

Use millimetres for geometry and radians internally. Convert to metres for N, N m, and joules; N mm divided by 1000 is N m. CAD display angles may be degrees, but each API boundary must convert explicitly.

The robot frame is right-handed: X forward, Y left, Z up. The local planar solver uses coordinates (x,z). Positive planar angle rotates +x toward +z, hence corresponds to rotation about **negative Y**. Its 3D rotation is

$$
R_{\mathrm{plane}}(\alpha)=
\begin{bmatrix}
\cos\alpha&0&-\sin\alpha\\
0&1&0\\
\sin\alpha&0&\cos\alpha
\end{bmatrix}.
$$

Embed a planar point as (x,y_layer,z), then apply the central frame's rigid transform. Layer offsets are physical manufacturing parameters: the 2D solver cannot establish link clearance, shaft length, or bearing stack-up.

## 2. Geometry contract and source map

Set O=(0,0), with crank pin

$$
G(\theta)=O+L_1(\cos\theta,\sin\theta).
$$

Use A_1=(H_x,H_y), A_2=-A_1, E_1=(-H_E,0), E_2=(H_E,0) as this project's explicit labeling of Fig. S9. Each slider lies on a fixed line:

$$
C_i=p_i+s_i t_i,\qquad \|t_i\|=1,\qquad s_i^{\min}\le s_i\le s_i^{\max}.
$$

The reference guides are horizontal. Their offsets, usable travel and stops must be specified, not inferred from perspective artwork. The source states that E_1,O,E_2 are collinear and the corresponding anchor pairs have central symmetry. [S, p. 7]

| Physical segment | Chain 1 | Chain 2 | Meaning |
|---|---:|---:|---|
| O to G | L_1 | shared | Crank radius |
| G to B_i | L_2 | L_7 | Crank connecting rod |
| A_i to B_i | L_3 | L_8 | Frame-pivoted rocker |
| B_i to C_i | L_4 | L_9 | Slider connecting rod |
| C_i to D_i | L_5 | L_10 | Output connecting rod |
| E_i to D_i | L_6 | L_11 | Torso output rocker |

The source equalities are L_2=L_7, L_3=L_8, L_4=L_9, L_5=L_10, L_6=L_11. The published optimization result is

$$
(H_x,H_y,L_1,L_2,L_3,L_4)
=(30,8.66,5,30,24.1215,45.7876)\ {\rm mm}.
$$

**L_5, L_6, H_E, guide offsets, and all manufacturing offsets remain to be verified or designed.** Do not silently identify H_E with a similarly named source variable or derive it from the 110 mm exterior body length. The source's missing H_x1 and slider-height h need an explicit geometric mapping. [S, pp. 7, 12-13]

Store every point's parent frame, coordinates, shaft axis, lateral layer, source status, and uncertainty. Store torso mounting transforms relative to E_i separately from rocker length. The reported 1:3:1 torso centerline ratio is a morphology target, not a full frame drawing. [P, p. 14]

The paper input delta and project input theta require a calibrated relation

$$
\theta=\sigma_\delta\delta+\theta_0,\qquad \sigma_\delta\in\{-1,+1\}.
$$

Determine sign and offset from the figure convention, the stated rotation direction, and two distinct documented reference poses. Do not assume that the paper's trigonometric signs match this coordinate frame.

## 3. Exact closure and constructive solver

For each input theta, each chain has five unknowns: two coordinates of B_i, one slider coordinate s_i, and two coordinates of D_i. Its five length equations are

$$
\begin{aligned}
\|B_i-G\|&=a_i,&\|B_i-A_i\|&=b_i,\\
\|C_i-B_i\|&=c_i,&\|D_i-C_i\|&=d_i,\\
\|D_i-E_i\|&=e_i,
\end{aligned}
$$

where (a,b,c,d,e)_1=(L_2,L_3,L_4,L_5,L_6), and chain 2 uses (L_7,L_8,L_9,L_10,L_11). All lengths must be strictly positive. B_1,G,B_2 are **not** one rigid collinear member.

### 3.1 Circle-circle intersection

For centers P,Q and positive radii r,s, let

$$
d=\|Q-P\|,\quad u=(Q-P)/d,\quad n=(-u_z,u_x),
\quad a=\frac{r^2-s^2+d^2}{2d},
\quad h^2=r^2-a^2.
$$

The candidate intersections are

$$
X_\pm=P+a u\pm\sqrt{h^2}\,n.
$$

Existence requires |r-s|<=d<=r+s. Coincident centers require explicit handling: equal radii give infinitely many solutions; unequal radii give none. Neither case may receive an arbitrary solution. Negative h squared beyond roundoff tolerance is infeasible. Clamp a tiny negative value only when it is consistent with floating-point error; record tangency.

Use this once for B_i with centers G,A_i and radii a_i,b_i, then for D_i with centers C_i,E_i and radii d_i,e_i.

### 3.2 Circle-line intersection

For C=p+s t on a unit guide and ||C-B||=r, define

$$
v=p-B,\qquad b=t^\top v,\qquad
\Delta=b^2-(v^\top v-r^2).
$$

Then

$$
s_\pm=-b\pm\sqrt{\Delta}.
$$

Reject genuinely negative Delta; select only candidates within usable guide travel. Use the same dimensionally appropriate squared-length roundoff rule as above. A near-zero discriminant is a conditioning event, not evidence of manufacturing clearance.

For numerical roundoff, use a documented multiple of machine epsilon times the largest relevant squared length. Manufacturing allowances must never enlarge these feasibility tests.

### 3.3 Branch continuation

At an initial pose enumerate both choices at each intersection, discard impossible and physically wrong configurations, and select the assembled branch from Fig. S9 and the intended part arrangement. Store this seed and all branch labels.

Advance theta through a complete revolution. Predict from the previous state and derivative; choose the feasible candidate nearest the prediction after coordinate scaling. Preserve oriented triangle signs except at a documented coalescence of solutions. Bisect the phase step near poor conditioning, ambiguous candidates, or small clearance. Stop with a diagnostic if continuation cannot distinguish a physical branch.

An initial 720-interval cycle is a **project sampling choice**, followed by adaptive refinement; it is not a proof that unsampled collisions cannot occur. The terminal pose must close to the initial pose after 2 pi. Preserve unwrapped motor phase even though the geometry is periodic.

## 4. Residuals, symmetry and conditioning

For each physical segment use the signed length residual

$$
r_\ell=\|P-Q\|-L,\qquad
\max_\ell |r_\ell|\le \tau_{\rm closure},
\qquad \tau_{\rm closure}>0.
$$

Log the maximum absolute residual in mm and the normalized residual divided by a declared reference length. Do not sum signed residuals, compare squared-length errors with an mm tolerance, or permit geometry errors because a rendering looks correct. Freeze numerical and CAD tolerances in [verification](06_verification_and_acceptance.md) before claiming a pass.

Compute the actual output rocker angle using atan2:

$$
\beta_i=\operatorname{atan2}(D_{iz}-E_{iz},D_{ix}-E_{ix}).
$$

The corresponding torso angle is beta_i plus its fixed mounting offset. Derive paper psi_1,psi_2 from the documented reference vectors; use angle unwrapping instead of an unsigned acos.

The paper's desired symmetry is an optimization objective:

$$
e_{\rm sym}(\theta)=\psi_1(\theta)+\psi_2(\theta)-\pi,\qquad
E_{\rm sym}=\max_\theta|e_{\rm sym}(\theta)|.
$$

The supplement reports a **9.29 degree maximum output error**, so symmetry is not an additional holonomic equality. Report the error definition and maximum absolute error for the reconstructed geometry; do not force the historical result to match. Exact closure and approximate symmetry are separate. [S, pp. 12-13, Figs. S11-S12]

For the crank-rocker stage, a useful independent full-turn feasibility condition is

$$
d_{\min}=\big|\|A_i-O\|-L_1\big|\ge |a_i-b_i|,
\qquad
d_{\max}=\|A_i-O\|+L_1\le a_i+b_i.
$$

Tangency still requires conditioning and branch assessment. Check slider reach and output-link existence throughout the cycle. Do not copy a source optimization inequality without validating its geometric meaning.

## 5. Derivatives and mechanical advantage

Stack unknown coordinates into z and exact residuals into f(z,theta)=0. With

$$
J_z=\frac{\partial f}{\partial z},\qquad
z_\theta=-J_z^{-1}f_\theta,
$$

solve a linear system; do not explicitly invert the matrix. A length residual has endpoint gradient (P-Q)/||P-Q||, making analytic assembly straightforward. Alternatively use verified automatic differentiation. Scale coordinates and residuals before reporting singular values and condition numbers.

For output coordinates q_s=g(z,theta),

$$
m(\theta)=\frac{dq_s}{d\theta}=g_z z_\theta+g_\theta,
\qquad
\dot q_s=m(\theta)\dot\theta.
$$

Check derivatives against convergent central differences on the same branch, away from nonsmooth events. Output reversal, where a component of m becomes zero, is expected; it is distinct from loss of rank in J_z. Investigate small linkage moment arms and internal force amplification even when the kinematic solve succeeds.

Ideal virtual work gives

$$
\tau_\theta=m^\top\tau_{\rm delivered}.
$$

Equivalently, for external torso torques tau_ext, quasistatic motor demand is -m transpose tau_ext. Add inertia, friction, gravity and other loads explicitly for a dynamic calculation. A small output velocity ratio does not imply unlimited useful torque: shafts, link forces, bearings and actuator limits still constrain the design. Do not infer a constant torque multiplier or assign a delivered load split from this scalar equation alone.

For a sinusoidal output, the approximate Fourier fit in [P, p. 16] may be used as a comparison curve. It is not exact loop closure, a hardware stop, or a globally single-valued inverse. Geometry must preserve the continuous forward crank branch.

## 6. Redundant actuation and 3D implementation

Represent motor shaft coordinates as

$$
\vartheta_j=\sigma_j\theta+\vartheta_{j0},\qquad
\tau_\theta=\sum_j \sigma_j\tau_j,\quad \sigma_j=\pm1.
$$

The source specifies mirrored synchronization and metal shafts linking the duplicated linkage systems. [P, p. 16; S, pp. 16-17] Mounting signs, zero offsets, encoder interpretation and continuous-rotation control mode must be verified against actual hardware [M]. Do not command principal-angle inverse solutions that reverse a motor every half cycle.

Model a single independent spine phase in the assembly. Provide an assembly/calibration pose and an adjustment procedure for redundant-drive alignment. Offset error can create internal preload even when the visible geometry barely changes. Neither equal current nor equal torque sharing follows from rigid geometric synchronization; any shaft compliance or control-based load-sharing model needs measured or sourced parameters.

Duplicate links as real separate solids with lateral clearances, supported pins, axial retention and realistic stacks. Carry guide end stops, motor/connector envelopes and synchronization shafts into swept-volume checks. The planar graph proves only nominal geometry.

## 7. Required implementation outputs

Provide the parameter/source table, solver code, saved branch seed, crank-to-pose function, joint/frame map, per-phase closure and symmetry results, conditioning/derivative records, and full-cycle interference results. Include uncertainty and missing-parameter reports; do not report these checks as executed until artifacts exist.

Integrate according to [FreeCAD workflow](05_freecad_mcp_workflow.md), [development plan](07_development_plan.md), and [agent ownership](08_agent_orchestration.md). The lead agent alone integrates the shared FreeCAD document.
