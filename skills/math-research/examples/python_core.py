"""Deterministic numerical acceptance cases; no network or expression evaluation."""
import json
import math
import os
from pathlib import Path
import sys
import time


def execute(config):
    import numpy as np
    from scipy import integrate, optimize, sparse
    from scipy.sparse import linalg

    name = config.get("experiment", "symbolic")
    checks, metrics, limitations = [], {}, []

    def check(label, passed, **details):
        checks.append({"name": label, "passed": bool(passed), **details})

    if name == "symbolic":
        import sympy as sp
        x = sp.Symbol("x", positive=True)
        identity = sp.simplify(sp.sqrt(x**2) - x)
        check("positive_domain_identity", identity == 0)
        negative = sp.sqrt(sp.Integer(-2)**2) != -2
        check("negative_domain_counterexample", negative)
        metrics.update(domain="x > 0, real", identity="sqrt(x**2) = x", counterexample={"x": -2, "lhs": 2, "rhs": -2})
        limitations.append("Symbolic simplification and finite examples are not a general formal proof.")
    elif name == "stiff_ode":
        times = np.linspace(0, 1, 101)
        exact = np.exp(-np.array([1., 1000.])[:, None] * times)
        errors, curves, samples = {}, [], {}
        for method in ("Radau", "BDF"):
            sol = integrate.solve_ivp(lambda t, y: -np.array([1., 1000.])*y,
                                      (0., 1.), [1., 1.], method=method,
                                      t_eval=times, rtol=1e-8, atol=1e-10)
            error = float(np.max(np.abs(sol.y - exact))) if sol.success else math.inf
            check(method + "_analytic_error", sol.success and error < 1e-7, error=error, threshold=1e-7)
            errors[method] = {"max_error": error, "nfev": sol.nfev, "njev": sol.njev, "nlu": sol.nlu, "message": sol.message}
            samples[method] = sol.y.T.tolist()

        def robertson(t, y):
            a = -.04*y[0] + 1e4*y[1]*y[2]
            c = 3e7*y[1]**2
            return [a, -a-c, c]

        reference = integrate.solve_ivp(robertson, (0., 100.), [1., 0., 0.], method="Radau", rtol=2e-12, atol=1e-14, dense_output=True)
        grid = np.r_[0., np.geomspace(1e-6, 100., 100)]
        check("robertson_reference_status", reference.success)
        for method in ("BDF", "Radau"):
            for tolerance in (1e-4, 1e-6, 1e-8):
                start = time.perf_counter()
                sol = integrate.solve_ivp(robertson, (0., 100.), [1., 0., 0.], method=method, rtol=tolerance, atol=tolerance*1e-3, t_eval=grid)
                elapsed = time.perf_counter()-start
                check(f"robertson_{method}_{tolerance}_status", sol.success)
                if sol.success:
                    mass = float(np.max(np.abs(sol.y.sum(axis=0)-1.)))
                    minimum = float(sol.y.min())
                    check(f"robertson_{method}_{tolerance}_invariants", mass < 1e-8 and minimum > -1e-7, mass_error=mass, minimum=minimum)
                    curves.append({"method": method, "rtol": tolerance, "seconds": elapsed, "max_error": float(np.max(np.abs(sol.y-reference.sol(grid))))})
        metrics.update(analytic_errors=errors, robertson_work_precision=curves, rtol=1e-8, atol=1e-10, sample_times=times.tolist(), solution_samples=samples)
        limitations.append("Robertson reference is a tighter numerical Radau solve, not an exact or rigorous enclosure. Single timings are illustrative.")
    elif name == "optimization":
        import cvxpy as cp
        x = cp.Variable(2)
        c = np.array([.75, 1.25])
        bounds, equality = x >= 0, cp.sum(x) == 1
        problem = cp.Problem(cp.Minimize(.5*cp.sum_squares(x)-c@x), [bounds, equality])
        problem.solve(solver="CLARABEL", tol_gap_abs=1e-10, tol_feas=1e-10, tol_gap_rel=1e-10)
        check("convex_status", problem.status == cp.OPTIMAL, status=problem.status)
        if x.value is not None:
            v = np.asarray(x.value)
            feasibility = max(float(abs(v.sum()-1)), float(max(0., -v.min())))
            stationarity = float(np.linalg.norm(v-c+equality.dual_value-bounds.dual_value, np.inf))
            complementarity = float(np.max(np.abs(v*bounds.dual_value)))
            check("known_quadratic_solution", np.max(np.abs(v-[.25,.75])) < 1e-7)
            check("kkt", feasibility < 1e-7 and stationarity < 1e-7 and complementarity < 1e-7)
            metrics.update(solution=v.tolist(), feasibility=feasibility, stationarity=stationarity, complementarity=complementarity)
        result = optimize.milp(c=[-3., -2.], integrality=[1, 1], bounds=optimize.Bounds([0, 0], [np.inf, np.inf]), constraints=optimize.LinearConstraint([[2,1],[1,2]], [-np.inf,-np.inf], [4,4]), options={"mip_rel_gap": 0.})
        check("integer_optimum", result.success and abs(result.fun+6.) < 1e-9 and result.mip_gap < 1e-9, status=int(result.status))
        metrics.update(integer_objective=float(-result.fun) if result.fun is not None else None, integer_gap=float(result.mip_gap) if result.success else None)
    elif name == "sparse":
        n = 16
        t = sparse.diags([-np.ones(n-1), 2*np.ones(n), -np.ones(n-1)], [-1,0,1], format="csr")
        matrix = sparse.kronsum(t, t, format="csr")
        truth = np.sin(np.arange(n*n)+1.)
        rhs = matrix@truth
        outcomes = []
        # SSOR is SPD, unlike a generic ILU; it is admissible for CG.
        lower = sparse.tril(matrix, format="csr")
        upper = lower.T.tocsr()
        diagonal = matrix.diagonal()
        preconditioner = linalg.LinearOperator(matrix.shape, matvec=lambda v: linalg.spsolve_triangular(upper, diagonal*linalg.spsolve_triangular(lower, v, lower=True), lower=False))
        for label, pre in (("none", None), ("ssor", preconditioner)):
            count = [0]
            def callback(value):
                count[0] += 1
            solution, status = linalg.cg(matrix, rhs, M=pre, rtol=1e-11, atol=1e-13, maxiter=2000, callback=callback)
            error = float(np.linalg.norm(solution-truth)/np.linalg.norm(truth))
            residual = float(np.linalg.norm(rhs-matrix@solution)/np.linalg.norm(rhs))
            backward = float(np.linalg.norm(rhs-matrix@solution, np.inf)/(linalg.norm(matrix, np.inf)*np.linalg.norm(solution, np.inf)+np.linalg.norm(rhs, np.inf)))
            check("cg_"+label, status == 0 and error < 1e-7 and residual < 1e-9)
            outcomes.append({"preconditioner": label, "iterations": count[0], "relative_error": error, "relative_residual": residual, "backward_error_inf": backward, "status": int(status)})
        # Preserve strict row diagonal dominance when adding nonsymmetry.
        # Without the diagonal shift, restarted GMRES can stagnate on this
        # nearly indefinite example; that is a different research question.
        nonsymmetric = matrix+sparse.eye(n*n, format="csr")*.5+sparse.diags(np.full(n*n-1, -.2), 1)
        b = nonsymmetric@truth
        answer, status = linalg.gmres(nonsymmetric, b, rtol=1e-11, atol=1e-13, maxiter=2000)
        gmres_error = float(np.linalg.norm(answer-truth)/np.linalg.norm(truth))
        gmres_residual = float(np.linalg.norm(nonsymmetric@answer-b)/np.linalg.norm(b))
        row_sums = np.asarray(abs(nonsymmetric).sum(axis=1)).ravel()
        dominance_margin = float(np.min(2*np.abs(nonsymmetric.diagonal())-row_sums))
        check("nonsymmetric_gmres", status == 0 and gmres_error < 1e-7 and gmres_residual < 1e-9)
        direct = linalg.spsolve(matrix, rhs)
        check("direct_reference", np.linalg.norm(direct-truth)/np.linalg.norm(truth) < 1e-12)
        condition = float((1+math.cos(math.pi/(n+1)))/(1-math.cos(math.pi/(n+1))))
        metrics.update(solvers=outcomes, analytic_spd_condition_2=condition, matrix_shape=list(matrix.shape), nnz=int(matrix.nnz),
                       nonsymmetric_gmres={"status": int(status), "relative_error": gmres_error, "relative_residual": gmres_residual,
                                           "diagonal_shift": .5, "row_dominance_margin": dominance_margin,
                                           "condition_inf_upper_bound": float(max(row_sums)/dominance_margin),
                                           "conditioning_note": "Strict row diagonal dominance gives an infinity-norm condition bound, not an exact 2-norm condition number."})
        limitations.append("Known-solution synthetic systems demonstrate correctness; they do not predict performance on research matrices.")
    elif name == "approximation":
        import mpmath as mp
        from flint import arb, ctx
        value, estimate = integrate.quad(math.sin, 0., math.pi, epsabs=1e-12, epsrel=1e-12)
        check("quadrature_exact_integral", abs(value-2.) < 1e-10)
        sizes = [16,32,64,128]
        trapezoid_errors, interpolation_errors = [], []
        sample = np.linspace(0., 1., 4097)
        for size in sizes:
            grid = np.linspace(0., math.pi, size+1)
            trapezoid_errors.append(abs(float(integrate.trapezoid(np.sin(grid), grid))-2.))
            nodes = np.linspace(0., 1., size+1)
            interpolation_errors.append(float(np.max(np.abs(np.interp(sample, nodes, np.exp(nodes))-np.exp(sample)))))
        trap_rates = np.log2(np.array(trapezoid_errors[:-1])/trapezoid_errors[1:])
        interp_rates = np.log2(np.array(interpolation_errors[:-1])/interpolation_errors[1:])
        check("trapezoid_second_order", np.all((trap_rates[-2:] > 1.8)&(trap_rates[-2:] < 2.2)))
        check("interpolation_second_order", np.all((interp_rates[-2:] > 1.8)&(interp_rates[-2:] < 2.2)))
        mp.mp.dps = 80
        small = mp.mpf("1e-8")
        reference = (1-mp.cos(small))/small**2
        stable = 2*(math.sin(1e-8/2)/1e-8)**2
        naive = (1-math.cos(1e-8))/1e-16
        ctx.prec = 256
        a = arb("1e-8")
        enclosure = 2*((a/2).sin()/a)**2
        # Check overlapping rigorous enclosures, independently evaluated forms.
        alternate = (1-a.cos())/(a*a)
        check("arb_consistent_enclosures", enclosure.overlaps(alternate))
        check("stable_cancellation_formula", abs(stable-float(reference)) < 1e-15)
        metrics.update(quadrature=value, quadrature_error_estimate=estimate, mesh_sizes=sizes, trapezoid_errors=trapezoid_errors, trapezoid_rates=trap_rates.tolist(), interpolation_errors=interpolation_errors, interpolation_rates=interp_rates.tolist(), cancellation={"naive": naive, "stable": stable, "mpmath_reference": str(reference), "arb_enclosure": str(enclosure)})
        limitations.append("mpmath supplies high precision, not rigorous bounds; Arb checks here cover the displayed expression only.")
    else:
        raise ValueError("Unknown Python experiment")
    return {"checks": checks, "metrics": metrics, "limitations": limitations}


if __name__ == "__main__":
    config = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}
    result = execute(config)
    output = Path(os.environ.get("MATH_OUTPUT_DIR", "/output"))
    (output/"experiment.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    sys.exit(0 if all(item["passed"] for item in result["checks"]) else 1)
