# Mathematics and numerical methods research

## Capabilities and boundaries

`/math-research` and `/numerical-research` use the existing `deep-research` agent with a shared math wrapper/router and focused skills. The first command emphasizes mathematical questions, literature, symbolic computation, and proofs. The second emphasizes accuracy, stability, convergence, conditioning, solver selection, and reproducible experiments. Both can combine these lanes.

The suite provides workflows and runnable local experiments, not a claim of general theorem-proving ability or research validation. A successful execution, a passed declared check, a symbolic identity under assumptions, a rigorous enclosure, and a formally checked theorem are different outcomes. Report them separately.

| Environment | Intended tools |
|---|---|
| Python 3.13 | NumPy, SciPy, SymPy, mpmath, python-flint, CVXPY, Matplotlib, JupyterLab |
| SageMath | Exact algebra, number theory, combinatorics, and graphs |
| SUNDIALS | Official Python bindings for stiff ODE, DAE, and nonlinear solvers |
| Lean | Lean 4, Lake, matching mathlib |
| PDE/HPC | FEniCSx, Gmsh, PETSc, SLEPc, compatible MPI |
| JAX | CPU JIT in the Python profile; CUDA 12 GPU JIT in the separate `jax-cuda` profile | Pin `0.12.0.1` requires Python 3.12 or newer; recheck the pin when changing interpreter versions.
| CUDA | CUDA development tools, CuPy, CUDA-enabled PETSc; CDI runs disable SELinux labels for GPU access |

Actual availability is determined by the installed environment manifest and doctor results. A profile definition or built image alone does not demonstrate successful execution.

`doctor` reports missing CPU profiles; use `--cuda` to include GPU profiles and run GPU smoke checks. The PETSc-CUDA profile disables GPU-aware MPI because its Open MPI build is not GPU-aware; it does not establish GPU-aware distributed communication. GPU access disables SELinux labeling for those containers.

On this machine, the complete verified installation is in `$HOME/.local/share/opencode/math-research-final`. Pass `--state-dir "$HOME/.local/share/opencode/math-research-final"` to the launcher to use it. The default `math-research-v2` state is incomplete.

## Install and inspect

Install the configuration using the existing `install.sh` preview/apply process. It carries complete skill directories, including the math launcher and environment assets. It does not implicitly install the computational stack.

From this checkout, run the deterministic stack installer in a terminal:

```sh
python3 skills/math-research/scripts/math_research.py setup --profile all --cuda
python3 skills/math-research/scripts/math_research.py setup --apply --profile all --cuda
```

The first command previews setup. The second applies it. Python profiles use Python 3.13 as requested. Specialist images may carry their own compatible interpreter; record the actual interpreter versions. For a global skill installation, replace the script with the absolute path under the installed `math-research` skill. Keep the working directory in the research project. Runtime state belongs under `${XDG_DATA_HOME:-$HOME/.local/share}/opencode/math-research-v2`; research artifacts belong in the research project, not the global configuration directory. The prior state remains under `math-research`.

The installer calls local package managers, Podman, compilers, and test programs directly. It makes **no model, agent, MCP, or AI API calls**. Its downloads, builds, precompilation, and local checks therefore use no LLM tokens when run directly from the terminal. Planning, code generation, and requested AI troubleshooting still use tokens. Installation logs remain on disk; do not stream large build logs into a model conversation. Failure produces a nonzero exit and diagnostics rather than an AI repair loop.

Setup must preserve matching completed stages, reuse downloads/image layers, and resume without implicit upgrades. Lock files, image digests, source revisions, and resolved package versions are evidence. Changing a dependency requires an explicit upgrade and renewed checks.

Inspect capabilities before research:

```sh
python3 skills/math-research/scripts/math_research.py doctor --offline
python3 skills/math-research/scripts/math_research.py doctor --smoke
```

Offline inspection and actual computation checks serve different purposes. Missing or blocked required profiles must be reported, never silently replaced by CPU or a different library.

