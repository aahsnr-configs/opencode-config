# Scientific Tools and Software Inventory

**Scope:** Tools and software currently defined in this repository for life-sciences, mathematics/numerical methods, and physics/molecular simulation. This is a source inventory, not a claim that every environment is installed or passing on a particular machine. Environment definitions and installed versions can differ; check each workflow's manifests, locks, and acceptance results.

## Shared workflow and compute layer

- **OpenCode / OpenChamber:** commands and skills route research requests to local scripts and domain tools.
- **Research entry points:** `/life-science`, `/math-research`, `/numerical-research`, `/physics-research`, and `/molecular-dynamics`; math and physics reuse the `deep-research` workflow where appropriate.
- **Python:** life-sciences helpers require Python 3.11+; math profiles use Python 3.13.5; physics profiles use Python 3.13 on Debian Trixie.
- **Podman:** rootless containers isolate numerical and simulation environments. Math and physics setup scripts build profiles, preserve logs and package records, and run declared smoke/acceptance checks.
- **CUDA and NVIDIA CDI:** CUDA 12.8.1 is the configured GPU baseline. A compatible host NVIDIA driver and Container Toolkit/CDI are prerequisites. GPU profiles select devices through CDI.
- **Package/build tools:** pip and `uv` install Python dependencies; Debian/Ubuntu APT installs system packages; Make, CMake, compilers, and Git build selected scientific software from source. The math/physics stacks do not use Conda.
- **Optional literature management:** Zotero can connect through the local research-tools bridge. It is disabled by default and is not a compute dependency.
- **No Julia:** Julia is not part of the current math or physics stack.

## Life-sciences research

### Runtime and integration model

- Pinned upstream source: public OpenAI Life Science Research plugin **1.0.3**, commit `0722921d5542fc593105c27bd52630babd8b8c2a`; the checkout contains all **50** skill directories.
- Python API helpers use `requests>=2.32.5,<3`. `matplotlib>=3.9,<4` is optional for locus-to-gene plots. These are bounded requirements, not a complete transitive lock.
- Skills call public source APIs directly. This bundle does not add an MCP server.
- Supplementary `life-sciences/lookup.py` supports Europe PMC search and AlphaFold metadata lookup.
- Hosted GPT-Rosalind/Workbench features, STAR/GATK/Nextflow pipelines, and paid or commercial services are outside this integration.

### Included source/API skills

**Research routing, literature, and trials:** `research-router-skill`, `biorxiv-skill`, `clinicaltrials-skill`, `ncbi-entrez-skill`, `ncbi-pmc-skill`, `ncbi-clinicaltables-skill`.

**Genomes, expression, and biological data:** `biostudies-arrayexpress-skill`, `bgee-skill`, `cellxgene-skill`, `efo-ontology-skill`, `encode-skill`, `ensembl-skill`, `eva-skill`, `mgnify-skill`, `ncbi-blast-skill`, `ncbi-datasets-skill`, `rnacentral-skill`.

**Human genetics, variants, and associations:** `biobankjapan-phewas-skill`, `cbioportal-skill`, `clinvar-variation-skill`, `epigraphdb-skill`, `eqtl-catalogue-skill`, `finngen-phewas-skill`, `genebass-gene-burden-skill`, `gnomad-graphql-skill`, `gtex-eqtl-skill`, `gwas-catalog-skill`, `locus-to-gene-mapper-skill`, `tpmi-phewas-skill`, `ukb-topmed-phewas-skill`.

**Proteins, structures, and pathways:** `alphafold-skill`, `human-protein-atlas-skill`, `ipd-skill`, `quickgo-skill`, `rcsb-pdb-skill`, `reactome-skill`, `string-skill`, `uniprot-skill`.

**Chemistry, drugs, and targets:** `bindingdb-skill`, `chebi-skill`, `chembl-skill`, `civic-skill`, `hmdb-skill`, `opentargets-skill`, `pharmgkb-skill`, `pubchem-pug-skill`, `rhea-skill`.

**Proteomics and metabolomics archives:** `metabolights-skill`, `pride-skill`, `proteomexchange-skill`.

See [life-sciences source scope and setup](docs/LIFE-SCIENCES.md), [upstream file/version lock](life-sciences/upstream-lock.json), and [runtime requirements](life-sciences/requirements.txt).

## Mathematics and numerical methods

### Environment profiles

