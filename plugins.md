# OpenCode V2 + OpenChamber: verified plugin recommendations

Updated November 1, 2026 · Cross-checked using Context7, Exa, official OpenCode V2 documentation, OpenChamber documentation, and plugin maintainers' repositories

## 1. Findings from reviewing my previous recommendations

The overall approach was correct, but several recommendations need correction or stronger qualifications. In particular, I would change which plugins are installed by default.

| Previous recommendation         | Verification result                                                  | Revised recommendation                                                               |
| ------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `@plannotator/opencode`         | Native V2 support confirmed                                          | Keep; configure manual workflow                                                      |
| `@tarquinen/opencode-dcp`       | Native V2 support confirmed                                          | Keep optional; benchmark token savings first                                         |
| `@bulga138/redactor`            | V2-native implementation documented                                  | Keep as an optional security layer, not a security guarantee                         |
| `opencode-supermemory`          | V2 support confirmed                                                 | Optional; automatic memory activity conflicts with strict manual-service preferences |
| `opencode-pty`                  | V2 adapter documented, but instructions mix old configuration syntax | Defer until tested with your permissions                                             |
| `opencode-goal-plugin`          | V2 support documented                                                | Generally unnecessary with OpenChamber Session Goals                                 |
| `opencode-notifier`             | V2 support confirmed                                                 | CLI-focused optional addition, not essential for OpenChamber                         |
| `opencode-wakatime`             | Official WakaTime V2 package confirmed                               | Add as an optional analytics integration                                             |
| Excalidraw and Resource Monitor | Official OpenChamber integrations confirmed                          | Keep                                                                                 |

The most important correction concerns V2 compatibility.

OpenCode V2 uses a new plugin implementation API based on `@opencode/plugin` and `Plugin.define({ id, setup })`. A plugin written exclusively for V1 does not become V2-compatible simply because you put it inside the `plugins` array. Context7's V2-indexed documentation and the official migration guide both confirm this.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode+1

The second correction concerns token optimization: DCP changes context sent to the model, which can invalidate cached prompt prefixes. It may reduce total token volume without necessarily reducing billed cost in every workload. Its maintainer has also shifted much of its newer development to Sleev.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub+1

## 2. Recommended OpenCode V2 plugins

I would organize your setup into three tiers: core functionality, development enhancements, and optional external services.

1\. Plannotator — visual plan reviews

Package: `@plannotator/opencode` · Verified V2 support

Lets you annotate implementation plans, review code and documents, and give structured feedback before major edits.

Particularly useful for complex software changes and configuration rewrites. Its maintainer documents stable OpenCode 2 support and CI testing against the new plugin API.

Use `workflow: "manual"` so review isn't automatically triggered whenever the plan agent runs. The plugin's optional agent tools should remain disabled.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

[Repository and installation guide](https://github.com/backnotprop/plannotator?utm_source=chatgpt.com)

2\. REDACTOR — credential redaction

Package: `@bulga138/redactor` · V2-native, limited independent adoption

Redacts recognized credential patterns from tool results and historical tool-result context. It can help prevent accidental model exposure when inspecting Git output, shell logs, configuration files, or MCP results.

Its published implementation uses V2 tool and context hooks. It does not rewrite tool inputs, and it cannot detect every secret or erase previously exposed secrets. I would test it using synthetic keys before trusting it with sensitive repositories.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opendock.net&sz=32)

OpenCode plugin · OpenDock

