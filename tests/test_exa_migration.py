#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, importlib.util, tempfile, unittest

ROOT = Path(__file__).resolve().parents[1]


class ExaMigration(unittest.TestCase):
    def test_exact_single_exa_and_no_firecrawl(self):
        cfg = json.loads((ROOT / "opencode.jsonc").read_text())
        servers = cfg["mcp"]["servers"]
        self.assertEqual(len(servers), 10)
        self.assertEqual(sum(n == "exa" for n in servers), 1)
        self.assertNotIn("firecrawl", servers)
        self.assertEqual(servers["exa"]["url"], "https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa,agent_run")
        self.assertTrue(
            all(s["disabled"] and s["codemode"] is False for s in servers.values())
        )
        self.assertFalse(
            any(
                "firecrawl" in json.dumps(r).lower()
                for r in cfg["permissions"] + cfg["policies"]
            )
        )

    def test_web_researcher_only_exa_search_fetch(self):
        import yaml

        p = ROOT / "agents/web-researcher.md"
        meta = yaml.safe_load(p.read_text().split("---", 2)[1])
        self.assertEqual(
            {r["action"] for r in meta["permissions"]},
            {"*", "exa_web_search_exa", "exa_web_fetch_exa"},
        )
        self.assertEqual(
            meta["permissions"][0], {"action": "*", "resource": "*", "effect": "deny"}
        )
        self.assertTrue(all(r["effect"] == "ask" for r in meta["permissions"][1:]))
        self.assertFalse((ROOT / "commands/firecrawl-research.md").exists())
        self.assertTrue((ROOT / "commands/exa-research.md").exists())

    def test_retirement_is_opt_in_and_checks_hash(self):
        mod_path = ROOT / "scripts/retire_legacy_firecrawl.py"
        spec = importlib.util.spec_from_file_location("retirer", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            commands = config / "commands"
            commands.mkdir()
            legacy = commands / "firecrawl-research.md"
            legacy.write_text("my custom script")
            self.assertEqual(mod.main(["--config-dir", str(config), "--apply"]), 3)
            self.assertTrue(legacy.exists())
            # Refusing an unknown user command must neither move it nor create an archive.
            self.assertEqual(legacy.read_text(), "my custom script")
            self.assertFalse((config / "archive").exists())

    def test_manual_controller_whitelist(self):
        m = (ROOT / "scripts/mcpctl.py").read_text()
        self.assertIn('"exa"', m)
        allow = m.split("ALLOWED = (", 1)[1].split(")", 1)[0]
        self.assertNotIn("firecrawl", allow.lower())


if __name__ == "__main__":
    unittest.main()