| Profile | Main tools and software | Source/version detail |
|---|---|---|
| `python` | NumPy, SciPy, SymPy, mpmath, python-flint, CVXPY, Matplotlib, JupyterLab, JAX CPU/JIT | Python 3.13.5 slim Bookworm; direct versions are pinned in `skills/math-research/environments/python.requirements.txt` |
| `sage` | SageMath for exact algebra, number theory, combinatorics, and graphs | `sagemath/sagemath:10.6` |
| `lean` | Lean 4, Lake, mathlib; elan installs and selects the toolchain | Lean/mathlib `v4.19.0`; elan `v4.1.2` |
| `sundials` | SUNDIALS Python bindings for ODE, DAE, and nonlinear solvers | `sundials4py==7.9.0`; uses the Python profile base |
| `fenics` | FEniCSx/DOLFINx, Gmsh, PETSc/petsc4py, SLEPc/slepc4py, mpi4py/MPI | DOLFINx `stable` image; records component versions during setup |
| `cuda` | NVIDIA CUDA development image and CuPy | CUDA `12.8.1`; `cupy-cuda12x==13.4.1` |
| `jax-cuda` | JAX compiled GPU execution with CUDA 12 plugin | `jax[cuda12]==0.12.0.1`; built on the Python profile |
| `petsc-cuda` | CUDA-enabled PETSc and petsc4py | PETSc `3.23.2`, CUDA architecture 75 (Turing); GPU-aware MPI is disabled |

### Direct Python package pins

- **Core Python profile:** `numpy==2.2.6`, `scipy==1.15.3`, `sympy==1.14.0`, `mpmath==1.3.0`, `python-flint==0.8.0`, `cvxpy==1.6.5`, `matplotlib==3.10.3`, `jupyterlab==4.4.3`, `jax==0.12.0.1`.
- **JAX CUDA profile:** `jax[cuda12]==0.12.0.1`.
- **Build/bootstrap:** `uv==0.7.13`; PETSc CUDA profile also uses Cython, wheel, Open MPI, GFortran, and build tools.

### Research data and reference resources

The workflows use or cite the **arXiv API**, **zbMATH API**, **NIST Digital Library of Mathematical Functions (DLMF)**, **OEIS**, **LMFDB**, and **SuiteSparse Matrix Collection**. These are research sources/data collections, not packages installed in the local compute images. Preserve source locators, versions, and download provenance when using them.

See [math workflow and validation boundaries](docs/MATH-RESEARCH.md), [profile definitions](skills/math-research/scripts/math_research.py), and the files under `skills/math-research/environments/`.

## Physics and molecular simulation

### Shared environment

- **Base images:** `docker.io/library/python:3.13-slim-trixie`; CUDA build stages use `docker.io/nvidia/cuda:12.8.1-devel-ubuntu22.04`.
- **General stack:** Python 3.13, pip/PyPI dependencies, Debian packages, rootless Podman, CMake, Make, G++, and selected Fortran/Git packages. Open MPI is used by the math PETSc CUDA profile, not the physics profiles.
- **Python scope:** Python 3.13 comes from the container image; no host-wide Python installation is required. Physics uses Debian Trixie as its runtime base and Ubuntu 22.04 only for CUDA build stages. Changing the runtime base requires checking distro-native packages and Python bindings.
- **GPU baseline:** CUDA 12.8.1 and Turing SM75 configuration. GPU variants are explicit profiles; they do not silently fall back to CPU.
- **Build/source tools:** source recipes use CMake, shared PLUMED, and selected engine build systems. The current physics recipes disable MPI for GROMACS/LAMMPS source builds.

### Simulation and analysis profiles