[Technical details and limitations](https://www.opendock.net/plugins/bulga138--redactor/?utm_source=chatgpt.com)

3\. Dynamic Context Pruning — controlled context reduction

Package: `@tarquinen/opencode-dcp` · Native V2 support from version 3.2.0

Provides conversation compression, tool-output deduplication, and pruning of obsolete material. It complements your existing Compactor agent but serves a different purpose: the agent produces handoff summaries, while DCP optimizes the model's active context.

Install it as an experiment, compare completed tasks and token usage, and retain it only when the benefit is measurable. Compression permission support in V2 currently distinguishes `allow` and `deny`, not interactive `ask`.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub+1

[Repository and V2 release notes](https://github.com/Tarquinen/opencode-dynamic-context-pruning?utm_source=chatgpt.com)

My revised default: Plannotator with manual workflow. Add REDACTOR after a privacy test, and DCP after a token-efficiency benchmark. This is safer than installing all three without validation.

## 3. More useful OpenCode V2 plugins

These have documented V2 implementations, though their value depends on whether you primarily use the CLI or OpenChamber Desktop.

| Plugin                                                                                                                | What it adds                                                      | My recommendation                                 |
| --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------- |
| [`@wakatime/opencode-wakatime`](https://github.com/wakatime/opencode-wakatime?utm_source=chatgpt.com)                 | AI coding activity, token usage, cache usage, costs, file changes | Recommended if you want detailed usage analytics  |
| [`@mohak34/opencode-notifier`](https://github.com/mohak34/opencode-notifier?utm_source=chatgpt.com)                   | Desktop notifications for approvals, errors, completed sessions   | Useful for the CLI; less necessary in OpenChamber |
| [`opencode-supermemory`](https://github.com/supermemoryai/opencode-supermemory?utm_source=chatgpt.com)                | Persistent memory, project knowledge, recall across sessions      | Optional; requires separate privacy review        |
| [`@prevalentware/opencode-goal-plugin`](https://github.com/prevalentWare/opencode-goal-plugin?utm_source=chatgpt.com) | Persistent objectives, goal continuation, task recovery           | Mostly redundant with OpenChamber Session Goals   |
| [`opencode-pty`](https://github.com/shekohex/opencode-pty?utm_source=chatgpt.com)                                     | Interactive/background terminal sessions and persistent output    | Defer due to permission-behavior caveats          |

### WakaTime: my strongest additional recommendation

The official WakaTime plugin documents OpenCode V2 support, including tracking input/output tokens, cached input, code changes, and costs. Its package is `@wakatime/opencode-wakatime`, not simply the older community package name `opencode-wakatime`.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

This makes it useful for measuring actual agent usage, particularly if you want to assess whether DCP saves tokens. But it sends activity data to WakaTime and can automatically download the WakaTime CLI, so install it only when you're comfortable with those background actions.

### Why I'm cautious about PTY

The maintainer documents a V2 adapter, but its examples still use `plugin` instead of the canonical V2 `plugins` format. More importantly, the published limitations state that `ask` permissions may be treated as `deny` for spawned processes, while certain external-directory prompts can be treated as allowed.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

Given your emphasis on explicit approval, I would not install this plugin by default. OpenChamber's existing terminal and dev-server interfaces should be evaluated first.

### Optional: stronger secret handling

Two alternatives deserve mentioning, but I would not run several secret-transforming plugins together without extensive tests.

| Alternative                                                                                                 | Verified characteristics                                                                                      | Caveat                                                                               |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [Rehydra](https://www.npmjs.com/package/@rehydra/opencode?utm_source=chatgpt.com)                           | Documented dual V1/V2 implementation; can redact values from `.env` files and protect external tool arguments | Reads configured secret files and transforms tool arguments; requires careful review |
| [Secret Shield](https://www.opendock.net/plugins/bandonker--opencode-secret-shield/?utm_source=chatgpt.com) | Listed as V2-native; supports observe, redact, and block modes                                                | Newer, less-established package; default is observation rather than blocking         |

For your system, I would test REDACTOR alone first. Adding more secret-transforming layers increases the possibility of broken tool inputs, unexpected substitutions, and difficult debugging.

## 4. OpenChamber extensions: expanded recommendations

OpenChamber extensions are not OpenCode plugins. They use OpenChamber's own extension framework and are installed through its interface. The official directory currently lists 42 community and official extensions across workflow, monitoring, developer tools, memory, and file management.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openchamber.dev&sz=32)

Community Directory+1

Here is the shortlist I would use for your Linux development and ChatGPT-like Work environment.

| Extension                                                                                    | Benefit                                                                     | Priority                          |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------- |
| [Excalidraw](https://docs.openchamber.dev/integrations/?utm_source=chatgpt.com)              | Edit diagrams and architecture drawings inside the file viewer              | High                              |
| [Resource Monitor](https://docs.openchamber.dev/integrations/?utm_source=chatgpt.com)        | Monitor CPU, memory, OpenCode processes and development servers             | High                              |
| [Context Inspector](https://openchamber.dev/extensions/?utm_source=chatgpt.com)              | Inspect context consumption by tools, skills, instructions and conversation | High                              |
| [Skills Manager](https://openchamber.dev/extensions/?utm_source=chatgpt.com)                 | Enable/disable OpenCode skills and manage groups or naming collisions       | High                              |
| [Open With](https://openchamber.dev/extensions/?utm_source=chatgpt.com)                      | Open the active project in Emacs, another editor, terminal or file manager  | High                              |
| [OpenChamber Makefile](https://openchamber.dev/extensions/?utm_source=chatgpt.com)           | List and run Makefile targets through a graphical panel                     | High for source-based development |
| [OpenChamber Kanban](https://openchamber.dev/extensions/?utm_source=chatgpt.com)             | Organize agent tasks on a board, linked to individual sessions              | Medium                            |
| [OpenSpec](https://openchamber.dev/extensions/?utm_source=chatgpt.com)                       | Browse specifications, plans, changes and implementation progress           | Medium                            |
| [Docker](https://github.com/openchamber/openchamber-extension-docker?utm_source=chatgpt.com) | Manage containers, Compose stacks, logs and images                          | Conditional                       |
| [WakaTime](https://openchamber.dev/extensions/?utm_source=chatgpt.com)                       | Usage statistics inside the OpenChamber sidebar                             | Conditional                       |
| [OpenChamber Queue](https://openchamber.dev/extensions/?utm_source=chatgpt.com)              | Queue tasks and start new sessions when a project becomes idle              | Optional                          |
| [GitHub Task Board](https://openchamber.dev/extensions/?utm_source=chatgpt.com)              | Link GitHub issues, dependencies and agent sessions                         | Optional                          |

These entries come from the current OpenChamber extension directory. The directory establishes availability and advertised functionality; it does not constitute independent security review of each community package.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openchamber.dev&sz=32)

Community Directory

### Which matter most for you?

Context Inspector + Resource Monitor

This is my preferred monitoring pair. One helps explain what occupies the agent's context; the other shows actual CPU and memory usage. They address different performance questions without introducing more MCP servers.

Skills Manager + Open With + Makefile

Useful for a setup involving Emacs, Fedora configuration, Python scripts, and complex repositories. Skills Manager organizes the assistant's instructions, Open With connects the GUI to your preferred editor, and Makefile provides convenient build/test commands.

Kanban or OpenSpec

Choose Kanban for general task management; choose OpenSpec for specification-driven development. You do not need both initially, and neither should automatically dispatch work without your approval.

The official Docker extension is powerful, but it uses host-side Docker execution. It can start, stop, remove and prune Docker resources, so treat it as a high-privilege extension rather than a simple monitoring widget.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

OpenChamber extensions can also request permissions to send prompts, read or write files, inspect sessions, or run local services with your user privileges. Examine those permissions individually.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.openchamber.dev&sz=32)

OpenChamber Docs

## 5. Recommended OpenCode V2 configuration

For your existing `~/.config/opencode/opencode.jsonc`, I recommend a conservative base configuration, with optional plugins explicitly listed but commented out.

```
{
  "$schema": "https://opencode.ai/config.json",

  "plugins": [
    {
      "package": "@plannotator/opencode",
      "options": {
        "workflow": "manual"
      }
    }

    // Enable after testing with synthetic credentials:
    // ,"@bulga138/redactor"

    // Enable only after benchmarking context usage:
    // ,"@tarquinen/opencode-dcp@3.2.0"

    // Optional: sends coding statistics to WakaTime:
    // ,"@wakatime/opencode-wakatime"

    // Optional: terminal-specific notifications:
    // ,"@mohak34/opencode-notifier"
  ]
}
```

This is the `plugins` section to merge, not a complete replacement for your configuration. Preserve your existing `agents`, `permissions`, `policies`, `compaction`, and `mcp.servers` settings.

The JSONC format above is valid, including the commented optional entries. OpenCode V2 supports package strings and `{ package, options }` objects in its plural `plugins` array.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai&sz=32)

OpenCode

For production use, replace unversioned packages with exact versions after testing them against your installed OpenCode release. I wouldn't invent version numbers that haven't been verified.

### Important distinction: plugins vs MCP

Your permanent MCP configuration should continue to follow this pattern:

```
{
  "mcp": {
    "servers": {
      "exa": {
        "type": "remote",
        "url": "https://mcp.exa.ai/mcp",
        "disabled": true,
        "codemode": false
      },
      "context7": {
        "type": "remote",
        "url": "https://mcp.context7.com/mcp",
        "disabled": true,
        "codemode": false
      }
    }
  }
}
```

This illustrates only two of your existing nine MCP servers. Retain the others in the actual file.

There are two separate security boundaries:

MCP connection boundary: `disabled: true` prevents normal startup connection. Your manual controller activates a server only when you authorize it.

Plugin execution boundary: A configured plugin loads when OpenCode starts and can register hooks or perform its own network requests. It is not governed automatically by `mcp.servers[*].disabled`.

V2's plugin API even supports modifying MCP configuration through transforms. Therefore, avoid plugins that automatically register or activate MCP servers, and recheck MCP status after installing each plugin.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai&sz=32)

OpenCode+1

For your strict policy, no plugin should be allowed to silently convert a disabled server into an active one.

## 6. Reproducing your ChatGPT plugin ecosystem

The existing ChatGPT plugin ecosystem you described is broader than coding. Here's the appropriate integration strategy.

| Capability                                  | Best implementation                                      | Additional plugin? |
| ------------------------------------------- | -------------------------------------------------------- | ------------------ |
| Exa search and research                     | Existing Exa MCP and Web Researcher agent                | No                 |
| Context7 documentation                      | Existing Context7 MCP                                    | No                 |
| Consensus / SciSpace / alphaXiv / Undermind | Separate, manually activated research connections        | No                 |
| GitHub                                      | `git-gh` agent, `gh`, existing GitHub MCP                | No                 |
| TickTick                                    | Existing TickTick MCP                                    | No                 |
| Scientific computation                      | Rowan SDK, Tamarind Bio MCP                              | No                 |
| Zotero                                      | Local API or compatible citation skill                   | No                 |
| Document and spreadsheet generation         | Python-based artifact tools and Agent Skills             | No                 |
| Persistent memory                           | Supermemory, if approved                                 | Optional           |
| Scheduled work                              | OpenChamber Scheduled Tasks                              | No                 |
| Visual planning                             | Plannotator                                              | Yes                |
| Usage monitoring                            | Context Inspector, Resource Monitor, optionally WakaTime | Yes, selectively   |

This architecture does not replicate ChatGPT's private plugin installation state or OAuth sessions. It reconstructs comparable capabilities through supported local tools and separately authenticated services.

For example, installing a dedicated Exa npm plugin would add little value because you already have the Exa MCP and a dedicated Web Researcher agent. It might also introduce another route for automatic search requests, undermining your explicit-call preference.

Supermemory deserves special caution: its current default behavior includes automatic recall and automatic capture. Although it supports `recallMode: "off"`, that setting alone does not necessarily disable every background memory operation. I would defer it until you explicitly want that functionality.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

## 7. Installation and compatibility testing

### OpenCode plugins

For packages without special options, use the documented V2 installer:

```
opencode plugin add @bulga138/redactor
opencode plugin add @tarquinen/opencode-dcp@3.2.0

# Inspect plugin registration
opencode plugin list

# Inspect built-in plugins
opencode plugin list --builtin

# Check updates
opencode plugin check

# Verify configuration and MCP state
opencode debug config
opencode mcp list
```

Do not run both `plugin add` and a separate manual registration for the same package. Use one registration method to avoid confusion.

For Plannotator's manual options, edit the `plugins` array as shown earlier.

Then test from both OpenCode CLI and OpenChamber Desktop, making sure they use the expected OpenCode server and load the same global configuration.

### OpenChamber extensions

Open Settings → Integrations for the official Excalidraw and Resource Monitor cards.

For community extensions, use the [OpenChamber extension directory](https://openchamber.dev/extensions/?utm_source=chatgpt.com), inspect the maintained repository, and follow the extension's installation instructions under Settings → Extensions.

Run a simple task with each extension and verify that it has not enabled unwanted tools, started unexpected background services, or gained permissions beyond what you intended.

### Interactive verification checklist

Acceptance checklist

0 / 10

OpenCode V2 discovers all configured plugins

Plannotator works only when explicitly invoked

REDACTOR passes a synthetic-secret test, if installed

DCP improves a representative coding benchmark, if installed

All nine MCP servers remain disconnected after startup

Plugins do not silently register or activate additional MCP servers

OpenChamber loads the expected OpenCode backend

Context Inspector and Resource Monitor display useful data

Any extension with filesystem or execution privileges has been reviewed

OpenCode CLI and OpenChamber both retain approval controls

## 8. Final recommended stack

## OpenCode V2 + OpenChamber Desktop

The configuration I would actually deploy for your requirements.

OpenCode plugins

| Default                | Plannotator (manual)     |
| ---------------------- | ------------------------ |
| After security testing | REDACTOR                 |
| After benchmarking     | Dynamic Context Pruning  |
| Optional analytics     | WakaTime                 |
| CLI notifications      | Notifier, only if needed |

OpenChamber extensions

| Recommended       | Excalidraw, Resource Monitor, Context Inspector, Skills Manager, Open With, Makefile |
| ----------------- | ------------------------------------------------------------------------------------ |
| Project-dependent | Kanban, OpenSpec, Docker, GitHub Task Board                                          |

Existing ecosystem

| Agents            | Retain all 10 existing custom agents              |
| ----------------- | ------------------------------------------------- |
| MCP               | Retain nine integrations, all disabled at startup |
| Invocation policy | Manual activation and per-tool approval           |
| Memory            | No external memory plugin initially               |

### Final assessment

The best enhancement to your current environment is not a large collection of automatically operating plugins. It is a carefully chosen set of V2-native plugins for planning, privacy and context management, combined with OpenChamber extensions that improve monitoring, file workflows and project management.

I would prioritize Plannotator, Context Inspector, Resource Monitor, Skills Manager, Open With, and Makefile first. Then test REDACTOR and DCP independently. This gives you meaningful new capabilities while preserving your manually controlled Exa, Context7, and other MCP connections.

The research above establishes documented compatibility, configuration formats, and stated limitations. It does not establish successful runtime testing of every third-party plugin against your exact installed OpenCode/OpenChamber versions. That remains the final acceptance requirement before treating the configuration as production-ready.
