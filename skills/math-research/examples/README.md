# Bundled mathematical experiments

These locally authored examples use no network or downloaded executable research code. The launcher copies each source and its declared support files into a run bundle, records hashes, and mounts them read-only at `/inputs`. Experiments write `experiment.json` and diagnostic artifacts under `/output`. Successful checks establish only the stated acceptance case, not broad scientific validation.

Select a catalog name using the launcher's JSON input. Catalog parameters choose fixed implemented models; they are not expression strings or dynamically evaluated code. All experiments deliberately fail on missing required backends rather than silently switching to CPU or skipping a check.

The stiff ODE case uses the exact reference `[exp(-t), exp(-1000*t)]`, 101 sample times, and a `1e-7` maximum-error threshold. Python also produces a Robertson work–precision table against a tighter Radau numerical reference, explicitly labeled approximate.

The Poisson case uses uniform triangle meshes, homogeneous Dirichlet conditions, exact solution `sin(pi*x)*sin(pi*y)`, and P1 finite elements. It checks the last two refinement rates in L2 and the H1 seminorm. These norms and quadrature settings are retained in the result.

CUDA arithmetic uses float64 explicitly. The vector-add example targets `sm_75` and must compile and pass Compute Sanitizer. The sanitizer report applies only to that kernel. GPU timings synchronize the device; they are illustrative and make no speedup promise. CuPy's pool allocation observation is not a true process-wide peak or hard VRAM limit.

Primary API references:

- [SciPy integration](https://docs.scipy.org/doc/scipy/reference/integrate.html), [linear algebra](https://docs.scipy.org/doc/scipy/reference/sparse.linalg.html), and [optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)
- [CVXPY](https://www.cvxpy.org/) and [SUNDIALS](https://computing.llnl.gov/projects/sundials/sundials-software)
- [DOLFINx manufactured Poisson example](https://docs.fenicsproject.org/dolfinx/main/python/demos/demo_poisson.html)
- [Lean proof validation](https://leanprover-community.github.io/did_you_prove_it.html)
- [Python-FLINT Arb](https://python-flint.readthedocs.io/en/latest/arb.html)
- [CuPy](https://docs.cupy.dev/en/stable/) and [PETSc GPU support](https://petsc.org/release/overview/gpu_roadmap/)