### CUDA prerequisites

The machine has an RTX 2080 Ti with 11 GiB VRAM. Read-only checks outside the sandbox succeeded with NVIDIA driver 615.78.08, Podman 5.8.9, and available CDI devices. Earlier sandbox failures did not establish a host driver fault. These host checks do not establish that every computational image or GPU experiment passes; retain the separate container and scientific checks.

CUDA libraries and development tools run inside rootless Podman containers. A functioning compatible NVIDIA driver and Container Toolkit/CDI remain host prerequisites. Do not automatically replace drivers, change kernel modules, disable SELinux, or run privileged containers. Expose only the selected GPU using CDI. An SELinux labeling exception, if required, needs explicit review.

The compatibility starting point is CUDA 12.8.1 with the detected Turing GPU. The entire actual combination must be checked and locked: image, compiler, toolkit libraries, GPU architecture, driver compatibility, CuPy and PETSc. Resolve all package artifacts during setup; computations must not fetch missing libraries. GPU matrix/vector types and device identity must be checked to prevent CPU fallback from passing GPU tests.

Default execution limits are four CPUs, 8 GiB host RAM, 256 processes, and no network. Setup, smoke checks, normal runs, and benchmarks have separate budgets. VRAM budgets are application checks, not hard isolation; host memory cgroups do not cap GPU allocations. Serialize GPU benchmarks and preserve allocation failures.

## Research workflow

1. Establish the question, deliverable, assumptions, domain, notation, units, exact versus approximate inputs, and resource budget.
2. Select one to three focused skills. Use literature retrieval only where needed; reuse timestamped approved records when inputs and freshness requirements are unchanged.
3. Define checks before execution: reference quality, error norm, tolerances, expected invariant or convergence behavior, and solver applicability.
4. Select a verified environment. Use explicit local model files, preserve all executed sources and hashes, and never execute retrieved code automatically.
5. Run in a new `research/math/` directory. Retain failed runs and logs. Rerunning creates a new directory; verification reads existing artifacts without recomputing.
6. Report observed results, check status, scientific limitations, and any remaining proof or validation obligations.

The launcher exposes `run --input <JSON> --output-dir <new-directory>`, `verify --run-dir <directory>`, and `benchmark --input <JSON> --output-dir <new-directory>`. Consult its `--help` and bundled example inputs for supported backend fields and experiment identifiers. Do not invent JSON fields or infer arbitrary-code safety from a filename. Execute sources through explicit argument lists, not shell interpolation or unrestricted expression evaluation.

For example, after choosing a bundled input or preparing a reviewed model:

```sh
python3 /absolute/path/to/math_research.py run \
  --input /absolute/path/to/experiment.json \
  --output-dir research/math/run-001
python3 /absolute/path/to/math_research.py verify \
  --run-dir research/math/run-001
```

Keep input, assumptions, citations and source locators, model hashes, environment identifiers, commands, tolerances, precision, solver stopping reasons, diagnostics, plots, timings, and limitations. Separate execution completion from declared scientific checks and from mathematical certification. An output hash verifies integrity, not truth.

## Numerical verification and examples

For standalone installation followed by all acceptance checks, run `bash skills/math-research/scripts/install_all.sh` from the checkout. It waits for an existing setup operation, installs all CPU/CUDA profiles, then writes a fresh acceptance report under the runtime state directory. It invokes no AI service and needs no model-driven polling. Downloads, builds, and local computation still consume bandwidth, disk, CPU/GPU time, and power.

This machine's installation was started through the user service `opencode-math-install.service`. Inspect it outside an AI session with `systemctl --user status opencode-math-install.service` or `journalctl --user -u opencode-math-install.service`. Per-profile build logs and `setup-summary.json` live under `$HOME/.local/share/opencode/math-research-v2/`. A running service is not evidence that installation or scientific checks passed.

After setup, run the complete local acceptance suite from the checkout. This script invokes no models or remote research providers; all diagnostics and per-case logs remain on disk. Choose a new output directory for each invocation:

