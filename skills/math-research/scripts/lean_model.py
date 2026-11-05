"""Container-only adapter for a locally reviewed Lean source and named theorem."""
import json
from pathlib import Path
import re
import subprocess
import sys


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    theorem = request.get("parameters", {}).get("theorem", "")
    if not isinstance(theorem, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9.]*", theorem):
        raise SystemExit("parameters.theorem must name the declaration to audit")
    source = Path("/inputs/model.lean").read_text()
    checked = Path("/tmp/checked.lean")
    checked.write_text(source + "\n#print axioms " + theorem + "\n")
    result = subprocess.run(["lake", "--dir", "/opt/mathlib", "env", "lean", str(checked)], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    found = re.findall(r"depends on axioms:\s*\[([^]]*)\]", result.stdout)
    axioms = [value.strip() for group in found for value in group.split(",") if value.strip()]
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    audit_present = bool(found) or "does not depend on any axioms" in result.stdout
    checks = [{"name": "lean_build", "passed": result.returncode == 0},
              {"name": "declared_axiom_policy", "passed": audit_present and set(axioms) <= allowed}]
    Path("/output/experiment.json").write_text(json.dumps({"checks": checks, "metrics": {"axioms": axioms, "theorem": theorem},
        "limitations": ["The formal statement still requires review against the intended research claim."]}, indent=2))
    return 0 if all(check["passed"] for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
