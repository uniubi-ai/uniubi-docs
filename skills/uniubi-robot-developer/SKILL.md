---
name: uniubi-robot-developer
description: Guide UniUbi robot development across SDK, ROS 2, and uniubi_rl_lab. Use for choosing a development path or coordinating cross-project changes, policy integration, and validation; use a specialist directly for a single-domain task.
---

# UniUbi Robot Developer

Turn the user's robot-development goal into changes and evidence in the appropriate repositories. This skill is the entry point for the ecosystem, not a requirement to use every specialist.

## Establish the working context

- Locate the user's actual checkouts and read their applicable AGENTS.md and README. Repositories can be separate, nested, or remote; do not assume a particular workstation, SSH host, or sibling layout.
- For affected repositories, inspect branch, commit, working-tree changes, and dependency pins. Preserve existing work. Use the user's designated workspace as authority.
- Determine only the context needed for the request: application vs. policy development, High-level vs. Low-level, language, runtime location, target firmware/SDK, or training environment. Reuse known answers; ask only when a missing answer changes the implementation.
- Use [repository and document routing](references/repositories.md) to locate source and documentation. Prefer the selected checkout/revision. Public default-branch pages are discovery aids, not proof of compatibility with an installed release.

## Select focused guidance

| Work | Skill |
| --- | --- |
| C++/Python SDK, observations, control lifecycle, media, native build | `uniubi-robot-sdk` |
| ROS 2 nodes, launch, messages, services, bridge integration | `uniubi-robot-ros2` |
| RL tasks, rewards, training, checkpoint replay and policy export | `uniubi-robot-rl` |

For each relevant domain, read its SKILL.md and only the references needed for this task. First use the host's available skill catalog; otherwise look for the named folder beside this skill or in a user-provided skills source directory. Do not assume the docs checkout remains beside an installed skill.

Reading specialist guidance does not require spawning agents, special invocation tools, or switching models. Specialists are independently usable; do not route them back through this entry point.

If a specialist is unavailable, state that briefly and continue from the relevant repository's documentation and source when sufficient. Do not invent its instructions, silently install tools, or block a simple supported task solely because the specialist is absent.

## Coordinate cross-project work

Keep changes in the smallest set of repositories that owns the requested behavior. Establish each boundary before implementing across it:

- **SDK to ROS 2:** confirm existing SDK capability, wire/message types, ROS topic/service schema, units, timestamps, namespaces, QoS, and lifecycle. Check whether the bridge already exposes the requested data before adding a new path.
- **RL to SDK:** identify the checkpoint and saved run configuration; compare exported model inputs/outputs, observation order and history, normalization, action/joint order, scaling, offsets, clipping, policy period, and reset behavior against the deployment adapter. Do not assume equal tensor sizes imply equivalent semantics.
- **RL to simulation to hardware:** distinguish policy replay, local Sim2Sim, SDK Mock/Sim2Sim, and hardware validation. Reuse a matching evaluation protocol when comparing policies.
- **Version changes:** check firmware compatibility, repository pins, runtime libraries, Python bindings, and generated message artifacts together. Do not upgrade unrelated components to make an example compile.

Follow the relevant specialist for implementation details. For a small single-domain task, complete it directly without creating a cross-project plan.

## Validate and report

Select the smallest useful check for the change: source/config checks, import/build, unit or integration tests, bounded training, replay, or simulation. A request to write code does not by itself authorize device deployment, firmware changes, real-robot motion, or an unbounded training run. Honor existing explicit authorization without asking again.

For hardware work, read the selected revision's control guide before operating. Read-only status work must not acquire motion control as a convenience. Connection success, accepted RPCs, and simulation results are different from verified physical behavior.

Deliver the changed files and relevant revisions, commands/checks actually run, observed results, and unverified stages. When handing an artifact to another domain, include the model/config or interface contract needed to reproduce it.
