"""Manufactured Poisson problem; P1 L2/H1 refinement on a unit square."""
import json
import math
from pathlib import Path
import numpy as np
from mpi4py import MPI
from petsc4py import PETSc
import ufl
from dolfinx import fem, mesh
from dolfinx.fem.petsc import LinearProblem

sizes = [8, 16, 32, 64]
errors = []
for n in sizes:
    domain = mesh.create_unit_square(MPI.COMM_WORLD, n, n)
    space = fem.functionspace(domain, ("Lagrange", 1))
    x = ufl.SpatialCoordinate(domain)
    exact = ufl.sin(math.pi*x[0])*ufl.sin(math.pi*x[1])
    forcing = 2*math.pi**2*exact
    trial, test = ufl.TrialFunction(space), ufl.TestFunction(space)
    boundary = mesh.locate_entities_boundary(domain, 1, lambda x: np.ones(x.shape[1], dtype=bool))
    dofs = fem.locate_dofs_topological(space, 1, boundary)
    bc = fem.dirichletbc(PETSc.ScalarType(0), dofs, space)
    dx = ufl.Measure("dx", domain=domain, metadata={"quadrature_degree": 8})
    problem = LinearProblem(ufl.inner(ufl.grad(trial), ufl.grad(test))*dx, ufl.inner(forcing, test)*dx,
                            bcs=[bc], petsc_options_prefix=f"math_{n}_",
                            petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
    numerical = problem.solve()
    numerical.x.scatter_forward()
    difference = numerical-exact
    l2sq = domain.comm.allreduce(fem.assemble_scalar(fem.form(ufl.inner(difference, difference)*dx)), op=MPI.SUM)
    h1sq = domain.comm.allreduce(fem.assemble_scalar(fem.form(ufl.inner(ufl.grad(difference), ufl.grad(difference))*dx)), op=MPI.SUM)
    errors.append([math.sqrt(abs(l2sq)), math.sqrt(abs(h1sq))])
rates = np.log2(np.array(errors[:-1])/np.array(errors[1:]))
checks = [{"name": "l2_order", "passed": bool(np.all((rates[-2:,0] > 1.8)&(rates[-2:,0] < 2.2)))},
          {"name": "h1_seminorm_order", "passed": bool(np.all((rates[-2:,1] > .85)&(rates[-2:,1] < 1.15)))}]
if MPI.COMM_WORLD.rank == 0:
    Path("/output/experiment.json").write_text(json.dumps({"checks": checks, "metrics": {"mesh_sizes": sizes, "errors_l2_h1_seminorm": errors, "rates": rates.tolist(), "solution": "sin(pi*x)*sin(pi*y)", "boundary": "homogeneous Dirichlet", "element": "P1", "quadrature_degree": 8}, "limitations": ["Observed convergence on a smooth manufactured solution is not validation of an arbitrary physical PDE model."]}, indent=2)+"\n")
raise SystemExit(0 if all(c["passed"] for c in checks) else 1)
