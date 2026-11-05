"""Offline command routing checks using the configured agent permissions."""

import fnmatch
import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class TestCommandRouting(unittest.TestCase):
    def test_memory_update_routes_to_an_agent_that_requests_edit_approval(self):
        config = json.loads((ROOT / "opencode.jsonc").read_text())
        command = yaml.safe_load(
            (ROOT / "commands/memory.md").read_text().split("---", 2)[1]
        )
        agent_name = command.get("agent", config["default_agent"])
        agent = yaml.safe_load(
            (ROOT / "agents" / f"{agent_name}.md").read_text().split("---", 2)[1]
        )
        result = "ask"
        for rule in config["permissions"] + agent["permissions"]:
            if fnmatch.fnmatchcase("edit", rule["action"]) and fnmatch.fnmatchcase(
                "PROJECT-MEMORY.md", rule["resource"]
            ):
                result = rule["effect"]
        self.assertEqual(result, "ask")
        self.assertEqual(agent_name, "work")


if __name__ == "__main__":
    unittest.main()
