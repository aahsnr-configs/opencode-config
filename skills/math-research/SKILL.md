---
name: math-research
description: Coordinate reproducible pure mathematics, numerical methods, and local CUDA research with explicit assumptions, checked computations, and preserved evidence.
---

# Mathematics research

Load `math-research-router` for broad questions, then the smallest relevant focused skill. Use `math-literature` for reference discovery and `numerical-verification` for accuracy or performance claims. Computation, symbolic simplification, and formal proof are different evidence types.

Resolve domains, assumptions, units, precision, tolerances, boundary conditions, and requested deliverables before executing. Run helpers by absolute path from the research project. Never change into the installed skill directory to create research outputs.

The standard-library launcher is `scripts/math_research.py`, relative to this skill. The Python and CuPy profiles use Python 3.13; specialist images retain their internally compatible interpreters. Run `setup` to preview; run `setup --apply --profile all --cuda` directly in a local terminal to install. Installation invokes no model, agent, AI API, or MCP. Its local package downloads and builds consume no LLM tokens. Asking a model to inspect or repair installation still consumes tokens. Setup logs and a machine-readable summary remain in the selected state directory. It never changes host GPU drivers.

Use `doctor --offline` for recorded installation state and `doctor --smoke` for actual container computations. A recorded image is not scientific validation. Missing or blocked CUDA prerequisites are failures, not CPU successes.

`run --input experiment.json --output-dir research/math/new-run` accepts a bundled experiment name or an explicit local source file. Read the launcher help and example manifests for the input contract. Review local model code before execution. No downloaded code is executed automatically. Containers receive selected copied inputs and a new output directory, no home directories, sockets, credentials, or network. The runtime is isolation, not a guarantee against malicious kernels or drivers.

Every run retains copied source, hashes, the input request, environment identity, command, diagnostic logs, scientific checks, and limitations. Existing paths and symlink ancestors are refused. `verify --run-dir ...` checks the preserved artifact hashes and declared check results without rerunning code or independently recomputing mathematical checks. It does not prove arbitrary models correct. Failed runs remain available; reruns require a new directory.

Initial setup resolves image tags and exports their immutable digests, built image IDs, and complete package snapshots into runtime state. These are installation-specific locks, not a claim that fresh dependency resolution is bit-for-bit reproducible. Subsequent setup reuses matching images and never upgrades them implicitly. Use `setup --apply --rebuild` in a new state directory to rebuild selected images without cached layers and repeat smoke checks. A changed environment definition requires a new state directory so earlier results remain reproducible.

For GPU work load `cuda-computing`. Record actual device and backend types, synchronize timings, separate transfers and compilation, and compare accuracy against an appropriate reference. Runtime host-memory limits do not impose GPU VRAM limits.

The suite grants no MCP, model, paid-compute, publication, or account authorization. Follow AGENTS.md. Use the existing deep-research agent for approved execution; never bypass edit or MCP policy through shell commands.
