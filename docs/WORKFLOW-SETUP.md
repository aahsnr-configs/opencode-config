# Project workflow setup

## Memory and agents

Use `/memory` to review or update `PROJECT-MEMORY.md` in the current project. The file is ordinary project data and can persist across sessions. Do not put credentials in it. Review it before sharing or committing it. The global guidance requests reading an existing file when relevant; this depends on the agent following that guidance.

For cross-project preferences, [Supermemory's OpenCode plugin](https://github.com/supermemoryai/opencode-supermemory) is configured at `2.0.17`. Its global profile provides cross-project context; project memories are scoped to a repository container. Its cloud integration captures conversation batches automatically, and setting `captureEveryNTurns` to `0` still captures remaining turns at session end. Its optional codebase indexing is separately invoked. See [the capture implementation](https://github.com/supermemoryai/opencode-supermemory/blob/main/src/services/capture.ts) and the provider's [privacy policy](https://supermemory.ai/privacy/). Plugin hooks can write automatically without individual agent tool prompts. Authentication and usage limits are separate from OpenCode; follow the plugin's login instructions after installing the configuration.

The `coder` agent selects `openai/gpt-6.1-terra#medium`; `explore-scout` and `web-researcher` use Luna, and `sol-advisor` uses `openai/gpt-6.1-sol#high`. Model availability and variants depend on the provider account. Obtain prior approval for each subagent call. Web research through the configured `web-researcher` also requires the explicit Exa authorization in [FOUR-AGENTS.md](FOUR-AGENTS.md).

## Plugins and Git

Superpowers is configured at tag `v7.0.2` in `opencode.jsonc`. OpenCode must download and load it on startup; installing this configuration does not prove that has succeeded. See the [upstream installation guide](https://github.com/obra/superpowers/blob/main/.opencode/INSTALL.md).

Caveman's OpenCode skills and plugin are separately installed in this machine's global OpenCode configuration. Its ancillary plugins have reported OpenCode V2 compatibility issues; verify actual behavior before relying on them. See [Caveman installation](https://docs.caveman.so/caveman/installation) and [compatibility report](https://github.com/JuliusBrussee/caveman/issues/1246).

RTK is installed as a separate binary. The OpenCode rewrite plugin has not been installed by this repository. `rtk init --global --opencode --dry-run --no-patch --no-trust-filters` previews the installed version's changes. The preview also lists Claude configuration changes, so review it before running without `--dry-run`. Restart OpenCode and verify rewriting after installation. See [RTK's supported agents guide](https://github.com/rtk-ai/rtk/blob/develop/docs/guide/getting-started/supported-agents.md).

For compact Git inspection, RTK provides `rtk git` and `rtk gh`; `/git-inspect` invokes the existing read-only Git agent after approval. Check `rtk git --help` and `rtk gh --help` for supported commands. This uses the installed tool rather than an additional unverified Git plugin.

## Vim

The V2 CLI configuration `cli.json` enables the [OpenCode Vim plugin](https://github.com/leohenon/opencode-vim-plugin) for modal prompt editing. It requires OpenCode 2.0.25 or newer and uses the moving `beta` channel. Use `/vim` to toggle it. It does not provide modal navigation throughout the interface. Plugin download and operation have not been verified in this environment.

OpenCode also supports Vim or Neovim as an external editor: set `EDITOR=vim` or `EDITOR=nvim` in the environment that starts OpenCode, then use `/editor`. See the [OpenCode TUI documentation](https://docs.opencode.ai/docs/tui/).

OpenChamber's published [chat input documentation](https://docs.openchamber.dev/chat-input/) describes keyboard shortcuts but does not document Vim mode. An OpenChamber-specific Vim mode has not been configured or verified.