| Profile | Main tools and software |
|---|---|
| `analysis` | NumPy 2.2.6, SciPy 1.15.3, SymPy 1.14.0, ASE 3.29.0, pymatgen 2026.9.24, spglib 2.6.0, seekpath 2.2.2, Phonopy 4.8.6, MDAnalysis 2.11.0, PyMBAR 4.0.3 with JAX extra, Matplotlib 3.10.8 |
| `pymbar-cuda` | PyMBAR 4.0.3 with JAX extra, JAX CUDA 12 (`0.12.0.1`), NumPy 2.2.6, SciPy 1.15.3 |
| `preparation` | OpenFF Toolkit 0.19.0, OpenFF Utilities and Force Fields source pins, openff-units 0.3.2, RDKit 2025.9.4, OpenMM 8.4.0, NetworkX 3.4.2, cachetools 5.5.2, xmltodict 0.14.2, python-constraint 1.4.0, packaging 25.0 |
| `openmm` | OpenMM 8.4.0 for programmable biomolecular/custom-force molecular dynamics |
| `gromacs` | GROMACS 2025.3 built from source, NumPy 2.2.6, PLUMED 2.10.2, FFTW |
| `lammps` | LAMMPS `stable_22Jul2025_update3` built from source, NumPy 2.2.6, PLUMED 2.10.2; Kokkos/CUDA in GPU variant |
| `hoomd` | HOOMD-blue 5.2.0 built from source, NumPy 2.2.6, pybind11 2.13.6 |
| `qe` | Quantum ESPRESSO from Debian packages; QE 7.4.1 silicon pseudopotential fixture |
| `cp2k` | CP2K and CP2K data from Debian packages |
| `pyscf` | PySCF 2.11.0 for molecular electronic structure |
| `quantum` | QuTiP 5.2.3 and physics-tenpy/TeNPy 1.1.1 |
| `kwant` | Kwant 1.5.0 with G++, Python headers, GFortran, OpenBLAS, and LAPACK |

CUDA variants are `openmm-cuda`, `gromacs-cuda`, `lammps-cuda`, and `hoomd-cuda`; `pymbar-cuda` is the GPU analysis profile. GROMACS, LAMMPS, PLUMED, and HOOMD use source builds. PLUMED is pinned to commit `90dec6d6ebf97ad5f2580e50e563b70c1728c4e6`, the `v2.10.2` release commit. A shared build recipe cleans temporary source/build trees from source-built images.

The preparation profile pins OpenFF Utilities to commit `4fc551250f568b86d42555d3108d34e4868376b6` and OpenFF Force Fields to commit `1a4063b18a16636833a0f0f0a119a9d741cf3c61`.

### Coverage by physics field

| Field | Configured tools | What they support |
|---|---|---|
| Molecular dynamics and biophysics | OpenMM, GROMACS, PLUMED, OpenFF Toolkit, RDKit, MDAnalysis, PyMBAR | Biomolecular and atomistic simulation, force-field preparation, trajectory analysis, enhanced sampling, and free-energy analysis |
| Condensed matter and materials physics | Quantum ESPRESSO, CP2K, ASE, pymatgen, spglib, seekpath, Phonopy, LAMMPS, HOOMD-blue, Kwant, TeNPy | Periodic electronic structure, crystal/materials data, symmetry and Brillouin-zone paths, phonons, atomistic/coarse-grained models, quantum transport, and tensor-network models |
| Quantum mechanics | PySCF, Quantum ESPRESSO, CP2K, QuTiP, TeNPy, Kwant | Molecular and periodic electronic structure, quantum dynamics, tensor-network models, and quantum transport |
| Classical mechanics and molecular simulation | GROMACS, LAMMPS, HOOMD-blue, OpenMM, SciPy, SUNDIALS | Particle and molecular dynamics plus numerical ODE/DAE integration |
| Lagrangian and Hamiltonian mechanics | SymPy Mechanics, SciPy, SUNDIALS | Symbolic equations of motion through SymPy Mechanics; numerical ODE/DAE integration. No separate Hamiltonian-mechanics engine is configured. |

These are workflow capabilities, not claims that every profile is installed or that a scientific model has been validated. SymPy Mechanics and the numerical methods profiles come from the shared math stack.

### System package families

The profile recipes use Debian/Ubuntu packages including `cmake`, `g++`, `make`, `git`, `pkg-config`, `libfftw3-dev`, `libeigen3-dev`, `gfortran`, `python3-dev`, `libopenblas-dev`, `liblapack-dev`, `quantum-espresso`, `cp2k`, and `cp2k-data`. Base image packages include Python/pip/venv, certificates, GSL, BLAS, and LAPACK. Resolved package inventories are recorded per build; unpinned distribution package versions can vary with repository snapshots.

See [physics workflow and profile scope](docs/PHYSICS-RESEARCH.md), [Python/APT/source pins](skills/physics-research/scripts/physics_research.py), and [source-build recipe](skills/physics-research/environments/source_build.sh).

## Reading this inventory

This file summarizes repository definitions. It does not certify that images built, GPU devices were used, APIs were available, or scientific results passed review. Check the domain setup summaries and acceptance reports for a particular machine and run. Primary workflow docs: [life-sciences](docs/LIFE-SCIENCES.md), [math research](docs/MATH-RESEARCH.md), and [physics research](docs/PHYSICS-RESEARCH.md).
