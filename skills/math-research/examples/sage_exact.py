"""Exact Sage arithmetic acceptance experiment."""
import json
from pathlib import Path
from sage.all import PolynomialRing, QQ, ZZ

ring = PolynomialRing(QQ, "x")
x = ring.gen()
polynomial = x**4 - 1
factors = polynomial.factor()
integer = ZZ(10403)
checks = [
    {"name": "polynomial_exact_reconstruction", "passed": factors.prod() == polynomial},
    {"name": "integer_factorization", "passed": integer.factor().prod() == integer and integer == ZZ(101)*103},
]
Path("/output/experiment.json").write_text(json.dumps({"checks": checks, "metrics": {"ring": str(ring), "factorization": str(factors), "integer_factors": str(integer.factor())}, "limitations": ["These exact finite calculations do not establish an arbitrary conjecture."]}, indent=2)+"\n")
raise SystemExit(0 if all(c["passed"] for c in checks) else 1)
