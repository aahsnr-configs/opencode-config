"""Build a named theorem and inspect the transitive axiom report."""
import json
from pathlib import Path
import re
import subprocess

allowed = {"propext", "Classical.choice", "Quot.sound"}


def build(path):
    result = subprocess.run(["lake", "env", "lean", str(path)], cwd="/opt/mathlib", text=True, capture_output=True, timeout=240)
    transcript = result.stdout + result.stderr
    reports = re.findall(r"depends on axioms:\s*\[([^\]]*)\]", transcript)
    axioms = {s.strip() for report in reports for s in report.split(",") if s.strip()}
    complete_report = bool(reports) or "does not depend on any axioms" in transcript
    accepted = result.returncode == 0 and complete_report and axioms <= allowed
    return accepted, sorted(axioms), transcript, result.returncode


accepted, axioms, transcript, status = build(Path("/inputs/theorem.lean"))
Path("/output/theorem-build.log").write_text(transcript)
incomplete = Path("/output/incomplete.lean")
incomplete.write_text("import Mathlib\ntheorem incomplete : False := by sorry\n#print axioms incomplete\n")
bad_accepted, bad_axioms, bad_transcript, bad_status = build(incomplete)
Path("/output/incomplete-build.log").write_text(bad_transcript)
checks = [{"name": "theorem_build_and_axioms", "passed": accepted}, {"name": "incomplete_proof_rejected", "passed": not bad_accepted and "sorryAx" in bad_axioms}]
result = {"checks": checks, "metrics": {"axioms": axioms, "allowed_axioms": sorted(allowed), "build_status": status, "negative_case_axioms": bad_axioms}, "limitations": ["Axiom inspection is a declared trust policy. The formal statement still requires human comparison with the intended research claim."]}
Path("/output/experiment.json").write_text(json.dumps(result, indent=2)+"\n")
raise SystemExit(0 if all(c["passed"] for c in checks) else 1)
