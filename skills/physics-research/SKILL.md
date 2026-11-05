---
name: physics-research
description: Coordinate reproducible local physics research, molecular simulations, and CPU or CUDA experiments with preserved evidence.
---

# Physics research

Load `physics-research-router` for broad questions and `physics-verification` for declared scientific checks. Select only the relevant focused skill and environment.

Resolve the model, assumptions, units, observable, boundary conditions, ensemble, precision, tolerances, and resource budget before computing. Run helpers by absolute path from the research project; create outputs in fresh `research/physics/` directories.

The launcher is `scripts/physics_research.py`, relative to this skill. It depends on the neighboring installed `math-research` skill for container and process primitives. Read [Physics Research](../../docs/PHYSICS-RESEARCH.md) in the checkout for profiles, input examples, installation, and acceptance commands.

`setup` previews; `setup --apply --profile all --cuda` installs directly in a terminal. The installer invokes no model, agent, AI API, or MCP and changes no host GPU drivers. Downloads, builds, and local checks consume no LLM tokens; model-assisted inspection and troubleshooting do. Logs and summaries remain in the selected state directory. `--rebuild` repeats selected builds without cached layers while preserving resolved package locks. Changed definitions require a new state directory.

Use `doctor --offline` to inspect recorded installation evidence and `doctor --smoke` to execute functional checks. Neither establishes correctness of an arbitrary research model. GPU variants require explicit `--cuda` and verified device execution; do not silently substitute CPU.

`run --input request.json --output-dir research/physics/new-run` accepts a supported profile with its bundled experiment or a reviewed explicit Python source. Preserve executed source, inputs, environment and package identities, diagnostics, declared checks, and limitations. Containers receive copied inputs and a new output directory without network, home directories, or credentials. Native scientific executables may be invoked by the reviewed Python model.

`verify --run-dir ...` checks artifact integrity and recorded declared checks without recomputing physics. `acceptance --output-dir ...` executes the bundled profile cases; a failed required profile fails overall acceptance. `benchmark` repeats runs and reports container wall time, which includes startup and transfers.

Reuse the existing math launcher for SymPy, SciPy, SUNDIALS, FEniCSx, PETSc/SLEPc, and CUDA experiments. No Julia is included. All physics profiles require Python 3.13.

Follow AGENTS.md. This skill grants no provider connection, paid compute, publication, privileged host change, or remote-account authorization. Do not automatically execute downloaded code or parameterize missing chemistry by guessing.
