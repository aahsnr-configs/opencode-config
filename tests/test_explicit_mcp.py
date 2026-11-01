#!/usr/bin/env python3
import json, pathlib, importlib.util, unittest, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/mcpctl.py"
spec = importlib.util.spec_from_file_location("mcpctl", MODULE)
ctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctl)


class Handler(BaseHTTPRequestHandler):
    calls = []

    def do_GET(self):
        self.calls.append(("GET", self.path))
        body = json.dumps(
            {
                "data": [
                    {"name": "context7", "status": {"status": "disabled"}},
                    {"name": "exa", "status": {"status": "disabled"}},
                ]
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.calls.append(("POST", self.path))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


class TestManual(unittest.TestCase):
    def setUp(self):
        Handler.calls = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:" + str(self.server.server_port)
        self.temp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.temp.name) / "opencode.jsonc"
        self.path.write_text(
            json.dumps(
                {
                    "mcp": {
                        "servers": {
                            "context7": {"disabled": True},
                            "exa": {"disabled": True},
                        }
                    }
                }
            )
        )

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def test_baseline_all_off(self):
        cfg = json.loads((ROOT / "opencode.jsonc").read_text())
        self.assertTrue(
            all(
                x["disabled"] is True and x["codemode"] is False
                for x in cfg["mcp"]["servers"].values()
            )
        )
        self.assertEqual(len(cfg["mcp"]["servers"]), 10)
        self.assertEqual(Handler.calls, [])

    def test_refuses_remote_target(self):
        for x in (
            "https://example.org:4096",
            "http://8.8.8.8:4096",
            "http://user:pass@localhost:4096",
            "http://localhost:4096/path",
        ):
            with self.assertRaises(ctl.ControlError):
                ctl.safe_origin(x)

    def test_connect_requires_human(self):
        with patch.object(ctl, "explicit_confirm", return_value=False):
            with self.assertRaises(ctl.ControlError):
                ctl.main(
                    [
                        "--url",
                        self.url,
                        "--config",
                        str(self.path),
                        "connect",
                        "context7",
                    ]
                )
        self.assertEqual([m for m, path in Handler.calls if m == "POST"], [])

    def test_connect_only_after_approval(self):
        with patch.object(ctl, "explicit_confirm", return_value=True):
            self.assertEqual(
                ctl.main(
                    [
                        "--url",
                        self.url,
                        "--config",
                        str(self.path),
                        "connect",
                        "context7",
                    ]
                ),
                0,
            )
        self.assertIn(("POST", "/api/experimental/mcp/context7/connect"), Handler.calls)
        self.assertTrue(
            json.loads(self.path.read_text())["mcp"]["servers"]["context7"]["disabled"]
        )

    def test_disconnect(self):
        self.assertEqual(
            ctl.main(
                ["--url", self.url, "--config", str(self.path), "disconnect", "exa"]
            ),
            0,
        )
        self.assertIn(("POST", "/api/experimental/mcp/exa/disconnect"), Handler.calls)

    def test_manual_session_cleanup(self):
        from io import StringIO

        class Tty:
            def __enter__(self):
                return StringIO("\n")

            def __exit__(self, *a):
                return False

        with (
            patch.object(ctl, "explicit_confirm", return_value=True),
            patch("builtins.open", side_effect=lambda *a, **kw: Tty()),
        ):
            self.assertEqual(
                ctl.main(
                    ["--url", self.url, "--config", str(self.path), "session", "exa"]
                ),
                0,
            )
        self.assertIn(("POST", "/api/experimental/mcp/exa/connect"), Handler.calls)
        self.assertIn(("POST", "/api/experimental/mcp/exa/disconnect"), Handler.calls)

    def test_no_runtime_side_effect_from_list(self):
        ctl.main(["--config", str(self.path), "list"])
        self.assertEqual(Handler.calls, [])

    def test_pending_connection_blocks_second_server(self):
        payload = {
            "data": [
                {"name": "context7", "status": {"status": "pending"}},
                {"name": "exa", "status": {"status": "disabled"}},
            ]
        }
        with (
            patch.object(ctl, "request", return_value=payload),
            patch.object(ctl, "explicit_confirm", return_value=True) as approval,
        ):
            with self.assertRaisesRegex(ctl.ControlError, "disconnect existing MCP"):
                ctl.main(
                    ["--url", self.url, "--config", str(self.path), "connect", "exa"]
                )
            approval.assert_not_called()

    def test_needs_auth_connection_blocks_second_server(self):
        payload = {
            "data": [
                {"name": "context7", "status": {"status": "needs_auth"}},
                {"name": "exa", "status": {"status": "disabled"}},
            ]
        }
        with (
            patch.object(ctl, "request", return_value=payload),
            patch.object(ctl, "explicit_confirm", return_value=True) as approval,
        ):
            with self.assertRaisesRegex(ctl.ControlError, "disconnect existing MCP"):
                ctl.main(
                    ["--url", self.url, "--config", str(self.path), "connect", "exa"]
                )
            approval.assert_not_called()

    def test_bad_status_response_fails_closed(self):
        for payload in (
            {"data": {}},
            {"data": [{"name": "context7", "status": {"status": "unknown"}}]},
            {
                "data": [
                    {"name": "context7", "status": {"status": "disabled"}},
                    {"name": "context7", "status": {"status": "disabled"}},
                ]
            },
        ):
            with (
                self.subTest(payload=payload),
                patch.object(ctl, "request", return_value=payload),
            ):
                with self.assertRaises(ctl.ControlError):
                    ctl.main(
                        [
                            "--url",
                            self.url,
                            "--config",
                            str(self.path),
                            "connect",
                            "exa",
                        ]
                    )

    def test_documented_api_status_parsing(self):
        payload = {
            "location": {"directory": "/tmp/repo"},
            "data": [
                {"name": "context7", "status": {"status": "connected"}},
                {"name": "exa", "status": {"status": "disabled"}},
            ],
        }
        self.assertEqual(
            ctl.statuses(payload), [("context7", "connected"), ("exa", "disabled")]
        )

    def test_mcp_tools_require_ask(self):
        cfg = json.loads((ROOT / "opencode.jsonc").read_text())
        permissions = cfg["permissions"]
        for n in cfg["mcp"]["servers"]:
            self.assertTrue(
                any(
                    rule == {"action": n + "_*", "resource": "*", "effect": "ask"}
                    for rule in permissions
                )
            )
        self.assertTrue(
            any(
                r.get("action") == "mcp.use"
                and r.get("resource") == "*"
                and r.get("effect") == "deny"
                for r in cfg["policies"]
            )
        )


if __name__ == "__main__":
    unittest.main()