```sh
python3 skills/math-research/scripts/acceptance.py \
  --state-dir "$HOME/.local/share/opencode/math-research-v2" \
  --output-dir research/math/acceptance-001 --cuda
```

The suite executes the bundled cases and checks their preserved artifacts. Missing required environments and failed checks produce a nonzero exit code. `verify` checks artifact integrity and recorded experiment reports; it does not rerun numerical computations or establish mathematical truth.

The acceptance design includes these complementary examples:

- Symbolic identity with domain assumptions and an out-of-domain counterexample.
- Sage exact factorization with reconstruction.
- Lean theorem with axiom output and a rejected incomplete proof.
- Stiff ODE in SciPy against an analytic solution, with Robertson work–precision analysis.
- Manufactured Poisson solution with four refinements and measured L2/H1 rates.
- Convex optimization with known solution/KKT checks and an integer problem with known optimum.
- Sparse systems with known solutions, residuals, backward/forward error, and preconditioner comparisons.
- Quadrature/interpolation refinement and cancellation analysis using high precision and Arb.

CUDA checks cover compiled kernels, Compute Sanitizer for each bundled custom kernel, CuPy matrix multiplication and normalized FFT reconstruction, sparse solves, and PETSc CUDA matrix/vector types. These checks establish only the tested cases. Do not promise speedup or whole-program GPU execution.

Convergence studies must distinguish discretization, iterative, sampling, and roundoff error. Small residuals do not imply small forward error in ill-conditioned problems. High precision is not a rigorous bound; Arb certification requires valid enclosures throughout the relevant computation. Lean checking requires a reviewed theorem statement and axiom audit, with `sorryAx` and unexpected axioms rejected.

Benchmarks separate compilation, warmup, data transfers, kernels, and total runtime. Synchronize GPU operations before timing. Record hardware, thread counts, seeds, precision, achieved accuracy, repeated timings, and peak observed memory. Correctness tests must not depend on unstable timing thresholds.

Synthetic fixtures are the deterministic baseline. The SuiteSparse Matrix Collection reported unavailable matrix downloads during planning on 2026-11-05; recheck service status before requesting files, cache downloads once, and preserve provenance/license details.

## Sources and authorization

Use the existing academic/deep-research workflows for screening and citation verification. arXiv papers may be preprints. zbMATH API terms apply. DLMF identities require equation locators and branch/domain conditions; OEIS matches require definitions and offsets; LMFDB objects require labels and reliability qualifications. Finite matching examples never establish a theorem.

No new MCP server or permission grant is required by this suite. Existing per-call authorization rules remain in force. Paid compute, remote services, privileged host changes, publication, and account changes require their own authorization.

Primary documentation used during planning:

- [SciPy](https://docs.scipy.org/doc/scipy/tutorial/), [SymPy parsing warning](https://docs.sympy.org/latest/modules/parsing.html), [SageMath](https://doc.sagemath.org/).
- [SUNDIALS](https://computing.llnl.gov/projects/sundials/sundials-software), [CVXPY](https://www.cvxpy.org/), [Python-FLINT](https://python-flint.readthedocs.io/en/latest/).
- [Lean proof verification](https://leanprover-community.github.io/did_you_prove_it.html), [Lean projects](https://leanprover-community.github.io/install/project.html).
- [FEniCSx installation](https://docs.fenicsproject.org/dolfinx/main/python/installation.html), [PETSc GPU support](https://petsc.org/release/overview/gpu_roadmap/).
- [NVIDIA CDI](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html), [CUDA 12.8.1](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-toolkit-release-notes/index.html), [CuPy](https://docs.cupy.dev/en/stable/install.html).
- [arXiv API](https://info.arxiv.org/help/api/user-manual.html), [DLMF](https://dlmf.nist.gov/), [OEIS](https://oeis.org/wiki/Welcome), [LMFDB](https://www.lmfdb.org/), [SuiteSparse matrices](https://sparse.tamu.edu/).
