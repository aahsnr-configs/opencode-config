"""PETSc CUDA backend types and known-solution CG acceptance."""
import json
import math
from pathlib import Path
from petsc4py import PETSc

n = 256
matrix = PETSc.Mat().create(comm=PETSc.COMM_SELF)
matrix.setSizes([n,n])
matrix.setType("aijcusparse")
matrix.setPreallocationNNZ(3)
for i in range(n):
    columns = list(range(max(0,i-1), min(n,i+2)))
    matrix.setValues(i,columns,[2. if j == i else -1. for j in columns])
matrix.assemble()
truth = PETSc.Vec().create(comm=PETSc.COMM_SELF)
truth.setSizes(n)
truth.setType("cuda")
truth.setValues(list(range(n)),[math.sin(i+1) for i in range(n)])
truth.assemble()
rhs, answer = truth.duplicate(), truth.duplicate()
matrix.mult(truth,rhs)
solver = PETSc.KSP().create(comm=PETSc.COMM_SELF)
solver.setOperators(matrix)
solver.setType("cg")
solver.getPC().setType("jacobi")
solver.setTolerances(rtol=1e-11, atol=1e-13, max_it=2000)
solver.solve(rhs,answer)
error = answer.copy()
error.axpy(-1.,truth)
relative_error = error.norm()/truth.norm()
residual = rhs.duplicate()
matrix.mult(answer,residual)
residual.axpy(-1.,rhs)
relative_residual = residual.norm()/rhs.norm()
matrix_type, vector_type = matrix.getType(), answer.getType()
checks = [{"name": "actual_cuda_backend", "passed": "cusparse" in matrix_type and "cuda" in vector_type},
          {"name": "cg_converged", "passed": solver.getConvergedReason() > 0},
          {"name": "known_solution", "passed": relative_error < 1e-7 and relative_residual < 1e-9}]
metrics = {"matrix_type": matrix_type, "vector_type": vector_type, "solver": solver.getType(), "preconditioner": solver.getPC().getType(), "converged_reason": solver.getConvergedReason(), "iterations": solver.getIterationNumber(), "relative_error": relative_error, "relative_residual": relative_residual, "analytic_condition_2": (1+math.cos(math.pi/(n+1)))/(1-math.cos(math.pi/(n+1)))}
Path("/output/experiment.json").write_text(json.dumps({"checks": checks, "metrics": metrics, "limitations": ["Tests PETSc GPU algebra only; it does not establish GPU finite-element assembly or GPU support in every preconditioner."]}, indent=2)+"\n")
raise SystemExit(0 if all(c["passed"] for c in checks) else 1)
