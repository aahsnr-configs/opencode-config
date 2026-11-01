#!/usr/bin/env python3
"""Offline tests for four migrated user agents; no provider, MCP, or CLI calls."""

from pathlib import Path
import unittest, json, yaml

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"compactor", "explore-scout", "git-gh", "web-researcher"}


class TestMigratedAgents(unittest.TestCase):
    def test_all_agents_exist(self):
        for name in NAMES:
            self.assertTrue((ROOT / "agents" / (name + ".md")).is_file())

    def test_frontmatter_is_v2(self):
        for name in NAMES:
            text = (ROOT / "agents" / (name + ".md")).read_text()
            self.assertTrue(text.startswith("---\n"))
            front = yaml.safe_load(text.split("---", 2)[1])
            self.assertEqual(front["mode"], "subagent")
            self.assertTrue(front["model"].startswith("openai/gpt-6"))
            self.assertTrue(front["permissions"])
            self.assertNotIn("tools", front)
            self.assertNotIn("effort", front)
            self.assertNotIn("omitClaudeMd", front)

    def test_web_only_explicit_exa_tools(self):
        front = yaml.safe_load(
            (ROOT / "agents/web-researcher.md").read_text().split("---", 2)[1]
        )
        self.assertEqual(
            {x["action"] for x in front["permissions"]},
            {"*", "exa_web_search_exa", "exa_web_fetch_exa"},
        )
        self.assertEqual(
            front["permissions"][0], {"action": "*", "resource": "*", "effect": "deny"}
        )
        cfg = json.loads((ROOT / "opencode.jsonc").read_text())
        self.assertTrue(cfg["mcp"]["servers"]["exa"]["disabled"])
        self.assertEqual(cfg["mcp"]["servers"]["exa"]["codemode"], False)
        self.assertNotIn("firecrawl", cfg["mcp"]["servers"])

    def test_all_four_have_command(self):
        for name in ("handoff", "scout", "git-inspect", "exa-research"):
            f = yaml.safe_load(
                (ROOT / "commands" / (name + ".md")).read_text().split("---", 2)[1]
            )
            self.assertTrue(f["subagent"])

    def test_no_legacy_model_references(self):
        for name in NAMES:
            self.assertNotIn(
                "claude-haiku", (ROOT / "agents" / (name + ".md")).read_text()
            )


if __name__ == "__main__":
    unittest.main()
