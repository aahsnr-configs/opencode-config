[**PLAN 1**]

---

# OpenCode v2: Oh My OpenCode Slim vs. your agent workflow

## 1. The fundamental architectural difference

The two repositories implement different approaches to multi-agent coordination.

Oh My OpenCode Slim

Automated orchestration

A central Orchestrator constructs a task dependency graph, delegates to specialized agents, monitors their execution, reconciles results, and verifies the final outcome.

Your OpenCode configuration

Controlled delegation

Separate primary agents and specialized subagents operate through explicit commands, restricted delegation permissions, and user approval gates.

This distinction is confirmed by the actual implementation and agent definitions, rather than the projects' marketing descriptions.

Your repository already has planning, implementation, exploration, architectural advice, code review, and verification capabilities. What Slim adds is a dedicated orchestration runtime that coordinates these activities automatically.

Consequently, the important question is not which project has more agents. It is whether automatic scheduling and delegation offer enough benefit to justify the added complexity, permissions, and token consumption.

Sources: [Slim background orchestration](https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/background-orchestration.md?utm_source=chatgpt.com) · [Your work agent](https://github.com/aahsnr-configs/opencode-config/blob/main/agents/work.md?utm_source=chatgpt.com) · [Your coder agent](https://github.com/aahsnr-configs/opencode-config/blob/main/agents/coder.md?utm_source=chatgpt.com)

## 2. Feature-by-feature comparison

| Criterion                | Slim                                                            | Your workflow                                         | Advantage                             |
| ------------------------ | --------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------- |
| Planning                 | Dependency graph and specialist routing                         | Built-in Plan, `/plan-work`, Work agent               | Slim for complex tasks                |
| Delegation               | Automatic, parallel-first                                       | Explicit, allowlisted, approval-gated                 | Slim for throughput                   |
| Implementation           | Scoped Fixer/Designer specialists                               | Coder agent with testing guidance                     | Depends on task                       |
| Code exploration         | Explorer with AST/LSP tools                                     | Read-only Explore Scout                               | Slim for tooling; yours for isolation |
| Architecture review      | Oracle and optional Council                                     | Sol Advisor and Reviewer                              | Slim for multi-model review           |
| Verification             | Orchestrator-owned final checks and verification-planning skill | Acceptance tests, review, diff inspection             | Slim for coordination                 |
| User oversight           | Configurable permissions and approval behavior                  | Strong approval-by-default policy                     | Yours                                 |
| MCP control              | Built-in Context7 and GitHub code-search MCP integration        | Manual connections, explicit authorization            | Yours                                 |
| Domain research          | General-purpose architecture with extensibility                 | Dedicated math, physics, life sciences, deep research | Yours                                 |
| Configuration complexity | Substantial orchestration runtime                               | Simpler agent runtime, but broad specialist ecosystem | Yours for orchestration simplicity    |

These judgments concern architectural capabilities and configuration, not measured task success rates.

## 3. Where Slim is better

### Parallel execution and dependency management

Slim's strongest advantage is its scheduler-first approach.

Slim's orchestration pipeline

Orchestrator: analyze goal and dependencies

Explorer

Oracle

Other specialists

Reconcile findings and assign non-overlapping edits

Fixer: module A

Fixer: module B

Final-state verification and delivery

Conceptual workflow. Parallel execution depends on file ownership, dependencies, permissions, and available models.

The actual `src/agents/orchestrator.ts` prompt includes several useful rules:

- Assign non-overlapping write scopes and validation owners.
- Delegate independent work in parallel but respect dependencies.
- Reuse an existing specialist session rather than starting a fresh one unnecessarily.
- Reconcile writer outputs before running final validation.
- Avoid delegation for tiny changes or context-heavy documentation when the parent already has the relevant context.

These are sensible improvements over a workflow that simply invokes subagents one after another.

Source: [Orchestrator source](https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/src/agents/orchestrator.ts?utm_source=chatgpt.com)

### Verification planning

Slim's `verification-planning` skill is another genuine improvement. Instead of merely adding tests after implementation, it asks what evidence will establish correctness before the change begins.

That is especially useful for numerical code, where passing a unit test does not necessarily establish scientific correctness. Your existing numerical and physics verification skills provide domain-specific methods; Slim's verification planning could coordinate when and how to use them.

### Deepwork and recoverable plans

For multi-phase refactoring, Slim has a `deepwork` skill that maintains small state files, tracks decisions and next steps, and applies phase-based review gates.

Your workflow already defines acceptance criteria and review, but does not have an equivalent built-in orchestration mechanism that manages phase progression and resumed specialist execution.

This is a valuable feature for long sessions, provided the state remains readable and consistent.

Source: [Slim's Deepwork and verification-planning skills](https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/skills.md?utm_source=chatgpt.com)

## 4. Where your architecture is better

Your configuration has a particularly useful separation between planning, authorized implementation, and read-only evaluation.

For example, your `work` agent grants delegation only to named agents, with approval required. Your `reviewer` denies editing, execution, networking, and further delegation. Your `explore-scout` is restricted to read, glob, and grep.

This is more conservative than simply installing a general-purpose orchestrator and letting its default routing decisions govern everything.

Your additional scientific workflows also matter substantially. You have specialist skills and computational environments for numerical PDEs, mathematical research, physics simulation, molecular dynamics, and biological research. Slim's default specialists are largely software-engineering oriented.

Replacing your workflow with Slim's default agent set would therefore lose useful specialization unless you carefully reintroduced your existing agents, skills, and restrictions.

A second benefit is predictable model spending. Your configuration already assigns economical Luna models to discovery tasks, Terra to coding, and Sol to difficult advice. Slim supports a comparable model hierarchy, but automatic background delegation can produce additional model calls.

Slim may reduce wall-clock time for independent tasks. It does not inherently reduce the total token count.

Sources: [Reviewer permissions](https://github.com/aahsnr-configs/opencode-config/blob/main/agents/reviewer.md?utm_source=chatgpt.com) · [Your numerical research architecture](https://github.com/aahsnr-configs/opencode-config/blob/main/docs/MATH-RESEARCH.md?utm_source=chatgpt.com) · [Physics workflows](https://github.com/aahsnr-configs/opencode-config/blob/main/docs/PHYSICS-RESEARCH.md?utm_source=chatgpt.com)

## 5. The biggest reason not to switch immediately: OpenCode v2 reliability

&#x20;Active orchestration regression

I verified that Slim's latest GitHub release is v3.0.7, published November 4, 2026. As of November 5, there are unresolved reports that directly affect its orchestration layer.

[Issue #1822 — Background subagent deadlock](https://github.com/alvinunreal/oh-my-opencode-slim/issues/1822?utm_source=chatgpt.com)

Opened November 5, 2026 · Open

A resumed background child can remain incorrectly marked as running after completion, preventing another task from starting and potentially blocking the parent. The reporter reproduced the issue against v3.0.7 production modules using a mocked v2 host. This is a significant concern for long-running orchestration.

[Issue #1808 — Slow startup recovery](https://github.com/alvinunreal/oh-my-opencode-slim/issues/1808?utm_source=chatgpt.com)

Open

A reported test involving 500 retained background children produced approximately 12–16 seconds of startup recovery overhead. The issue describes service initialization failures in that scenario. This matters for persistent OpenCode/OpenChamber usage.

[Issue #1810 — Deepwork state and prompt degradation](https://github.com/alvinunreal/oh-my-opencode-slim/issues/1810?utm_source=chatgpt.com)

Open

A user reported increasingly compressed and difficult-to-read progress files and subagent instructions during long GPT-6.1 Sol Deepwork sessions. The report has no minimal reproduction, and another context-management plugin was active, so causation remains uncertain.

These are reported defects, not failures I independently reproduced. Nevertheless, the first report includes a detailed deterministic reproduction and concerns precisely the capability for which you would adopt Slim.

Slim also documents a compatibility distinction worth understanding: its implementation has compile-time coverage against OpenCode v2.2.0, while its documented live-host verification baseline is older. Source-contract compatibility does not prove every orchestration path works reliably on the latest runtime. [V2 compatibility documentation](https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/opencode-v2-compatibility.md?utm_source=chatgpt.com)

## 6. Potential conflicts with your existing setup

### Plan agent and Plannotator

Your current configuration declares `default_agent: "chat"` and configures Plannotator with `workflow: "plan-agent"`.

Slim has a separate primary `orchestrator` agent. It does not simply enhance your existing built-in `plan` agent. Furthermore, Slim's `setDefaultAgent` setting normally preserves an already configured, valid primary agent such as `chat`.

Therefore, installing Slim would not automatically make your existing planning workflow use its Orchestrator. Nor should you assume that the Plannotator Plan-agent workflow automatically handles plans created inside Slim's Orchestrator.

That integration would need testing.

### Superpowers and Deepwork

Your Superpowers plugin already introduces structured software-development practices. Slim's Deepwork, verification planning, and related workflows could overlap with those practices.

Using both without clear ownership risks duplicated planning, repeated reviews, and longer sessions. I would designate one system as the authority for phase planning, rather than invoking both automatically.

### Explicit MCP authorization

Your `AGENTS.md` explicitly prohibits automatic MCP activation and requires approval for each invocation.

Slim bundles integrations such as Context7 and `gh_grep`. Although its configuration supports disabling them through `disabled_mcps`, the default integration approach is less restrictive than your policy.

That is another reason to avoid installing its defaults without a compatibility audit.

## 7. What I would adopt from Slim

My preferred architecture would retain your agents and add a lightweight orchestration contract to your `work` agent.

Recommended hybrid workflow

Plan + Plannotator approval

Scope, acceptance criteria, dependency graph

Work agent — coordinator

Dispatch decisions, ownership, approval gates

Explore Scout

Sol Advisor

Domain skills

Coder — scoped implementation

Independent work only when safe and approved

Reviewer + final verification

Inspect integrated diff, tests and evidence

For your workflow, the highest-value adaptations are dependency-aware task scheduling, explicit file ownership, project-specific verification planning before implementation, and a durable but concise progress record for long-running work.

These can largely be implemented through revisions to `agents/work.md`, `commands/plan-work.md`, and your existing workflow skills without adopting the entire Slim runtime.

OpenCode v2 already supports foreground and background subagent sessions, so a useful portion of Slim's coordination model can be expressed using native capabilities.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode+1

One distinction matters: a prompt-only workflow can direct a model to coordinate tasks, but does not reproduce Slim's managed job board, persistence, recovery, or concurrency controls.

## 8. Would I install Slim alongside your configuration?

I would consider an isolated trial, but not replace your workflow with it immediately.

Slim does offer a useful compromise through `backgroundJobs.mode: "native"`. This retains native OpenCode delegation and lightweight status/cancellation controls while avoiding Slim's managed background-job board.

A minimal experimental configuration could look like this:

```
{
  "setDefaultAgent": false,
  "backgroundJobs": {
    "mode": "native"
  },
  "disabled_mcps": [
    "context7",
    "gh_grep"
  ],
  "autoUpdate": false,
  "fallback": {
    "enabled": false
  },
  "marketplace": {
    "enabled": false
  }
}
```

These settings are documented by Slim; this is not a tested compatibility configuration for your complete setup. Agent permissions, model selection, bundled hooks, and interaction with your existing plugins would still need auditing.

The tradeoff is that native mode avoids much of the managed scheduler infrastructure—including the area implicated by issue #1822—but consequently does not provide the entire managed orchestration feature set.

Source: [Slim configuration reference](https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/configuration.md?utm_source=chatgpt.com)

## 9. Final recommendation

OVERALL DECISION

Keep your workflow

## Keep your existing agent ecosystem and selectively strengthen its orchestration.

Slim provides a more sophisticated automatic scheduler, but your system has stronger default oversight and significantly better specialization for your scientific and research workloads. The currently reported v2 orchestration regressions make a wholesale migration difficult to justify.

| Your primary objective                       | Preferred approach                                |
| -------------------------------------------- | ------------------------------------------------- |
| Maximum parallel coding throughput           | Slim, once relevant regressions are resolved      |
| Lower and more predictable token consumption | Your existing workflow, with selective delegation |
| Reliable approval-gated operation            | Your existing workflow                            |
| Complex scientific and numerical research    | Your existing specialized agents and skills       |
| Long multi-stage software development        | Hybrid workflow using Slim's planning principles  |
| Experimental multi-agent automation          | Isolated Slim trial using native mode             |

The cost and throughput comparisons here are architectural expectations, not benchmark results. I found no controlled head-to-head measurements establishing that either repository consistently uses fewer tokens or completes tasks faster.

My conclusion: Slim's orchestration design is better than your current Work agent's relatively simple delegation logic. But Slim as an entire plugin is not currently a better replacement for your OpenCode v2 configuration.

I would improve your existing architecture first, preserving your Plan/Plannotator approval workflow, specialist models, research integrations, and manual MCP policy. That offers much of the coordination benefit without introducing a second, substantially more complex orchestration system.

---

---

---

[**PLAN 2**]

---

# TODO OpenCode V2 experimental features and Claude Smart configuration audit

Research date: November 5, 2026 · Sources: OpenCode V2 documentation, Context7, Exa, upstream GitHub issues, release notes, and Claude Smart documentation.

## Executive findings

Native TODO tracking is worth enabling, but there are genuine limitations. It is now an official experimental feature rather than something that requires an unmaintained plugin. However, recent bug reports document problems with automatic task-list creation, configuration inheritance, and UI visibility.

My previous Claude Smart Option A was not correct for OpenCode V2. It used the older `provider.models.options` configuration structure. OpenCode V2 documentation instead specifies `providers.models.settings`, with `providers` plural.

This distinction matters because an accepted-looking configuration can fail to apply your intended reasoning settings. The corrected structure is:

```
{
  "providers": {
    "openai": {
      "models": {
        "gpt-6-luna": {
          "settings": {
            "reasoningEffort": "low"
          }
        }
      }
    }
  }
}
```

This example is appropriate only if your selected model actually belongs to the `openai` provider. For an OpenCode Console model, the provider key would instead be `opencode`.

The syntax is verified against OpenCode V2's [official Models documentation](https://opencode.ai/v2/docs/models/?utm_source=chatgpt.com), but whether it controls Claude Smart's isolated learning requests requires a separate check.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode+1

## 2. Common complaints about experimental TODOs

The reports below concern OpenCode V2, except where explicitly identified as historical context. These are documented complaints, not statistical measurements of how frequently users encounter them.

1\. Agents do not create TODO lists automatically

A report filed October 26 says enabling `experimental.todo` makes the tool available, but agents often ignore it unless explicitly instructed to create a checklist. The report attributes this to missing system-prompt guidance after the V2 restoration.

[Issue #59259](https://github.com/anomalyco/opencode/issues/59259?utm_source=chatgpt.com) · Affects usefulness, not necessarily stability

Moderate

2\. Global TODO settings can disappear inside projects

On October 30, an issue documented and reproduced a configuration-merging bug in V2.2.0–V2.2.1. When a project has its own `experimental` object, it can replace the whole global experimental object, even when the project changes an unrelated setting.

This can silently disable your global `experimental.todo: true`.

[Issue #60410](https://github.com/anomalyco/opencode/issues/60410?utm_source=chatgpt.com) · Reproduced upstream

Moderate

3\. Sidebar state has visibility limitations

The implementation reads the latest relevant TODO state from loaded session history. Very long sessions may not display older task updates until more history is loaded. After compaction, finished checklists are not necessarily restored. Subagent task lists are not automatically aggregated into the parent session.

[PR #56948 implementation notes](https://github.com/anomalyco/opencode/pull/56948?utm_source=chatgpt.com)

Low–moderate

4\. Some clients received TODO rendering later than others

The TUI gained experimental TODO support in V2.1.0 on October 20. Desktop support followed in V2.2.0 on October 27. Browser-based UI parity was separately requested, so it is not safe to assume all clients behave identically.

[Official changelog](https://opencode.ai/changelog?utm_source=chatgpt.com) · [V2 TODO discussion](https://github.com/anomalyco/opencode/issues/42421?utm_source=chatgpt.com)

Client-dependent

There is also a performance trade-off. An OpenCode contributor explained that the original TODO tools were removed partly because they slowed agents without a clear corresponding performance improvement in their observations. Reintroducing a checklist means extra tool calls and model context, although I found no reliable V2 benchmark quantifying the overhead.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

### How I would mitigate these issues

For a relatively dependable workflow, use the native feature with a short instruction in your existing global `AGENTS.md`:

```
## Task tracking

For implementation tasks involving three or more distinct steps:

1. Create a concise task list using the native `todowrite` tool.
2. Keep one task marked `in_progress` at a time.
3. Mark tasks completed immediately after verifying them.
4. Update the list when scope changes.
5. Do not mark tests or verification complete unless they actually pass.
6. Use task tracking only when the native tool is available.
```

This addresses the missing-behavior-guidance problem without adding another plugin.

I would also keep the experimental settings in your global OpenCode config and check whether individual projects have overriding `experimental` blocks. That matters more than adding complicated task-management extensions.

Assessment: The known issues are sufficient to avoid relying on TODOs as the sole authoritative project record, but not sufficient to discourage trying the feature. For the visual implementation checklist you want, I would enable it.

## 3. Other experimental features worth considering

The official [OpenCode V2 Experimental configuration](https://opencode.ai/v2/docs/config/?utm_source=chatgpt.com#experimental) documents five main options. Newer release notes also mention additional experimental capabilities.

| Feature                 | Benefits and risks                                                                                           | Recommendation   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------- |
| `todo`                  | Native checklist. Possible stale state and missed updates.                                                   | Enable           |
| `subagent_depth`        | Lets subagents delegate to subagents. More complex orchestration and higher potential token consumption.     | Keep default `1` |
| `background_compaction` | Prepares summaries before the context limit. Can spend tokens on summaries never used.                       | Leave disabled   |
| `image_generate`        | Configures a preferred image-generation model. Adds model and provider dependencies.                         | Only if needed   |
| `location_idle_timeout` | Controls how long inactive project services remain loaded. Longer periods retain resources.                  | Keep default     |
| `artifacts`             | Lets agents publish interactive or static artifacts. New in V2.2.4.                                          | Wait             |
| `schedules`             | Enables scheduled prompts and related tools. Newer opt-in capability, with recurring execution implications. | Wait             |

The first five are documented in the V2 configuration guide. `artifacts` and `schedules` are also described in the release history, but their recent introduction and limited operating history make them less attractive as global defaults.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode+1

### Why I would avoid nested subagents for now

The `subagent_depth` setting is especially relevant to your Superpowers and multi-agent workflows. It allows a subagent to launch another subagent, rather than simply delegating from the primary session.

However, an October 23 V2 Desktop report documents that the running-subagents indicator does not properly show deeper descendants when `subagent_depth` exceeds 1. The underlying sessions still exist, but their activity becomes harder to monitor.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

Since you have `subagent` permissions configured to ask for approval, I would favor simpler delegation until nested permission handling and visibility are verified in your particular version.

### Why I would avoid background compaction

Your current configuration already enables automatic compaction with an 8,000-token recent-history allowance and a 15% buffer.

Background compaction is different: it may begin generating a summary before the summary is required, reducing interruption latency but potentially incurring unnecessary model usage. The official October 23 release notes explicitly acknowledge that unused summaries still consume tokens.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

For your token-conscious workflow, the default `false` is the better choice.

### The one additional experimental setting I would consider

If you frequently switch between several OpenCode projects and find that their MCP servers repeatedly reconnect after inactivity, this option may be useful:

```
"experimental": {
  "todo": true,
  "location_idle_timeout": "2 hours"
}
```

The default idle timeout is 60 minutes. A two-hour value is a reasonable trial, but it retains idle project services for longer and is not an improvement if reconnections are already fast.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode

I would not add it preemptively. The two-hour value is an operational preference, not a documented reliability enhancement.

## 4. Claude Smart: a more reliable low-reasoning configuration

I inspected Claude Smart's current implementation, not just its README.

The important files are:

- [OpenCode learning bridge](https://github.com/ReflexioAI/claude-smart/blob/main/plugin/scripts/opencode-claude-compat.js?utm_source=chatgpt.com)
- [Installer and model validation](https://github.com/ReflexioAI/claude-smart/blob/main/bin/install-guide.js?utm_source=chatgpt.com)
- [Environment-file loader](https://github.com/ReflexioAI/claude-smart/blob/main/plugin/scripts/_lib.sh?utm_source=chatgpt.com)

### What the source actually does

Claude Smart launches an isolated OpenCode process for learning. Its bridge constructs an `opencode run` invocation, selects the learning model, and optionally supplies a model variant.

I verified the following behavior:

| Mechanism                               | Source-code finding                                        |
| --------------------------------------- | ---------------------------------------------------------- |
| `CLAUDE_SMART_LEARNING_MODEL`           | Used to select the learning model                          |
| `CLAUDE_SMART_OPENCODE_MODEL`           | Supported fallback if the learning-model setting is absent |
| `CLAUDE_SMART_OPENCODE_VARIANT`         | Passed as `--variant` to OpenCode                          |
| `provider/model#low`                    | Accepted by OpenCode V2 model selection                    |
| `#low` in Claude Smart setup            | Rejected by the setup wizard's model-ID validation         |
| Variant variable in Claude Smart `.env` | Not explicitly imported by its shell environment loader    |

The last two points are why I would not recommend simply adding `#low` to the model name through Claude Smart's setup wizard or putting `CLAUDE_SMART_OPENCODE_VARIANT=low` into its `.env` file.

### Option A — Corrected global model settings

This is the corrected version of my earlier Option A:

```
diff --git a/opencode.jsonc b/opencode.jsonc
--- a/opencode.jsonc
+++ b/opencode.jsonc
@@
   "snapshots": true,
+  "providers": {
+    "openai": {
+      "models": {
+        "gpt-6-luna": {
+          "settings": {
+            "reasoningEffort": "low",
+          },
+        },
+      },
+    },
+  },
```

This uses official V2 syntax and is straightforward to maintain.

But it changes the model's default reasoning effort for every OpenCode use of `openai/gpt-6-luna`, not just Claude Smart. An explicitly selected model variant may override the model-level settings.

Verdict: Correct for V2, subject to provider verification, but not completely isolated or bullet-proof.

### Option B — Dedicated Claude Smart model alias

This is my preferred approach for your setup.

OpenCode V2 lets you define a separate catalog name using `modelID`, while keeping the underlying API model unchanged. Its official documentation explicitly supports model-specific settings on aliases.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode

For example, create a dedicated low-effort alias:

```
diff --git a/opencode.jsonc b/opencode.jsonc
--- a/opencode.jsonc
+++ b/opencode.jsonc
@@
   "snapshots": true,
+  "experimental": {
+    "todo": true,
+  },
+  "providers": {
+    "openai": {
+      "models": {
+        "gpt-6-luna-claude-smart": {
+          "modelID": "gpt-6-luna",
+          "settings": {
+            "reasoningEffort": "low",
+          },
+          "capabilities": {
+            "tools": true,
+            "input": ["text", "image"],
+            "output": ["text"],
+            "reasoning": {
+              "supported": true,
+              "effort": ["low"],
+            },
+          },
+          "limit": {
+            "context": 1050000,
+            "output": 128000,
+          },
+        },
+      },
+    },
+  },
```

The context and output limits reflect the published GPT-6 Luna model specifications.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://models.opencode.ai&sz=32)

Models.dev

The alias has these properties:

| Property                             | Value                                                                  |
| ------------------------------------ | ---------------------------------------------------------------------- |
| Alias                                | `gpt-6-luna-claude-smart`                                              |
| Actual model                         | `gpt-6-luna`                                                           |
| Default reasoning effort             | `low`                                                                  |
| Dedicated API key required           | No additional key beyond the selected provider's normal authentication |
| Changes ordinary GPT-6 Luna defaults | No                                                                     |

This assumes the provider ID is `openai`. If your installation exposes Luna through OpenCode Console, use `opencode` as the provider key instead. Do not define both without confirming which one Claude Smart actually uses.

Once the alias is available, configure Claude Smart:

```
npx claude-smart setup
```

Choose your existing local OpenCode learning provider, select a custom model ID, and enter:

```
openai/gpt-6-luna-claude-smart
```

This model identifier passes Claude Smart's documented installer structure and its source-code validation, unlike a model identifier containing `#low`.

The key advantage is that Claude Smart has its own model configuration without modifying your ordinary GPT-6 Luna defaults.

### Is this bullet-proof?

No integration can be considered bullet-proof without executing it against the installed version. The alias approach is nevertheless stronger than the earlier proposal because it avoids undocumented environment-variable loading and uses the native V2 model configuration interface.

There are three remaining things to verify: model availability under the provider you've authenticated, resolution of the custom alias in Claude Smart's isolated subprocess, and confirmation that the provider receives the intended reasoning setting.

## 5. Verification procedure

Run these checks in order.

Check the OpenCode version and model inventory

```
opencode --version
opencode models | grep -i 'gpt-6-luna'
```

Confirm the provider prefix used by your account.

Test the dedicated model alias

After adding the alias to your global configuration, run:

```
opencode run \
  --model openai/gpt-6-luna-claude-smart \
  "Reply with OK"
```

This verifies that the alias resolves and generates a response. It does not, by itself, prove the exact reasoning effort transmitted to the provider.

Check Claude Smart's saved learning model

```
grep -E '^CLAUDE_SMART_(LEARNING_PROVIDER|LEARNING_MODEL)=' \
  ~/.claude-smart/.env
```

Expected learning-model assignment:

```
CLAUDE_SMART_LEARNING_MODEL=openai/gpt-6-luna-claude-smart
```

If the provider prefix differs, substitute the one verified in the previous checks.

Check installation health

```
npx claude-smart status
```

Then restart OpenCode and test a small task that explicitly requests native TODO tracking. Check that the checklist appears and updates after each step.

For definitive reasoning-effort verification, inspect an actual provider request or trustworthy provider-side diagnostic showing `low`. A successful test response and the stored config are necessary checks, but they are not conclusive evidence of the transmitted request settings.

## 6. Final recommendations

| Decision                             | Recommendation                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------ |
| Native experimental TODOs            | Enable                                                                               |
| Separate TODO plugin                 | Do not install                                                                       |
| TODO behavior instructions           | Add to `AGENTS.md`                                                                   |
| Nested subagent depth                | Keep default                                                                         |
| Background compaction                | Keep disabled                                                                        |
| Experimental image generation        | Use only when needed; newer V2 releases can expose it automatically                  |
| Experimental artifacts and schedules | Defer                                                                                |
| Claude Smart low reasoning           | Use a dedicated V2 model alias                                                       |
| Original Option A                    | Replace with V2 `providers.models.settings` syntax if you choose the global approach |
| Supermemory                          | Keep removed                                                                         |
| Plannotator                          | Retain the OpenCode V2-compatible plugin                                             |

My preferred final configuration is native TODO tracking plus a dedicated GPT-6 Luna low-reasoning alias for Claude Smart. That achieves the screenshot-style checklist without additional task-management dependencies, while avoiding unintended changes to the reasoning effort of other OpenCode agents.

The remaining risks are primarily the experimental TODO implementation and version-specific behavior in Claude Smart's background subprocess. Both can be tested independently, and neither requires replacing your existing Superpowers, Plannotator, RTK, or custom Caveman setup.

No local configuration or repository files were modified during this audit.

---

---

---

[**PLAN 3**]

---

# OpenCode v2 plugin audit — November 5, 2026

The first important finding is that not every plugin listed in OpenDock is actually compatible with OpenCode v2, even when it appears in a search for OpenCode plugins.

Two distinctions matter for your configuration:

- `opencode-acp` is a v1-only plugin. Its maintainer explicitly states that it does not load on OpenCode 2.x. It recommends `billion-context` for v2 instead. [Source](https://www.opendock.net/plugins/opencode-acp/?utm_source=chatgpt.com)
- `opencode-skills-collection` adds skills, not merely updates your existing skills. It ships more than 2,400 skills, organizes them into a separate library, and makes them available through approximately 100 category-pointer skills. It does not function as a general updater for your hand-written skills. [Source](https://github.com/FrancoStino/opencode-skills-collection?utm_source=chatgpt.com)

Your existing repository already contains extensive research-oriented skills, custom agents, research commands, and a compaction configuration. Consequently, the decision should be based on functionality your setup lacks, rather than how many plugins or skills can be installed.

## 1. OpenWork plugin added to your GitHub configuration

&#x20;Committed and verified

Branch: `main`

Repository: [aahsnr-configs/opencode-config](https://github.com/aahsnr-configs/opencode-config?utm_source=chatgpt.com)

I updated `opencode.jsonc` with the published `opencode-openwork@0.1.0` package, preserving your existing plugin entries and configuration.

```
--- a/opencode.jsonc
+++ b/opencode.jsonc
@@ -31,6 +31,7 @@
   "plugins": [
     "superpowers@git+https://github.com/obra/superpowers.git",
     "opencode-rtk-plugin",
+    "opencode-openwork@0.1.0",
     "opencode-todo",
     "/var/home/ahsan/.config/opencode/plugins/caveman",

```

[View the exact GitHub commit](https://github.com/aahsnr-configs/opencode-config/commit/118ba618d3a17938051ce519fffcb4e2255579d9?utm_source=chatgpt.com)

I independently fetched the updated file, confirmed the plugin appears exactly once, and checked that the configuration remains parseable as JSONC. No other configuration values were changed.

### What OpenWork actually adds

It connects a local OpenCode v2 installation to OpenWork Cloud, providing organization-managed AI models and MCP connections. It does not automatically give you the OpenWork desktop interface.

The package was tested upstream against OpenCode 2.0.26; I have not run it inside your installed OpenCode executable.

To activate it, after pulling the updated configuration, run:

```
opencode auth login openwork
```

Or use `opencode2` if that is your v2 executable. You need an OpenWork account and organization membership with appropriate access. The plugin alone does not create or provision them.

For verification:

```
opencode auth list
opencode models | grep ipr_
opencode mcp list
```

The package can provide `openwork-cloud` and organization-assigned connections. It coexists with your existing local skills and MCP configuration.

Official instructions: [OpenWork for OpenCode 2](https://openworklabs.com/docs/model-context-protocol/opencode-plugin?utm_source=chatgpt.com).

## 2. Dynamic Context Pruning (DCP)

[@tarquinen/opencode-dcp](https://www.opendock.net/plugins/tarquinen--opencode-dcp/?utm_source=chatgpt.com) · v3.2.0 · OpenCode v2 compatible

Verdict: Worth testing, but not necessary by default.

DCP offers several capabilities beyond your existing compaction settings.

| Capability                          | Your configuration                 | DCP             |
| ----------------------------------- | ---------------------------------- | --------------- |
| Automatic compaction                | Enabled                            | Complementary   |
| Model-initiated compression         | Not provided by the settings alone | Yes             |
| Selective message-range compression | Not configured                     | Yes             |
| Repeated tool-output deduplication  | Not configured                     | Yes             |
| Old failed-tool input pruning       | Not configured                     | Yes             |
| Context-reduction statistics        | Limited                            | Dedicated panel |

DCP provides a `compress` tool, `/dcp` control panel, and `/dcp-compress` command. It can summarize selected portions of a conversation rather than compacting the entire session.

Your existing Compactor agent is different: it primarily helps with structured summaries and workflow handoffs. DCP operates at the context-management layer.

### The important trade-off

Context pruning changes the prompt content sent to the model. Consequently, it may invalidate cached prompt prefixes.

With GPT-6 and subscription-based usage, fewer input tokens do not necessarily translate into proportionally lower usage limits or costs. Reducing context can also discard details important to complex research work.

The maintainer additionally reports that newer development has shifted toward Sleev, although DCP remains available.

Recommendation: Keep your existing compaction system and consider DCP as a controlled experiment on lengthy coding sessions. Do not install both DCP and another automatic context-pruning plugin without testing their interactions.

## 3. What is `opencode-acp`?

[opencode-acp](https://www.opendock.net/plugins/opencode-acp/?utm_source=chatgpt.com) · Active Context Pruning

ACP is a more elaborate model-controlled context-management system.

Its architecture uses three levels of progressively compressed memory:

T1 — Capture

Compress raw conversation into detailed summaries

T2 — Distill

Reduce previous summaries to decisions and outcomes

T3 — Condense

Preserve the most important long-term facts

It also implements decompression and context search so the model can recover previously compressed information.

However, `opencode-acp` does not support OpenCode v2. Its upstream documentation explicitly redirects v2 users to its successor, `billion-context`.

The author presents substantial long-session performance results, but those are project-reported benchmarks rather than a demonstration that the system will improve your particular GPT-6 workflow.

My recommendation is to avoid `opencode-acp` entirely in your v2 setup. Evaluate `billion-context` separately only if your existing compaction proves insufficient.

## 4. Would OpenCode Skills Collection improve your existing skills?

[FrancoStino/opencode-skills-collection](https://github.com/FrancoStino/opencode-skills-collection?utm_source=chatgpt.com) · v4.1.35

I counted 82 top-level `SKILL.md` definitions in your current GitHub repository.

These already cover substantial areas of your workflow, including numerical PDEs, numerical linear algebra, CUDA, molecular dynamics, mathematical optimization, biophysics, life-science databases, academic research, and deep research.

The collection's strongest advantage is breadth rather than specialization.

# 82

Your current skills

Specialized and integrated with your agents and research tools

# 2,400+

Collection's bundled skills

Broad library exposed through roughly 100 category pointers

### Does it add skills or update them?

It does both, but importantly, it updates its own bundled collection, not your existing custom skills.

At startup, the plugin populates two locations:

```
~/.config/opencode/
├── skills/
│   ├── backend-dev-category-pointer/
│   ├── ...other category pointers
│
└── skill-libraries/
    ├── backend-dev/
    │   ├── laravel-expert/
    │   └── ...
    └── ...
```

Its bundled skill catalog is synchronized through the project's release process. When the installed collection changes, the plugin can refresh its managed vault and pointer files.

It does not generally modify your existing `math-research/SKILL.md`, `molecular-dynamics/SKILL.md`, or other individually maintained skills.

### Would I install it?

Not in your default configuration.

Its approximately 100 pointers increase the advertised skill catalog, and selecting a skill requires an additional discovery step. There is also a security consideration: the collection supports risk-based filtering, but its default filtering is opt-in. Its CI scanning is not a comprehensive trust guarantee for thousands of third-party instructions.

For your existing highly specialized environment, I would prefer manually selecting useful skills from the collection and incorporating them into your current repository after reviewing their instructions, dependencies, provenance, and duplication.

Verdict: More skills, but not necessarily a better skills system. Your present curated skills are likely a stronger default for research and numerical analysis.

## 5. Which `/goal` implementation is best?

The critical development is that OpenCode v2.2.1 introduced native `/goal` on October 29, 2026.

The official release confirms that it continues working until a reviewer confirms the objective has been met. It supports pause, resume, and clear controls. [Official v2.2.1 release notes](https://github.com/anomalyco/opencode/releases/tag/v2.2.1?utm_source=chatgpt.com).

The other two implementations have useful features, but the native feature changes the recommendation substantially.

| Capability                    | Native `/goal`                    | `opencode-goal-plugin`                       | `@prevalentware` goal                  |
| ----------------------------- | --------------------------------- | -------------------------------------------- | -------------------------------------- |
| OpenCode v2 support           | Yes, 2.2.1+                       | Yes                                          | Yes                                    |
| Automatic continuation        | Yes                               | Yes                                          | Yes                                    |
| Completion review             | Native reviewer                   | Evidence gate; optional independent verifier | Evidence-required completion           |
| Configurable resource budgets | Not documented to the same extent | Yes, including cost                          | Yes, including token and duration      |
| Persistent goal state         | Native session integration        | Yes                                          | Yes                                    |
| Multiple ordered goals        | Not documented                    | Yes                                          | Persistent plans with phases and tasks |
| Custom goal management tools  | Native controls                   | Yes                                          | Yes                                    |
| Additional plugin required    | No                                | Yes                                          | Yes                                    |

### A. `opencode-goal-plugin` by william-ricchiuti

[GitHub repository](https://github.com/william-ricchiuti/OpenCode-goal-plugin?utm_source=chatgpt.com) · v0.11.4

This is the more interesting extension if your priority is strict verification and controlled autonomous execution.

It provides persistent goal state, independent completion verification when explicitly enabled, multiple goals, ordered goal sequences, and limits on duration, turns, tokens, and cost.

Its independent verifier can operate with restricted read-only capabilities, providing a more explicitly constrained verification process than merely asking the primary agent to declare itself finished.

However, the maintainer has switched to maintenance-only development and recommends native `/goal` for ordinary use. The plugin also relies on experimental hooks, making compatibility with future OpenCode releases something to test rather than assume.

Verdict: Potentially better for highly controlled autonomous workflows, not better for routine goal execution.

### B. `@prevalentware/opencode-goal-plugin`

[GitHub repository](https://github.com/prevalentWare/opencode-goal-plugin?utm_source=chatgpt.com) · v0.1.95

This implementation emphasizes goal lifecycle management.

Its distinguishing features include durable plans with phases and tasks, checkpoints, goal history, TUI indicators, budget management, and explicit states for goals blocked on user input.

It also has safeguards against accidentally continuing execution while an agent is in Plan mode and mechanisms for retaining goal context through compaction.

That could be useful when conducting lengthy, multi-stage research or software implementation.

Its own maintainer nevertheless recommends OpenCode's native implementation for most users on v2.2.1 and later.

Verdict: Consider it only if persistent phase/task tracking, budget checkpoints, or its more extensive goal-management API is essential.

### My choice for your setup

Keep native `/goal`.

Your existing `plan`, `chat`, `work`, `coder`, `reviewer`, and research-specific workflows already provide considerable task orchestration.

Adding an alternative goal plugin would introduce another layer of session state, continuation behavior, and plugin compatibility requirements.

For a task such as implementing a numerical PDE solver, you can use native `/goal` to require passing tests and validated numerical results before completion. Your existing reviewer and numerical-verification skills remain useful inside that workflow.

Neither third-party goal plugin is sufficiently better across the board to justify making it part of your default configuration. I would also avoid installing both, since their commands and continuation hooks can conflict.

## 6. Final recommendations

| Plugin                                | Recommendation                     |
| ------------------------------------- | ---------------------------------- |
| `@tarquinen/opencode-dcp`             | Optional experiment                |
| `opencode-acp`                        | Do not install — v1 only           |
| `opencode-skills-collection`          | Selective skill extraction instead |
| `opencode-goal-plugin`                | Use native `/goal` instead         |
| `@prevalentware/opencode-goal-plugin` | Use native `/goal` instead         |
| `opencode-openwork@0.1.0`             | Added and committed                |

The important architectural principle for your repository is to maintain one authoritative system for each major responsibility: your curated skills for domain knowledge, your custom agents for orchestration, OpenCode's native goal and compaction systems for session management, and carefully chosen external plugins for genuinely missing capabilities.

Context7's OpenCode v2.1.2 documentation confirms the plural `plugins` configuration format and support for versioned npm packages. The official v2 documentation also confirms that the plugin API is still beta, so source compatibility alone does not guarantee flawless runtime integration.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode

Implementation status: The requested OpenWork addition is committed to `main`, its configuration has been checked, and the other plugins were intentionally left uninstalled. Runtime loading and OpenWork authentication still need to be verified on your Fedora machine.

---

---

---

# PLAN 4

---

OpenCode v2 already supports exactly what you're describing. The feature is called prompt steering: you can send additional context, corrections, or instructions while the agent is still working, without cancelling its current task.

According to the [official OpenCode v2 TUI documentation](https://opencode.ai/v2/docs/cli/tui/?utm_source=chatgpt.com):

| Action                   | Shortcut               | Behavior                                                  |
| ------------------------ | ---------------------- | --------------------------------------------------------- |
| Steer a running agent    | `Enter`                | Delivers your new instructions before the next model step |
| Queue a prompt           | `Ctrl+X`, then `Enter` | Runs the new prompt after the current work finishes       |
| Write a multiline prompt | `Shift+Enter`          | Inserts a newline without submitting                      |
| Interrupt execution      | `Esc`                  | Stops the current execution                               |

For example, while your `coder` agent is implementing something, you can type:

> Update the implementation requirements: use Ruff instead of Flake8, preserve the existing tests, and continue from the current progress without restarting.

Then press `Enter`. OpenCode delivers that instruction at the next safe execution boundary. Tools already running are allowed to finish.

This is native OpenCode v2 functionality, so you don't need a plugin for ordinary mid-workflow instruction updates.

However, I found several relevant plugins on OpenDock that extend this functionality.

## Best matches on OpenDock

[Opencode: 다양한 LLM을 사용할 수 있는, 터미널 기반의 오픈소스 AI 코딩 에이전트 - 읽을거리&정보공유 - PyTorchKR](https://images.openai.com/static-rsc-4/GFoPvTkJab6R4bLHsaWLzkxIfYFAB_ecAMPVRHcwlVGbpyVUrw5kcgrYVQF5MLdo4c1xxcZswWn3X_7It7zVgEeVqTFwfwrjCA53v0viejzQkkp9-SuOVkvwZLIzMEYoEsYpuUgMDkfzd-SmxOHqKLF8zZIcAQUFpiM9K3XktSw?purpose=inline)

1\. [opencode-queue](https://www.opendock.net/plugins/opencode-queue/?utm_source=chatgpt.com)

Best plugin match

v2.1.0 · OpenCode v2.0.27+ · MIT

Provides persistent prompt queues, immediate steering, queue editing, and model/variant selection. Use `/queue:now` for mid-execution instructions or `/queue` to schedule the next task.

[Medium](https://images.openai.com/static-rsc-4/s24S0jpdPX8q3NVuq80Ljd2fPEzvVBr64SwH-BpkJLGw5CFv928yYMYE6ITCvVoFtAcw4Pl3afF5IY59OWX5RMEaatBv7HfJQoeUMJF1ANm40YkTAeVlMyhSnNM6F34h5shoGorl-YjHP-KHaw93CW6w1gwDYvouVC1VrpUlvWY?purpose=inline)

2\. [opencode-subagent-intervene](https://www.opendock.net/plugins/opencode-subagent-intervene/?utm_source=chatgpt.com)

v1.0.1 · OpenCode v2.2.0+ · MIT

Lets your orchestrator send new instructions to an already-running subagent using `subagent_send`. It can also inspect or stop individual subagents without stopping the parent workflow.

[GitHub - frap129/opencode-rules: An opencode plugin to dynamically inject rules into context, like cursor · GitHub](https://images.openai.com/static-rsc-4/xP5hp4qFIvdiQT2-r8mOuwGF1ibsGkD8GZzZtoMoAXGwulNscr0apvYZRoSqmPXJ11pqc7is7IOeiI6PHWGKtcNKVFyAVrOAQLiFg9yCwAyvX5mG_s2xVVCIQLCExezrSwpVbowgEP30d1866kNG1G2vQRDZWEoQwGlzreK4zLk?purpose=inline)

3\. [opencode-smart-subagents](https://www.opendock.net/plugins/opencode-smart-subagents/?utm_source=chatgpt.com)

v0.3.0 · OpenCode v2 · MIT

Supports two-way messages between parent and child agents, mid-run steering, and subagent questions. More extensive, but it replaces OpenCode's native subagent tool and increases integration complexity.

[vogel (@ryanvogel) on X](https://images.openai.com/static-rsc-4/1OvdtNlEWVLlNbAOG1CR2e-YiVJEPnZ_TSUiuMJN4ar3-O3YNgUVMwPxhN-yDi37PzDRhrjMtnE0n3B90LNysb_f3UHg_8tt8jPinyeQTpl71_3ALTvzVYFo9J8_eqvYnroT0wY7Dnlom1KZYkBxtKu1Q1eVj6lOqQFmoMiq0Mg?purpose=inline)

4\. [@rphang/opencode-workflows](https://www.opendock.net/plugins/rphang--opencode-workflows/?utm_source=chatgpt.com)

v0.2.0 · OpenCode v2.0.15 specifically

Provides a workflow orchestration engine with live steering of individual agents through `/workflows msg`. Its documented compatibility is pinned to v2.0.15, so I would not recommend it for your newer v2 configuration without additional testing.

## Using `opencode-queue`

These are verified commands from its current OpenDock documentation.

```
/queue:now Stop using the deprecated API. Use the
new API and continue the implementation.

/queue After implementation, run the tests.

/queue:edit last Run the tests and fix failures.

/queue:list
```

`/queue:now` is the important one: it delivers an instruction at the next model checkpoint. The plugin can also switch the model or reasoning variant for subsequent execution, which native text steering alone does not offer in the same command.

To add it to your existing `opencode.jsonc`:

```
"plugins": [
  "opencode-queue@2.1.0"
]
```

This is the entry to merge into your current array, not a replacement for your other plugins. I have not modified your repository in this turn.

## Which is most useful for your agents?

Your OpenCode setup uses custom orchestrating agents, research agents, and coding/reviewer workflows. There are two distinct cases.

When you want to update your main agent's instructions, native steering is sufficient. Add `opencode-queue` only when you want persistent, editable, ordered prompts or controlled changes to the agent/model between tasks.

When you want to modify a subagent's instructions while it is working, `opencode-subagent-intervene` provides more meaningful additional functionality. A message sent to the parent does not automatically guarantee that the child receives it; the parent must forward the instruction. This plugin gives the parent explicit tools for that process.

My recommendation is to use native steering immediately and prioritize `opencode-subagent-intervene` if you need control over your delegated agents. I would avoid installing all four.

---

---

---

# PLAN 5

---

## APPEARANCE

Yes. OpenDock has several OpenCode v2 plugins that change the terminal interface's appearance, layout, and visual feedback, including one that specifically skins the entire TUI.

The important distinction is that OpenCode v2 supports two kinds of visual customization: skins and themes, which change how existing elements look, and interface extensions, which add sidebars, status bars, and interactive panels.

## Best visual customization plugins

[耳朵 (@RookieRicardoR) on X](https://images.openai.com/static-rsc-4/Oj9f2jPJ9tEpYUuI8YoinGU8MXAuxM27ZtdbRlPTOQK9clsz8HeDNx4_L3rshmmm0edkemG79STt-mZ3XzrEEfdKpAKLl_shtA7Ri7l10kHvcccQK861vj9rql-GsGnyhBLD6JNB0IuVg-FaHrwC4AvDrgyGljchOUxs7PgTNTk?purpose=inline)

1\. [Beautify OpenCode](https://www.opendock.net/plugins/beautify-opencode/?utm_source=chatgpt.com)

Best for visual redesign

v0.1.1 · OpenCode v2 · MIT

Changes the appearance of existing interface elements: rounded btop-style panels, titles embedded in borders, redesigned meter bars, and gradient home-screen logo. Supports neon, btop, and theme-derived palettes. It doesn't add new panels.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock

[Opencode, an AI coding agent, built for the terminal.](https://images.openai.com/static-rsc-4/YQXvKZHCxOsBvKjg0MEO6tP4oBZbH2Q84BfDblVRl7WPMTe7uFSizziRXykHhI6zGKHvQkEnjR0B4ADTAfM7c9BI7a6KedjOJhrXHO0kPURkYZ4KQ8q8nWrs4jI6K3Dc73SB3UgM9jk3ZmmnKB09MgxvrCB9Rw3yH2bjNmUsrDI?purpose=inline)

2\. [OpenCode TUI Extras](https://www.opendock.net/plugins/opencode-tui-extras/?utm_source=chatgpt.com)

v1.1.0 · OpenCode v2.0.26+ · MIT

Adds transparent backgrounds, Powerline-style prompt/status bars, context usage statistics, and dedicated Skills and MCP sidebars. Particularly useful for a configuration with many skills and MCP servers.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock

[OpenCode가 요즘 뜨는 이유, 그리고 'Oh My OpenCode'가 유난히 사랑받는 이유](https://images.openai.com/static-rsc-4/KntWVBM7HL_5p_tJqRq0emiJluPhNlQQsAm1sCWYwRAge4K_olY4bTOepueAAbqS-lLj1FwGjdDOIlT7YcoOsK-SV1PzmEo_lFvZfGSAvazU3zBl4_2daZ-02XkC2W7nmX5b_OjRZR-K2aKMrmA3_i2-YL3bLtn2G18eYYhTi3c?purpose=inline)

3\. [OpenCode Sidebar TUI](https://www.opendock.net/plugins/opencode-sidebar-tui/?utm_source=chatgpt.com)

v0.3.3 · Developed for OpenCode v2.2.0 · MIT

Creates a unified monitoring sidebar showing MCP status, provider budgets, context consumption, installed plugins, skill usage, and todos. Also adds a Git-aware footer. The author reports testing on Windows; Linux compatibility deserves verification.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock

## How to install them in OpenCode v2

These are TUI plugins, so they belong in `cli.json`, not the server-side `opencode.jsonc` plugin array. OpenCode's official documentation confirms this separation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode

For a visual redesign without introducing more monitoring components, I would start with Beautify OpenCode:

```
// ~/.config/opencode/cli.json
{
  "plugins": [
    {
      "package": "beautify-opencode@0.1.1",
      "options": {
        "palette": "theme",
        "cards": true,
        "cardTitles": true,
        "boxBars": true,
        "textBars": true,
        "logo": true,
        "logoGradient": "aurora"
      }
    }
  ]
}
```

Merge this entry into your existing `cli.json` rather than replacing the file.

For additional monitoring and visual controls, TUI Extras is the more useful alternative:

```
{
  "plugins": [
    "-opencode.sidebar.context",
    "-opencode.sidebar.mcp",
    {
      "package": "opencode-tui-extras@1.1.0",
      "options": {
        "context": true,
        "sidebarScrollbar": false,
        "transparent": true,
        "mcp": true,
        "skills": true,
        "powerline": true
      }
    }
  ]
}
```

The two `-opencode.sidebar.*` entries disable the built-in sections that this plugin replaces, preventing duplicate sidebar content.

## You can also customize OpenCode without plugins

OpenCode v2 already supports theme selection, interface animations, cursor styling, sidebar visibility, vertical or horizontal tabs, transcript grouping, and Markdown presentation through `cli.json`.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode+1

For example:

```
{
  "theme": {
    "name": "catppuccin",
    "mode": "dark"
  },
  "animations": true,
  "cursor": {
    "style": "block",
    "blinking": true
  },
  "session": {
    "sidebar": "auto",
    "scrollbar": false,
    "grouping": "auto",
    "markdown": "rendered"
  },
  "tabs": {
    "mode": "on",
    "layout": "horizontal",
    "indicators": "status"
  }
}
```

The theme name must correspond to an installed or built-in theme. Custom themes can be created as JSON files using the [official theme system](https://dev.opencode.ai/v2/docs/cli/theme/?utm_source=chatgpt.com).

## What I recommend for your configuration

| Option                            | Visual impact | Recommendation                                        |
| --------------------------------- | ------------- | ----------------------------------------------------- |
| Beautify OpenCode                 | High          | Try first                                             |
| TUI Extras                        | Medium–high   | Add if you want more sidebar information              |
| Sidebar TUI                       | Medium–high   | Alternative to TUI Extras, not alongside it initially |
| Native themes and layout settings | Medium        | Configure regardless of plugin choice                 |

I would start with Beautify OpenCode + native Catppuccin theming, then evaluate TUI Extras separately. Beautify OpenCode is very new and modifies the rendered interface tree using heuristic matching, so its compatibility with future OpenCode updates is less certain than native theming.

I would also avoid running TUI Extras and Sidebar TUI simultaneously until their overlapping sidebar sections have been tested.

One other distinction: OpenCode Desktop has a separate GUI plugin system that supports CSS injection, custom themes, and panels. Those capabilities don't automatically apply to the terminal interface.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

For your existing setup, the most substantial appearance change with the fewest additional moving parts is Beautify OpenCode plus native theme and layout settings.

---

---

---

# PLAN 6

---

## Org Mode Integration

Yes, you can integrate OpenCode v2 with your Emacs Org-mode workflow, including `org-agenda`, `org-todo`, `org-capture`, `org-refile`, `org-clock`, and even `org-roam`.

The strongest solutions I found are MCP servers rather than conventional OpenCode plugins. That's an important distinction: OpenCode v2 can use MCP tools directly, and an Emacs-aware MCP server can interact with your existing Org configuration rather than maintaining a separate task database.

For your Emacs setup, I would prioritize an integration that preserves your custom TODO keywords, capture templates, agenda views, and Org-roam database.

## Best integrations

| Integration                                                                                      | Capabilities                                               | Assessment                           |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- | ------------------------------------ |
| [laurynas-biveinis/org-mcp](https://github.com/laurynas-biveinis/org-mcp?utm_source=chatgpt.com) | Agenda, capture, TODO states, tags, custom agenda commands | Best Emacs-native starting point     |
| [szaffarano/org-mcp-server](https://github.com/szaffarano/org-mcp-server?utm_source=chatgpt.com) | Agenda, capture, search, TODO updates, OpenCode skills     | Best standalone Org-file integration |
| [rhblind/emacs-mcp-server](https://github.com/rhblind/emacs-mcp-server?utm_source=chatgpt.com)   | Agenda, capture, refile, archive, clocking, Org-roam       | Best broad feature coverage          |
| [jeigrei/org-mcp](https://github.com/jeigrei/org-mcp?utm_source=chatgpt.com)                     | TODOs, capture, agenda-style workflows                     | Lightweight file-backed alternative  |

These are real projects with documented Org functionality, although I have not yet verified them running against your exact Emacs and OpenCode versions.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub+3

## Which features are supported?

| Org feature   | Emacs-native `org-mcp`         | `rhblind/emacs-mcp-server` | `szaffarano/org-mcp-server` |
| ------------- | ------------------------------ | -------------------------- | --------------------------- |
| `org-agenda`  | Yes, including custom commands | Yes                        | Yes                         |
| `org-todo`    | Yes                            | Yes                        | Yes                         |
| `org-capture` | Yes                            | Yes, existing templates    | Yes, file-backed capture    |
| `org-refile`  | Not confirmed                  | Yes                        | Not documented              |
| `org-archive` | Not confirmed                  | Yes                        | Not documented              |
| `org-clock`   | Not confirmed                  | Yes                        | Not documented              |
| `org-roam`    | Not confirmed                  | Yes                        | Not documented              |

The key advantage of the Emacs-native implementations is that they can respect Org's actual semantics rather than merely editing `.org` text. In particular, `rhblind/emacs-mcp-server` documents support for existing capture templates, Org refile and archive operations, clocking, and Org-roam nodes.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://mcpmarkets.com&sz=32)

MCPMarkets

## How I would integrate this into your OpenCode v2 setup

OpenCode v2

Coding agents · Research agents · Orchestrator

MCP tools

Emacs Org MCP server

Agenda · Capture · TODO · Clock · Refile

Org-mode operations

Emacs 30/31 Org-mode

\~/org · Org agenda · Org capture · Org-roam

OpenCode v2's official MCP configuration uses `mcp.servers`, not the older v1-style configuration.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

For the Emacs-native `laurynas-biveinis/org-mcp`, the documented setup requires `mcp-server-lib`, explicit allowed files, and starting the server inside Emacs. Its README supplies a stdio bridge script that can be registered with an MCP client.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

For example, after installing the Emacs dependencies and setting up that bridge, the OpenCode v2 side would look like this:

```
{
  "mcp": {
    "servers": {
      "emacs-org": {
        "type": "local",
        "command": [
          "/home/YOUR_USER/.emacs.d/emacs-mcp-stdio.sh",
          "--server-id=org-mcp",
          "--init-function=org-mcp-enable",
          "--stop-function=org-mcp-disable"
        ]
      }
    }
  }
}
```

This is an integration template, not a ready-to-run configuration. The bridge script, Emacs server, and file permissions must first be configured.

Once connected, you could ask OpenCode to:

- Show today's Org agenda, including deadlines and scheduled tasks.
- Capture a coding task under the correct Org capture template.
- Mark a TODO as DONE after tests pass.
- Refile completed project work or archive it.
- Clock time spent on a development task.
- Search Org-roam for existing notes relevant to a research project.

These operations depend on which MCP server you choose.

## My recommendation

For your existing Emacs and OpenCode workflow, I would evaluate `rhblind/emacs-mcp-server` first, because its documented feature set covers the largest portion of your Org workflow, particularly capture templates, clocking, refiling, and Org-roam.

I would use `laurynas-biveinis/org-mcp` instead if preserving your custom `org-agenda-custom-commands` is the highest priority. Its agenda API explicitly supports those commands.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

I would also implement two safeguards: restrict write access to your intended Org files and require approval before destructive or bulk modifications. The `org-mcp` maintainer explicitly warns that AI tools can modify or delete Org data and recommends backups and versioning.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

One important design decision: should OpenCode merely read your agenda and capture tasks on request, or should your coding agents automatically update Org TODO states, clock time, and create project entries as their workflows progress?

The second option is feasible, but would benefit from a small dedicated OpenCode v2 plugin layered on top of an Org MCP server, with controlled lifecycle hooks and task-to-Org-ID mapping.&#x20;

[NOTE:] -> SKILLS and mcp combined
Yes. Separate, customized OpenCode v2 skills can reproduce most of the Org-mode workflow I described, and they may be a better architectural fit for your existing agent configuration than installing a large, general-purpose MCP server.

However, there is an important distinction:

- Skills define how an agent performs a workflow. They provide instructions, procedures, conventions, and reusable scripts.
- MCP servers expose capabilities. They provide structured tools for interacting with Emacs or Org-mode.

A skill can invoke `emacsclient`, run Emacs Lisp, and operate on your existing Org files. This means you can implement agenda retrieval, TODO management, capture, refiling, clocking, and Org-roam operations without an MCP server.

The main trade-off is that a skill alone does not create a persistent integration with Emacs. It still needs a reliable execution mechanism, such as `emacsclient` and a running Emacs server.

## 1. What can customized skills reproduce?

| Org-mode capability                               | Skills + `emacsclient`                    | MCP required?   |
| ------------------------------------------------- | ----------------------------------------- | --------------- |
| Read today's `org-agenda`                         | Full support with helper functions        | No              |
| List and filter `org-todo` entries                | Full support                              | No              |
| Create entries using `org-capture` templates      | Full support                              | No              |
| Schedule tasks and deadlines                      | Full support                              | No              |
| Refile tasks to projects                          | Full support                              | No              |
| Archive completed tasks                           | Full support                              | No              |
| Start/stop `org-clock`                            | Full support                              | No              |
| Search and create Org-roam nodes                  | Full support with Org-roam installed      | No              |
| Automatically update tasks after agent completion | Requires additional lifecycle integration | Not necessarily |
| Real-time, event-driven synchronization           | Requires a plugin, hook, or watcher       | Not necessarily |

Here, full support means that Emacs provides the underlying operations and a custom integration can expose them. It does not mean OpenCode supplies those operations automatically.

GNU Emacs officially supports evaluating Emacs Lisp through `emacsclient --eval`, and OpenCode v2 supports skills containing reusable instructions and supporting scripts.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.gnu.org&sz=32)

gnu.org+1

## 2. My proposed skill architecture

I would divide the integration into six specialized skills rather than creating one enormous Org-mode skill.

OpenCode v2 agents

Orchestrator · Coder · Researcher · Reviewer

org-agenda

Review tasks, deadlines and priorities

org-todo

Create, update, schedule and refile tasks

org-capture

Capture ideas, findings and project notes

org-clock

Track time against existing Org entries

org-roam

Search and link knowledge notes

org-project

Synchronize agent milestones with Org

Shared Python/Emacs Lisp bridge

Input validation · JSON output · Error handling · emacsclient

Running Emacs + Org-mode

\~/org · Org agenda · Capture templates · Org-roam

Each skill would contain a `SKILL.md` describing the operations and one or more scripts that perform the actual work.

A possible repository structure:

```
skills/
├── org-agenda/
│   ├── SKILL.md
│   └── scripts/agenda.py
├── org-todo/
│   ├── SKILL.md
│   └── scripts/todo.py
├── org-capture/
│   ├── SKILL.md
│   └── scripts/capture.py
├── org-clock/
│   ├── SKILL.md
│   └── scripts/clock.py
├── org-roam/
│   ├── SKILL.md
│   └── scripts/roam.py
├── org-project/
│   ├── SKILL.md
│   └── scripts/project.py
└── _shared/
    ├── emacs_bridge.py
    └── org_bridge.el
```

OpenCode v2 discovers directory-based skills and loads their full instructions on demand. The supporting scripts are not automatically executed simply because the skill is loaded.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

## 3. Example: a customized Org agenda skill

Here is a minimal `SKILL.md` showing how I would structure one skill.

```
---
name: org-agenda
description: Read and summarize the user's Emacs Org agenda, scheduled tasks, deadlines, and priorities.
---

# Org Agenda

Use this skill when the user asks about:
- Today's tasks or weekly schedule
- Overdue deadlines
- Project priorities
- Outstanding TODO items

## Workflow

1. Check that the Emacs server is running.
2. Call the shared Org agenda bridge.
3. Parse the structured JSON output.
4. Present tasks grouped by date and priority.
5. Do not modify tasks without explicit authorization.

## Rules

- Use the user's existing org-agenda-files.
- Respect custom TODO keywords and agenda commands.
- Never edit .org files directly when an Emacs Org API
  operation is available.
- Report bridge errors rather than inventing task data.
```

This is an illustrative skill specification, not a complete executable integration.

## 4. The critical part: reliable Emacs communication

I would avoid letting agents generate arbitrary Emacs Lisp and execute it directly.

Instead, create a small, fixed API in Emacs Lisp:

```
(my/org-api-agenda ...)
(my/org-api-todo ...)
(my/org-api-capture ...)
(my/org-api-refile ...)
(my/org-api-clock ...)
(my/org-api-roam ...)
```

These are proposed functions, not built-in Org-mode functions.

The shared bridge would validate arguments, invoke only approved functions through `emacsclient`, and return structured JSON.

This provides several advantages over unconstrained shell commands: predictable results, less risk of malformed Org files, preservation of Emacs configuration, and easier testing.

For your Fedora setup, I would also require all write operations to use the running Emacs instance, avoiding simultaneous modifications by Emacs and external scripts.

## 5. Where skills are not enough

The principal limitation is automation.

Suppose your OpenCode orchestrator is implementing a Python package. You want it to:

1. Create an Org TODO when implementation begins.
2. Start an Org clock.
3. Update the task when tests pass.
4. Capture the implementation summary.
5. Stop the clock when the workflow finishes.

A skill can instruct the agent to perform all five steps. However, it cannot guarantee that every step executes. The agent might omit a step, terminate unexpectedly, or lose relevant instructions after a long workflow.

For stronger guarantees, I would introduce a small OpenCode v2 lifecycle plugin that calls the same shared Org bridge when selected agent events occur. The plugin would handle event detection; the skills would handle the higher-level Org workflow.

This would be a more robust solution than relying exclusively on agent compliance with skill instructions.

## 6. What I would implement first

For your existing configuration, I recommend a skills-first, MCP-optional architecture:

- Build the six Org skills using a single, tested Emacs Lisp/Python bridge.
- Preserve your existing Org capture templates, custom TODO keywords, agenda configuration, and Org-roam setup.
- Use stable Org IDs to associate coding tasks and agent sessions with Org entries.
- Require confirmation for destructive actions such as archiving, deleting, or bulk refiling.
- Add a small lifecycle plugin later if you need reliable automatic task tracking.

This approach avoids installing a large MCP server while giving you direct control over how your agents interact with Emacs.

My recommendation is not to install an Org MCP server yet. Start with customized skills and a shared bridge. Add an MCP server only if you later need standardized tool discovery or access from several different AI clients.

The official [OpenCode v2 Skills documentation](https://dev.opencode.ai/v2/docs/skills/?utm_source=chatgpt.com) supports this architecture, including on-demand skill loading and bundled scripts.

For your workflow, the biggest benefit is that Emacs remains the authoritative source of tasks and research notes, while OpenCode acts as an intelligent interface to it.&#x20;

# PLAN 7: Chatgpt Usage

Yes. There are OpenCode plugins for tracking AI-provider usage, but tracking a ChatGPT subscription is different from tracking OpenAI API usage.

For your OpenCode v2 setup, the distinction matters:

- ChatGPT subscription usage: remaining usage allowance, rate limits, and reset times associated with your ChatGPT/OpenAI sign-in.
- OpenAI API usage: token consumption and dollar-denominated billing through an API key.
- OpenCode session usage: tokens, cache usage, and model activity recorded by OpenCode itself.

A plugin can accurately report one category without supporting the others. In particular, token costs calculated using API prices should not be interpreted as charges against a ChatGPT Plus subscription.

## Verified OpenCode v2 plugins

I found several relevant packages on OpenDock, including ones explicitly designed for ChatGPT/Codex subscription quotas.

| Plugin                                                                                                              | Interface               | What it tracks                                                  |
| ------------------------------------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------- |
| [opencode-openai-limits](https://www.opendock.net/plugins/opencode-openai-limits/?utm_source=chatgpt.com)           | Footer + sidebar        | ChatGPT/Codex remaining quota, primary and weekly reset windows |
| [opencode-usage-monitor](https://www.opendock.net/plugins/opencode-usage-monitor/?utm_source=chatgpt.com)           | Sidebar                 | ChatGPT/Codex, Z.AI, DeepSeek and OpenCode Go                   |
| [opencode-quota-tracker](https://www.opendock.net/plugins/opencode-quota-tracker/?utm_source=chatgpt.com)           | `/quota` screen         | GPT and Claude subscription quotas, API and local usage         |
| [opencode-v2-cli-codex-usage](https://www.opendock.net/plugins/opencode-v2-cli-codex-usage/?utm_source=chatgpt.com) | Sidebar                 | Remaining Codex quota, reset timers, credits                    |
| [opencode-codex-usage](https://www.opendock.net/plugins/opencode-codex-usage/?utm_source=chatgpt.com)               | Command + notifications | Codex quota, reset times, threshold alerts                      |

All five are listed as OpenCode v2-compatible, although they have different minimum versions and authentication requirements.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock+4

One compatibility warning: `opencode-codex-usage` currently documents that it does not support the newer ChatGPT token-sharing sign-in method. It requires one of the legacy Codex OAuth login methods. I would not choose it as your default unless you use that authentication method.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock

## My recommendation

For your configuration, I would choose `opencode-openai-limits` if you only need ChatGPT Plus/Codex usage, or `opencode-usage-monitor` if you want multiple providers displayed together.

[OpenAI Limits](https://www.opendock.net/plugins/opencode-openai-limits/?utm_source=chatgpt.com)

v0.1.0 · OpenCode v2

Displays remaining usage percentages and reset countdowns directly in the footer and sidebar. Uses OpenCode's active OpenAI OAuth credential, rather than requiring a separate API key.

Illustrative sidebar display

OpenAI usage

Primary window · example: 80% remaining

Weekly window · example: 65% remaining

Example only — not your actual account usage.

For broader monitoring, `opencode-usage-monitor` is more mature in versioning and provides a configurable sidebar, but introduces additional configuration and provider integrations.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock

### Important limitations

These plugins generally retrieve ChatGPT/Codex subscription quota information from an undocumented ChatGPT usage endpoint. Consequently, their functionality could break if the endpoint or authentication behavior changes. They also cannot necessarily report every ChatGPT product limit, such as ordinary web-chat message allowances.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock+1

They require access to sensitive OAuth credentials, so I would review the source before installing one.

Bottom line: Yes, standardized, packaged OpenCode v2 plugins exist for tracking your ChatGPT/Codex subscription usage. For your setup, `opencode-openai-limits` is the simplest fit, while `opencode-usage-monitor` is better if you want a unified provider dashboard. I would install only one quota-display plugin initially to avoid duplicated UI elements and unnecessary polling.

---

---

---

# PLAN 8: github repo

# OpenCode v2 — Quick Cheatsheet

A compact reference for everyday terminal usage, agent workflows, configuration, and debugging.

## 1. Start OpenCode

| Command                 | Purpose                   |
| ----------------------- | ------------------------- |
| `opencode`              | Launch interactive TUI    |
| `opencode .`            | Open current project      |
| `opencode run "prompt"` | Run a one-off prompt      |
| `opencode --help`       | Show CLI commands         |
| `opencode --version`    | Show installed version    |
| `opencode models`       | List available models     |
| `opencode auth login`   | Configure a provider      |
| `opencode auth list`    | List configured providers |

## 2. Keyboard shortcuts

| Shortcut               | Action                                        |
| ---------------------- | --------------------------------------------- |
| `Enter`                | Submit prompt; steer a running agent          |
| `Ctrl+X`, then `Enter` | Queue prompt until current work finishes      |
| `Shift+Enter`          | Insert a newline                              |
| `Esc`                  | Interrupt running generation                  |
| `Ctrl+C`               | Cancel input or interrupt, depending on state |
| `Tab`                  | Switch agents, where supported                |
| `Ctrl+P`               | Open command palette, where configured        |

Some shortcuts can be customized, so check the TUI's keybinding help for your installation.

## 3. Common TUI commands

| Command     | Purpose                         |
| ----------- | ------------------------------- |
| `/help`     | Display help                    |
| `/new`      | Start a new session             |
| `/sessions` | Browse sessions                 |
| `/models`   | Choose a model                  |
| `/agents`   | Choose an agent                 |
| `/compact`  | Compact conversation context    |
| `/undo`     | Undo the last applicable change |
| `/redo`     | Redo an undone change           |
| `/exit`     | Leave OpenCode                  |

Custom commands and installed plugins may add more entries.

## 4. Working with files and shell commands

| Syntax                        | Example                       |
| ----------------------------- | ----------------------------- |
| Attach a file                 | `@src/main.py`                |
| Attach specific lines         | `@src/main.py#20-45`          |
| Execute shell command         | `!git status`                 |
| Ask a temporary side question | `/btw Why did the test fail?` |

`/btw` answers a question without adding it to the main conversation context.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

## 5. Useful additional shortcuts

| Shortcut           | Action                         |
| ------------------ | ------------------------------ |
| `Ctrl+X`, then `M` | Select model                   |
| `Ctrl+X`, then `A` | Select agent                   |
| `Shift+Tab`        | Cycle agents                   |
| `Ctrl+X`, then `N` | New session                    |
| `Ctrl+X`, then `L` | Session list                   |
| `Ctrl+X`, then `U` | Undo                           |
| `Ctrl+X`, then `R` | Redo                           |
| `Ctrl+X`, then `E` | Edit prompt in external editor |
| `Ctrl+X`, then `Q` | Manage queued prompts          |
| `Ctrl+Tab`         | Next tab                       |

`Ctrl+X` is the default leader key; custom keybindings may override these.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode+1

## 6. Plugins, MCP servers, and usage

```
# Plugins
opencode plugin list
opencode plugin check
opencode plugin update

# MCP servers
opencode mcp list

# Usage statistics
opencode stats
opencode stats --days 7
opencode stats --models
opencode stats --cost

# Script-friendly output
opencode run --format json "Summarize this project"
```

These commands are documented for OpenCode v2.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

## 7. Configuration locations

| Location                            | Purpose                          |
| ----------------------------------- | -------------------------------- |
| `~/.config/opencode/opencode.jsonc` | Global runtime configuration     |
| `~/.config/opencode/cli.json`       | Terminal interface configuration |
| `~/.config/opencode/skills/`        | Global custom skills             |
| `.opencode/skills/`                 | Project-specific skills          |
| `AGENTS.md`                         | Project instructions             |

## 8. Everyday workflow

```
cd ~/projects/my-project
opencode
```

Then prompt:

```
Analyze this repository and explain its architecture.
```

```
Create an implementation plan. Do not modify files yet.
```

```
Implement the approved plan and run relevant tests.
```

```
Review the git diff for bugs, regressions, and security issues.
```

Official references: [TUI guide](https://dev.opencode.ai/v2/docs/cli/tui/?utm_source=chatgpt.com) · [CLI commands](https://dev.opencode.ai/v2/docs/cli/commands/?utm_source=chatgpt.com) · [Keyboard shortcuts](https://dev.opencode.ai/v2/docs/cli/keybinds/?utm_source=chatgpt.com)

---

---

---

# PLAN 9: Vim Integration

OpenCode v2 does not appear to have an officially maintained Vim-mode plugin, but there is a third-party Vim plugin designed for the official OpenCode v2 terminal interface.

The most relevant option is [OpenCode Vim by leohenon](https://leohenon.github.io/opencode-vim/?utm_source=chatgpt.com). It provides modal editing without requiring you to replace OpenCode with a fork.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://leohenon.github.io&sz=32)

Vim mode for OpenCode

## Available Vim integrations

| Option                                                                                 | OpenCode v2 support     | Recommendation                                       |
| -------------------------------------------------------------------------------------- | ----------------------- | ---------------------------------------------------- |
| [OpenCode Vim plugin](https://github.com/leohenon/opencode-vim?utm_source=chatgpt.com) | v2.0.25+, beta          | Best starting point                                  |
| [vimcode](https://github.com/oribarilan/vimcode?utm_source=chatgpt.com)                | Experimental v2 support | Alternative, with more compatibility risk            |
| Native OpenCode keybindings                                                            | Officially supported    | Best for remapping shortcuts, not full Vim emulation |
| External Neovim editor                                                                 | Officially supported    | Best for full Vim editing without a plugin           |

The OpenCode Vim plugin supports motions, operators, text objects, registers, visual selection, and repeat operations. Its plugin version applies to prompt editing only; the author's separate OpenCode fork also implements Vim-based session navigation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://leohenon.github.io&sz=32)

Vim mode for OpenCode

## 1. Install the Vim plugin

The author's current website documents this command:

```
opencode plugin @leohenon/opencode-vim-plugin --global
```

The project also documents a beta build for OpenCode v2. Before installing, check the plugin's [repository](https://github.com/leohenon/opencode-vim-plugin?utm_source=chatgpt.com) for its current compatibility requirements and release channel.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://leohenon.github.io&sz=32)

Vim mode for OpenCode

## 2. Avoid conflicts with default keybindings

OpenCode v2's default leader key is `Ctrl+X`, which can coexist with Vim normal-mode keys. I recommend keeping `Ctrl+X` as the OpenCode leader rather than remapping it to Space immediately.

The potential conflicts are:

| Key       | Vim behavior                                    | OpenCode behavior         | Recommendation                     |
| --------- | ----------------------------------------------- | ------------------------- | ---------------------------------- |
| `Esc`     | Return to Normal mode                           | Interrupt generation      | Check mode-aware handling          |
| `Enter`   | Insert newline or confirm, depending on context | Submit or steer prompt    | Preserve OpenCode submission       |
| `Tab`     | Completion/navigation                           | Agent switching           | Preserve completion in Insert mode |
| `Ctrl+P`  | Often mapped to fuzzy finding in Vim setups     | Open command palette      | Keep OpenCode default              |
| `Ctrl+X`  | Various Vim insert-mode operations              | OpenCode leader           | Keep OpenCode default initially    |
| `j` / `k` | Move cursor in Normal mode                      | Text input in Insert mode | Let Vim plugin handle these        |

The most important conflict is Esc: pressing it to leave Vim Insert mode should not accidentally interrupt an active OpenCode operation.

## 3. Recommended OpenCode v2 keybindings

OpenCode v2 stores TUI settings in `~/.config/opencode/cli.json`, separate from `opencode.jsonc`.

For a conservative Vim-friendly setup:

```
{
  "$schema": "https://opencode.ai/v2/cli.json",
  "keybinds": {
    "leader": "ctrl+x",
    "session.interrupt": "ctrl+g"
  },
  "leader": {
    "timeout": 2000
  }
}
```

This example moves session interruption from `Esc` to `Ctrl+G`, reducing one potential collision with Vim mode. However, it is a proposed mapping, not a verified plugin-specific requirement. You should test whether the plugin already handles `Esc` correctly before changing it.

Merge the `keybinds` and `leader` objects into your existing configuration. Do not overwrite other settings.

OpenCode's official configuration documentation supports remapping commands and disabling bindings with `"none"`.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

## 4. Alternative: use Neovim as the prompt editor

If you want full Vim behavior without depending on an experimental plugin, this is the most robust option.

```
export EDITOR=nvim
export VISUAL=nvim
opencode
```

Inside OpenCode, press `Ctrl+X`, then `E`, or run `/editor`.

This opens the current prompt in Neovim, where your existing mappings, plugins, registers, and text objects work normally. Save and exit to return the prompt to OpenCode.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

## Recommendation

For your customized OpenCode v2 setup, I would use OpenCode Vim's prompt plugin, preserve the default leader initially, and only remap keys that produce reproducible conflicts.

I would not adopt the author's full OpenCode fork solely to obtain Vim keybindings, because that introduces another OpenCode distribution to maintain.

If your priority is maximum reliability rather than inline modal editing, use the official external-editor integration with Neovim—or Emacs, if you prefer your existing Emacs editing environment.
