#!/usr/bin/env python3
"""Exercise doctor.sh against a mocked OpenCode V2 binary; no network needed."""

from pathlib import Path
import os, subprocess, tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="opencode-doctor-mock-") as d:
    mock = Path(d) / "opencode"
    env = os.environ.copy()
    env["PATH"] = d + os.pathsep + env.get("PATH", "")

    def run():
        return subprocess.run(
            ["bash", str(root / "doctor.sh")],
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
        )

    # Current V2 CLI and the expected custom agents
    mock.write_text("""#!/usr/bin/env bash
case "$*" in
  --version) echo '2.0.mock'; exit 0 ;;
  'debug config') echo 'global config'; exit 0 ;;
  'debug agents') printf 'build\nchat\nwork\ncoder\nresearch\nreviewer\ndigest\ncompactor\nexplore-scout\ngit-gh\nweb-researcher\ndeep-research\nlearn\nsol-advisor\n'; exit 0 ;;
  'mcp list') echo 'all disabled'; exit 0 ;;
  *) echo 'unexpected V1 CLI command: '"$*" >&2; exit 70 ;;
esac
""")
    mock.chmod(0o755)
    result = run()
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert "agent chat discovered" in result.stdout
    assert "agent sol-advisor discovered" in result.stdout
    assert "opencode agent list" not in result.stdout
    mock.write_text(mock.read_text().replace("\nsol-advisor\n", "\n"))
    result = run()
    assert result.returncode == 4, (result.returncode, result.stdout, result.stderr)
    assert "agent sol-advisor not found" in result.stderr
    # Agent discovery fails even though CLI exits 0 if custom agents are missing
    mock.write_text("""#!/usr/bin/env bash
case "$*" in
  --version) echo '2.0.mock'; exit 0 ;;
  'debug config') echo 'config'; exit 0 ;;
  'debug agents') echo 'build'; exit 0 ;;
  'mcp list') exit 0 ;;
  *) exit 70 ;;
esac
""")
    result = run()
    assert result.returncode == 4, (result.returncode, result.stdout, result.stderr)
    assert "agent chat not found" in result.stderr
    # V1-only CLI should fail with informative message
    mock.write_text("""#!/usr/bin/env bash
case "$*" in
  --version) echo '1.9.mock'; exit 0 ;;
  'debug config') exit 0 ;;
  'debug agents') echo 'invalid command' >&2; exit 2 ;;
  *) exit 70 ;;
esac
""")
    result = run()
    assert result.returncode == 3, (result.returncode, result.stdout, result.stderr)
    assert "not: opencode agent list (V1)" in result.stderr
print("PASS: OpenCode V2 command, missing-agent failure and V1 command rejection tests")
