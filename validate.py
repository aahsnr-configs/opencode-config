#!/usr/bin/env python3
"""Offline audit. No model calls, network, installed-CLI checks, or account actions."""

from pathlib import Path
import json, re, sys, subprocess, shlex

root = Path(__file__).resolve().parent
conf = json.loads((root / "opencode.jsonc").read_text())
assert conf["$schema"] == "https://opencode.ai/config.json"
assert conf["default_agent"] == "chat"
assert "permissions" in conf and "permission" not in conf
assert "agents" not in conf and "agent" not in conf
assert conf["share"] == "disabled"
assert conf["update"] in ("disable", "notify", "auto")
assert conf["snapshots"] is True
assert conf["tool_output"]["max_lines"] > 0 and conf["tool_output"]["max_bytes"] > 0
assert __import__("re").fullmatch(
    r"([1-9][0-9]?(\.[0-9]+)?)%", conf["compaction"]["buffer"]
)
assert conf["default_agent"] in {"chat", "work", "coder", "research", "digest"}
allowed_keys = {
    "$schema",
    "default_agent",
    "update",
    "share",
    "snapshots",
    "plugins",
    "compaction",
    "tool_output",
    "permissions",
    "mcp",
    "policies",
}
assert set(conf) <= allowed_keys, set(conf) - allowed_keys
assert isinstance(conf["permissions"], list) and len(conf["permissions"]) >= 12
for rule in conf["permissions"]:
    assert set(rule) == {"action", "resource", "effect"}
    assert isinstance(rule["action"], str) and isinstance(rule["resource"], str)
    assert rule["effect"] in ("ask", "allow", "deny")
assert {item["action"] for item in conf["permissions"]} >= {
    "read",
    "shell",
    "edit",
    "subagent",
    "external_directory",
}
assert conf["permissions"][0] == {"action": "*", "resource": "*", "effect": "ask"}
assert conf["compaction"]["auto"] is True
assert isinstance(conf["compaction"]["keep"]["tokens"], int)
assert conf["mcp"].keys() == {"servers"}
assert isinstance(conf["policies"], list)
assert conf["policies"][0] == {"action": "mcp.use", "resource": "*", "effect": "deny"}
for policy in conf["policies"]:
    assert (
        set(policy) == {"action", "resource", "effect"}
        and policy["action"] == "mcp.use"
    )
    assert policy["effect"] in ("deny", "allow")

servers = conf["mcp"]["servers"]
inventory = json.loads((root / "schemas/config-inventory.json").read_text())
assert set(servers) == set(inventory["servers"])
for n, c in servers.items():
    assert (
        c["type"] in ("local", "remote")
        and c["disabled"] is True
        and c["codemode"] is False
    ), (n, c)
    assert {"action": n + "_*", "resource": "*", "effect": "ask"} in conf["permissions"]
    assert {"action": "mcp.use", "resource": n, "effect": "allow"} in conf["policies"]
    if c["type"] == "remote":
        assert c["url"].startswith("https://") and set(c) <= {
            "type",
            "url",
            "disabled",
            "protocol",
            "codemode",
        }
        if "protocol" in c:
            assert c["protocol"] in ("legacy", "auto", "2026-07-28")
    else:
        assert len(c["command"]) >= 2
        if n == "zotero":
            assert c["command"] == ["opencode-research-tools", "serve-zotero"]
        else:
            assert c["command"][0] == "npx"
try:
    import yaml
except ImportError:
    yaml = None
assert {p.stem for p in (root / "agents").glob("*.md")} == set(inventory["agents"])
assert {p.stem for p in (root / "commands").glob("*.md")} == set(inventory["commands"])
assert {p.parent.name for p in (root / "skills").glob("*/SKILL.md")} == set(inventory["skills"])
assert "Kilo" not in (root / "AGENTS.md").read_text()
for p in [
    *(root / "agents").glob("*.md"),
    *(root / "commands").glob("*.md"),
    *(root / "skills").glob("*/SKILL.md"),
    root / "examples/openchamber/repo-digest.loop.md",
]:
    s = p.read_text()
    assert s.startswith("---\n"), p
    _, front, body = s.split("---", 2)
    assert body.strip(), p
    if yaml:
        obj = yaml.safe_load(front)
        assert isinstance(obj, dict) and isinstance(
            obj.get("description") or obj.get("name"), str
        ), p
        if p.parent.name == "agents":
            assert obj["mode"] in ("primary", "subagent", "all"), p
            assert isinstance(obj.get("permissions"), list), p
            for pr in obj["permissions"]:
                assert set(pr) == {"action", "resource", "effect"}
            if p.stem == "digest":
                assert {"action": "read", "resource": "*.env", "effect": "deny"} in obj[
                    "permissions"
                ]
        if p.name == "SKILL.md":
            assert obj["name"] == p.parent.name, p
        if p.name == "repo-digest.loop.md":
            assert obj["enabled"] is False and obj["model"].startswith("REPLACE_WITH_")
    else:
        assert "description:" in front or "name:" in front, p

# Verify specialty model mapping, exact V2 fields, and manual MCP constraints.
expected_models = {
    "compactor": "openai/gpt-6-luna",
    "explore-scout": "openai/gpt-6-luna",
    "git-gh": "openai/gpt-6-luna",
    "web-researcher": "openai/gpt-6-luna",
    "sol-advisor": "openai/gpt-6.1-sol#high",
}
if yaml:
    for name, model in expected_models.items():
        p = root / "agents" / (name + ".md")
        front = p.read_text().split("---", 2)[1]
        obj = yaml.safe_load(front)
        assert obj["model"] == model and obj["mode"] == "subagent"
        assert not set(obj).intersection(
            {"tools", "effort", "omitClaudeMd", "permission", "prompt", "maxSteps"}
        )
        if name == "web-researcher":
            assert {"action": "*", "resource": "*", "effect": "deny"} in obj[
                "permissions"
            ]
            assert {r["action"] for r in obj["permissions"]} == {
                "*",
                "exa_web_search_exa",
                "exa_web_fetch_exa",
            }
        else:
            assert {"action": "edit", "resource": "*", "effect": "allow"} not in obj[
                "permissions"
            ]
assert "firecrawl" not in servers
assert servers["exa"]["disabled"] is True and servers["exa"]["codemode"] is False
assert {"action": "exa_*", "resource": "*", "effect": "ask"} in conf["permissions"]
assert {"action": "mcp.use", "resource": "exa", "effect": "allow"} in conf["policies"]
assert not (root / "commands/firecrawl-research.md").exists()
assert (root / "commands/exa-research.md").exists()

subprocess.run(["bash", "-n", str(root / "install.sh")], check=True)
assert not (root / "paseo").exists()
assert not (root / "kilo.jsonc").exists()
print(
    "PASS: V2 config fields, MCP shape, permissions, agent/command/skill/loop metadata, installer syntax"
)
if not yaml:
    print(
        "WARNING: PyYAML not installed: YAML semantics were not fully parsed (pip install PyYAML)"
    )
