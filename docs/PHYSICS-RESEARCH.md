# Physics and molecular simulation research

## Capabilities and evidence

`/physics-research` and `/molecular-dynamics` use the existing deep-research agent, a physics router, and focused scientific skills. The stack covers molecular dynamics, biophysics, condensed matter, quantum systems, and classical/Lagrangian/Hamiltonian mechanics. Existing math profiles supply symbolic mechanics, ODE/DAE solvers, continuum PDEs, sparse solvers, and general CUDA computation. Existing life sciences integrations supply identifiers and source structures.

A profile definition is not an installation claim. A built image, passed smoke check, passed declared scientific fixture, and converged research result are different evidence. Inspect the target machine's manifests and acceptance reports. This document does not claim all environments have been built or validated.

| Profile | Intended tools and role |
|---|---|
| `analysis` | Python 3.13; ASE, pymatgen, spglib, seekpath, Phonopy, MDAnalysis, PyMBAR with its JAX extra, NumPy/SciPy/SymPy, Matplotlib |
| `pymbar-cuda` | PyMBAR with JAX CUDA 12; GPU-device assertion and MBAR free-energy smoke test |
| `preparation` | Python 3.13; official OpenFF source distributions and RDKit |
| `openmm` | Programmable biomolecular and custom-force MD |
| `gromacs` | Biomolecular MD with PLUMED |
| `lammps` | General atomistic/materials MD with PLUMED |
| `hoomd` | Coarse-grained particles and hard-particle Monte Carlo |
| `qe` | Quantum ESPRESSO periodic electronic structure and lattice dynamics, CPU |
| `cp2k` | Molecular/periodic electronic structure and small ab initio MD, CPU |
| `pyscf` | Molecular electronic structure, CPU |
| `quantum` | QuTiP and TeNPy quantum dynamics and tensor-network models, CPU |
| `kwant` | Python 3.13 quantum transport environment, CPU |
| `openmm-cuda`, `gromacs-cuda`, `lammps-cuda`, `hoomd-cuda` | Explicit CUDA variants requiring demonstrated GPU execution |

All physics profiles use the Python 3.13 base image. CUDA build stages supply the toolkit to that same interpreter environment. GROMACS, LAMMPS, PLUMED, and HOOMD use source builds because the distribution packages do not provide the required capabilities. Dependency resolution may fail if a requested combination is unavailable; report that failure instead of silently changing interpreter or method. No Julia is included. Plasma, particle transport, relativity, and astrophysics engines are outside this release. GPU4PySCF and Quantum ESPRESSO/CP2K GPU toolchains are deferred.

## Install and inspect

The configuration installer carries complete skill directories, but does not install computational environments. The physics launcher depends on the neighboring `math-research` skill for shared container/process primitives. Keep both skills installed together.

From this checkout:

```sh
python3 skills/physics-research/scripts/physics_research.py setup --profile all --cuda
python3 skills/physics-research/scripts/physics_research.py setup --apply --profile all --cuda
```

The first command previews profiles, packages, runtime state, and an approximate disk budget. The second installs sequentially. Omit `--cuda` for CPU environments; select one environment with `--profile NAME`. The broad stack can require substantial storage and build time; the preview estimate is not measured disk usage.

Default runtime state is `${XDG_DATA_HOME:-$HOME/.local/share}/opencode/physics-research-v5`. Pass `--state-dir /absolute/path` after the subcommand to select another location. State contains package resolution records, resolved PyPI and dpkg package inventories, image identities, setup summaries, and per-profile logs. Research outputs belong in the research project, not global configuration or runtime state.

Direct PyPI requirements are version-pinned. Setup records the installed transitive PyPI packages and Ubuntu dpkg inventory after each build. A new state directory may resolve different transitive versions as repositories change. Rebuilds reuse the recorded profile definition and installed base image, but reinstall direct requirements from PyPI.

Installation runs local package managers, Podman, compilers, and checks directly. It makes **no model, agent, AI API, or MCP calls**. Terminal installation therefore consumes no LLM tokens; downloads and compilation still consume network, storage, power, and compute. Asking an AI to inspect logs or fix failures uses tokens. Logs remain on disk, and failed required stages produce a nonzero result.

The CUDA baseline is the existing RTX 2080 Ti/Turing system and CUDA 12.8.1. A compatible host driver and NVIDIA Container Toolkit/CDI are prerequisites. The installer does not change host drivers or launch privileged containers. GPU containers use an SELinux labeling exception for device access; review that boundary before execution. Host memory limits do not cap GPU VRAM. GPU execution checks must fail when requested device support is unavailable.

Inspect installation records and actual functionality separately:

```sh
python3 skills/physics-research/scripts/physics_research.py doctor --offline --cuda
python3 skills/physics-research/scripts/physics_research.py doctor --smoke --cuda
```

`--offline` reports recorded installation evidence and local image availability; it does not run a scientific experiment. `--smoke` performs actual profile computations. Neither validates arbitrary models.

For an unattended local terminal run, use a user service with an absolute checkout path and working directory:

```sh
systemd-run --user --unit=opencode-physics-install --collect \
  --property=WorkingDirectory="$PWD" \
  /usr/bin/python3 "$PWD/skills/physics-research/scripts/physics_research.py" \
  setup --apply --profile all --cuda
journalctl --user -u opencode-physics-install.service -f -o cat
```

The journal shows stage status. Detailed build and smoke output remains in `logs/PROFILE.log` under the selected runtime state. For example:

```sh
tail -F "$HOME/.local/share/opencode/physics-research-v5/logs/gromacs-cuda.log"
```

