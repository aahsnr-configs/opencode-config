"""Offline regression checks for ordered configuration permissions."""

import fnmatch
import json
from pathlib import Path
import subprocess
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def effect(rules, action, resource):
    result = "ask"
    for rule in rules:
        if fnmatch.fnmatchcase(action, rule["action"]) and fnmatch.fnmatchcase(resource, rule["resource"]):
            result = rule["effect"]
    return result


class TestConfigurationSafety(unittest.TestCase):
    def test_git_output_options_never_run_without_approval(self):
        config = json.loads((ROOT / "opencode.jsonc").read_text())
        rule_sets = {"global": config["permissions"]}
        for path in (ROOT / "agents").glob("*.md"):
            front = yaml.safe_load(path.read_text().split("---", 2)[1])
            rule_sets[path.stem] = config["permissions"] + front["permissions"]
        for name, rules in rule_sets.items():
            for command in ("git diff --output=/tmp/result", "git log --output=/tmp/result", "git show --output=/tmp/result"):
                with self.subTest(agent=name, command=command):
                    self.assertNotEqual(effect(rules, "shell", command), "allow")

    def test_auth_store_remains_denied_after_agent_overrides(self):
        config = json.loads((ROOT / "opencode.jsonc").read_text())
        for path in (ROOT / "agents").glob("*.md"):
            front = yaml.safe_load(path.read_text().split("---", 2)[1])
            rules = config["permissions"] + front["permissions"]
            for resource in ("/home/example/.local/share/opencode/auth.json", "/custom/data/opencode/auth.json"):
                with self.subTest(agent=path.stem, resource=resource):
                    self.assertEqual(effect(rules, "read", resource), "deny")

    def test_validator_refuses_disabled_assertions(self):
        result = subprocess.run([sys.executable, "-O", str(ROOT / "validate.py")], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("PASS:", result.stdout)
        self.assertIn("optimized Python", result.stderr)


if __name__ == "__main__":
    unittest.main()
