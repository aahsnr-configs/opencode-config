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

Official references: [TUI guide](https://dev.opencode.ai/v2/docs/cli/tui/?utm_source=chatgpt.com) · [CLI commands](https://dev.opencode.ai/v2/docs/cli/commands/?utm_source=chatgpt.com) · [Keyboard shortcuts](https://dev.opencode.ai/v2/docs/cli/keybinds/?utm_source=chatgpt.com).