The service makes no background model or MCP calls. A running service is not proof of successful installation; inspect its exit status and `setup-summary.json`.

## Run and preserve experiments

Invoke installed helpers by absolute path while keeping the working directory in the research project. Declare physical assumptions, units, observables, checks, tolerances, seeds, and resource limits before execution. Review explicit model code; do not execute retrieved code automatically.

A bundled request selects its profile and corresponding base experiment name:

```json
{"profile": "openmm", "experiment": "openmm"}
```

For the GPU variant use `{"profile":"openmm-cuda","experiment":"openmm"}` and pass `--cuda`. A reviewed custom Python model uses `{"profile":"analysis","source":"/absolute/path/model.py"}`. The model receives the copied request path as its first argument and writes `experiment.json` in its output working directory. Scientific checks must be a nonempty `checks` array with named boolean results, for example `{"checks":[{"name":"reference_agreement","passed":true}]}`. A successful process without passing declared checks fails the run.

```sh
python3 /absolute/path/skills/physics-research/scripts/physics_research.py run \
  --input /absolute/path/request.json --output-dir research/physics/run-001
python3 /absolute/path/skills/physics-research/scripts/physics_research.py verify \
  --run-dir research/physics/run-001
```

Containers run offline with copied inputs, a new output directory, a read-only root filesystem, reduced capabilities, and bounded CPU/host-memory/process resources. They receive no home directory, credentials, or host sockets. Isolation is not a guarantee against malicious native code, kernels, or drivers. Supporting scientific data must be deliberately prepared in the selected environment or model input design; research runs must not fetch missing libraries or potentials.

Keep source, inputs, assumptions, environment identity, package locks, commands, logs, force fields/pseudopotentials and their hashes/licenses, solver diagnostics, uncertainty, and limitations. Existing output paths and symlink ancestors are refused. Failed runs remain available; reruns require fresh directories. `verify` checks preserved artifact integrity and declared results without rerunning the simulation or independently validating physical truth.

For classical analytical mechanics or continuum models, invoke the existing math launcher and its installed state explicitly. Its output directory can be a new `research/physics/` directory. See [Math Research](MATH-RESEARCH.md).

## Acceptance and scientific checks

Run the bundled profile acceptance cases after installation:

```sh
python3 skills/physics-research/scripts/physics_research.py acceptance \
  --profile all --cuda --output-dir research/physics/acceptance-001
```

Missing required profiles or failed declared checks fail overall acceptance. The report records the tested cases; passing them does not establish every engine feature or scientific workflow. Use `benchmark --input request.json --output-dir research/physics/benchmark-001 --repetitions 3 --warmup 1` for repeated complete runs. Container wall time includes startup and transfers; it is not a kernel time or a speedup claim.

The scientific review standard includes:

- Mechanics: pendulum derivation, oscillator refinement, Kepler angular momentum, and long-time symplectic behavior through existing math tools.
- MD: analytic/finite-difference forces, short NVE timestep studies, restart continuity, and precision-aware CPU/GPU force comparisons. Chaotic trajectories need not match pointwise.
- PLUMED: a known collective variable and a working interface in each selected engine; supported capabilities differ by engine/version.
- Preparation/analysis: topology and atom-map consistency, declared charge/force-field choices, known geometry, periodic boundaries, correlation, and effective samples.
- Quantum models: analytic two-level dynamics, trace/positivity, and small spin chains against exact diagonalization.
- Transport: clean-chain transmission and expected propagating channels.
- Electronic structure: explicit SCF outcomes, force checks, and basis/cutoff/k-point refinement for the requested observable.
- Phonons: finite-displacement/force convergence and acoustic/translational diagnostics.

Use `physics-verification` to distinguish functional smoke coverage from these research-level checks. Document checks not covered by a particular bundled fixture; do not infer them from package availability.

## Sources and authorization

Primary documentation used to select the stack:

- [ASE calculators](https://docs.ase-lib.org/), [Phonopy interfaces](https://phonopy.github.io/phonopy/interfaces.html), [Kwant](https://www.kwant-project.org/doc/).
- [OpenMM](https://docs.openmm.org/latest/userguide/), [GROMACS PLUMED interface](https://manual.gromacs.org/documentation/2025.3/reference-manual/special/plumed.html), [LAMMPS KOKKOS](https://docs.lammps.org/stable/Speed_kokkos.html), [HOOMD-blue](https://hoomd-blue.readthedocs.io/en/stable/).
- [PLUMED interfaces](https://www.plumed.org/doc-v2.10/user-doc/html/index.html), [MDAnalysis](https://www.mdanalysis.org/documentation/), [pymbar correlation analysis](https://pymbar.readthedocs.io/en/latest/timeseries.html).
- [Quantum ESPRESSO build requirements](https://www.quantum-espresso.org/Doc/user_guide/node11.html), [CP2K](https://www.cp2k.org/), [PySCF](https://pyscf.org/user/index.html), [QuTiP](https://qutip.readthedocs.io/en/latest/), [TeNPy](https://tenpy.readthedocs.io/en/latest/).
- [OpenFF Toolkit](https://docs.openforcefield.org/projects/toolkit/en/stable/), [SymPy Lagrangian mechanics](https://docs.sympy.org/latest/modules/physics/mechanics/lagrange.html).

No new MCP server or permission grant is required. Reuse existing research integrations only with their normal explicit authorization. This suite grants no paid-compute, assay, publication, privileged host, or remote-account permissions. External source claims require verified references and appropriate uncertainties.

The revised no-Conda source recipes have passed host checks only. Container builds and scientific acceptance remain pending user authorization. Existing v3 installation records describe the previous recipes and must not be reported as validation of these changes.
