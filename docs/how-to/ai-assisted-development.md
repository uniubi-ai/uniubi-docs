# AI-Assisted Robot Development

**English** | [简体中文](ai-assisted-development.zh-CN.md)

## Goal

Use an AI coding assistant to develop UniUbi SDK applications, ROS 2 integrations, and RL policies with guidance grounded in your actual source version. The skills are published in this documentation repository and work across the UniUbi projects.

## Choose skills

| Skill | Responsibility |
| --- | --- |
| [uniubi-robot-developer](../../skills/uniubi-robot-developer/SKILL.md) | Unified entry point: choose a development path and coordinate cross-project work |
| [uniubi-robot-sdk](../../skills/uniubi-robot-sdk/SKILL.md) | C++ / Python SDK builds, applications, observations, control and media |
| [uniubi-robot-ros2](../../skills/uniubi-robot-ros2/SKILL.md) | ROS 2 nodes, launch configuration, messages, services and bridge integration |
| [uniubi-robot-rl](../../skills/uniubi-robot-rl/SKILL.md) | RL tasks, rewards, training diagnosis, export and replay in uniubi_rl_lab |

Install all four for cross-project work, or install a specialist independently. The entry point reads relevant specialist guidance when available; it does not require subagents or a particular model. Missing specialists do not prevent using available repository documentation.

Skills provide development instructions. They do not install the SDK, ROS 2, Isaac Lab, model weights, or device software.

## Install

Each skill is a portable folder following the [Agent Skills format](https://agentskills.io/specification). Keep its SKILL.md and references together. Other assistants may use different discovery directories; follow that assistant's installation instructions. These files do not require a private server or credentials.

For Codex, the current [official skill documentation](https://learn.chatgpt.com/docs/build-skills) lists `~/.agents/skills` for user-wide discovery and `.agents/skills` inside a project for repository-scoped discovery.

Use a checkout of [uniubi-docs](https://github.com/uniubi-ai/uniubi-docs) at a revision containing these skills. Run the following from its root on the machine/environment where your assistant reads skills. To install a subset, change `selected_skills`. For a project-only installation, set `skills_target` to the absolute path of that project's `.agents/skills`.

```bash
cd /path/to/uniubi-docs
git rev-parse HEAD
```

```bash
bash <<'BASH'
set -eu
skills_source="$PWD/skills"
skills_target="$HOME/.agents/skills"
selected_skills="uniubi-robot-developer uniubi-robot-sdk uniubi-robot-ros2 uniubi-robot-rl"

for skill in $selected_skills; do
  test -f "$skills_source/$skill/SKILL.md" || {
    echo "Missing skill: $skills_source/$skill" >&2
    exit 1
  }
  if [ -e "$skills_target/$skill" ] || [ -L "$skills_target/$skill" ]; then
    echo "Already exists; review before updating: $skills_target/$skill" >&2
    exit 1
  fi
done
mkdir -p "$skills_target"
for skill in $selected_skills; do
  cp -R "$skills_source/$skill" "$skills_target/$skill"
done
echo "Installed skills in $skills_target"
BASH
```

The commands refuse to overwrite an existing skill. For updates, compare the installed folders with the selected source revision, preserve local customizations, and deliberately replace the reviewed folders. Avoid installing duplicate copies with the same name in user and project locations.

Check that your assistant discovers the installed skill names. If Codex does not show a newly installed skill, restart it. Alternatively, ask the assistant to read a specific SKILL.md from this checkout; this permits explicit use without claiming automatic discovery.

## Start a task

Provide the relevant checkout paths and goal. Include known runtime/firmware versions or a training task/checkpoint when relevant; the assistant should inspect files for the remaining information.

Example prompts below use skill names in natural language. Use your assistant's skill picker or explicit invocation syntax when available.

**Application development**

> Use uniubi-robot-sdk. In my Python SDK checkout at /path/to/uniubi_robot_sdk_py, create a minimal read-only IMU example for an external Linux PC. Check the actual version and API first, and include subscription cleanup and a way to verify fresh data.

**ROS 2 integration**

> Use uniubi-robot-ros2. In /path/to/uniubi_ros2, add an application node that consumes IMU data. Inspect the existing bridge topic, message type, QoS and namespace before changing code. Do not start robot motion.

**RL development**

> Use uniubi-robot-rl. In /path/to/uniubi_rl_lab, add a reward term to my existing task. First check whether an equivalent term exists. Wire it into the current task and perform static checks; do not start training yet.

**Cross-project policy integration**

> Use uniubi-robot-developer. Review how my exported policy connects to the Low-level SDK. Compare the saved training config with the deployment adapter's observations, normalization, joint order, action scaling and control period. Fix confirmed adapter mismatches and validate offline; do not deploy to a robot.

**Training diagnosis**

> Use uniubi-robot-rl. Diagnose the failure in this run directory using its logs and saved configuration. Identify the active task and algorithm before proposing a fix. Do not restart the job.

## Expected results and boundaries

The assistant should identify relevant source files, make requested changes, run proportionate checks, and report what was observed and what remains unverified. A source edit, import, build, training run, simulation, successful RPC, and physical robot behavior are separate validation stages.

Writing an application does not itself authorize firmware changes, device deployment, robot movement, or a long training job. Follow the existing [High-level](high-level-control.md) and [Low-level](low-level-control.md) guides for hardware prerequisites and control handback. Provide explicit operational scope when requesting live work.

If the necessary checkout, dependency, compatible documentation, or hardware is unavailable, expect a precise limitation rather than an invented API or a claim of successful validation.

## Maintaining the skills

Keep routing and cross-project contracts in the entry point; keep domain procedures in their specialist. Link to current source/docs instead of duplicating full API manuals. Keep specialist folders independently usable after copying outside this repository.

When changing the skills, check formatting and references with `python3 scripts/check_docs.py` and validate each SKILL.md's frontmatter against the Agent Skills format. Try the prompts above in a disposable environment with the permitted scope: verify the chosen domain, source evidence, generated changes, and validation claims. In particular, check standalone specialist use, a missing specialist, and RL-to-SDK integration without authorizing hardware execution.

[Back to How-to Guides](README.md)
