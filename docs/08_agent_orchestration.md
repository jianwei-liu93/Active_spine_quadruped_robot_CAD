# 08 — Codex model and subagent orchestration

**Guidance checked:** 2026-10-11. Model availability and configuration syntax depend on the installed client and account. This is a practical project recommendation based on current official documentation, not a published FreeCAD-specific model benchmark.

## 1. Role allocation

| Role | Suggested model | Reasoning effort | Scope |
|---|---|---|---|
| Lead | `gpt-6.1-sol` | `high` | Architecture, interfaces, mechanism reasoning, live FreeCAD, integration, acceptance |
| Routine worker | `gpt-6-luna` | `high` | Bounded source extraction, supplier data, BOM, documentation, straightforward assigned source modules |
| Complex bounded implementation | `gpt-6.1-sol` | `medium` | Component or verification code with already defined interfaces |
| Independent reviewer | `gpt-6.1-sol` | `high` | Mechanism correctness and final integration evidence |
| Difficult-issue escalation | `gpt-6-astra` | Start `low`; use `medium` when justified | Unresolved geometric/mechanical issue with a minimal reproducer |

The lead can use lower effort for later routine edits after the design is stable. `xhigh`, `max`, and `ultra` are not default settings for this project. Use additional effort only for a concrete unresolved issue or a demonstrated improvement.

Official sources describe Sol as suitable for complex coding/professional work, Luna for focused repeatable work, and Astra for the most demanding tasks. The high-effort lead choice is our engineering recommendation because incorrect mechanism interpretation can invalidate many downstream parts.

## 2. Mandatory collaboration boundary

**Only the lead owns the live FreeCAD MCP session, canonical document, shared parameter schema, and integration state.** All workers follow this rule even if inherited tools technically expose MCP writes.

FreeCAD operations that change geometry, placements, active documents, visibility used for verification, saves, or exports should be serialized by the lead. A subagent may inspect static exports and reports or draft an assigned module, then return it for integration.

Worktrees separate source changes; they do not isolate access to the same application instance. Never run two agents against the same mutable FreeCAD document concurrently.

Use at most **three concurrent subagents**, with **no recursive delegation**. This is a cap, not a requirement to keep every slot occupied.

## 3. Good delegated tasks

- Extract a specific source table and reconcile units/page references.
- Verify an exact motor/bearing/horn interface from a manufacturer's drawing.
- Write a named part-generation module using frozen dimensions and attachment frames.
- Populate BOM rows from verified component records.
- Derive/check one mechanism relation or inspect one bounded report.
- Prepare assembly instructions or drawing annotations after geometry is stable.

Keep decisions about source interpretation, missing geometry, structural assumptions, fit selection, allowable motion, and final acceptance with the lead. Workers may propose options with evidence; they do not silently alter the shared design.

## 4. Handoff contract

Every delegated task must include:

1. Purpose and exact scope.
2. Assigned files; files that remain owned elsewhere.
3. Relevant parameter revision, units, frame definitions, and interface dimensions.
4. Evidence/source subset needed for the task.
5. Expected output and acceptance check.
6. Actual model/effort requested, if the client exposes selection.

Worker returns should include changed paths, concise findings, checks actually performed, source references, and blockers. Avoid flooding the lead with entire PDFs or unfiltered logs.

Use deterministic tools for enumeration, formatting, unit conversion, numeric sweeps, mass sums, file hashes, and repeated checks. A model need not narrate every iteration.

## 5. Escalation and review

Allow a cheaper worker up to two materially different repair attempts on a concrete failure. Then escalate to the lead or a Sol worker with a small reproducible case and actual error output. Two repetitions of the same failing action are not two distinct approaches.

Use Astra selectively for an issue Sol has not resolved, or when independent stronger judgment has a clear purpose. Bound the request to the relevant graph, equations, dimensions, or part stack. Do not send the whole project for an unconstrained redesign.

Plan two bounded independent reviews:

- After the mechanism and its implementation evidence exist, before relying on it for detailed whole-robot integration.
- After the complete native/export package exists, focusing on concrete remaining correctness/manufacturing risks.

Rerun reviews or checks only after relevant changes or unresolved findings. Record the actual findings and resolution; a model's approval is not physical validation.

## 6. Local configuration

Use `/model` to verify locally available models/efforts. Current Codex releases support a launch such as:

```bash
codex -m gpt-6.1-sol -c 'model_reasoning_effort="high"' --search
```

Optional settings to merge into the local/project configuration alongside the existing MCP configuration:

```toml
model = "gpt-6.1-sol"
model_reasoning_effort = "high"

[agents]
enabled = true
max_concurrent_threads_per_session = 3
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "high"
```

This block is documentation, not an automatically installed configuration. Preserve existing MCP entries and account settings. Check the installed client's schema before applying it.

Subagents can inherit the parent model and effort when no override is given. Request cheaper models explicitly. Current documented custom-agent files may override resolved spawn/default settings; inspect their configuration if actual routing differs from the request.

If model overrides, custom agents, or delegation are unavailable, continue using an available model and report the limitation. Do not claim that a different model/effort ran merely because the prompt requested it. Do not assume a model can silently change its own running session settings.

## 7. Cost interpretation

At the time checked, official standard API text-token rates per million tokens were Sol input/output **$2/$10**, Luna **$0.10/$0.50**, and Astra **$10/$50**. These rates exclude cache behavior, tool usage, long-context adjustments, and other processing options; they are not a quote for ChatGPT plan credits or the total project cost.

Cheaper workers save money only when the task is sufficiently constrained and the resulting work needs little rework. Additional parallel agents can increase total token use. Favor lower total cost per accepted result over maximizing parallelism.

## 8. Official references

- [Codex models and availability](https://learn.chatgpt.com/docs/models)
- [Codex subagents and configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-6.1 Sol specifications and pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
- [GPT-6 Luna specifications and pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [GPT-6 Astra specifications and pricing](https://developers.openai.com/api/docs/models/gpt-6-astra)

Recheck these sources when updating the orchestration policy. The mechanical design documents remain usable if the model lineup changes.
