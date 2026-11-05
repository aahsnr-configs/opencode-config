"""Offline regression checks for the standalone generic REST helper copies."""

import importlib.util
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills/alphafold-skill/scripts/rest_request.py"
SPEC = importlib.util.spec_from_file_location("generic_rest_safety", SOURCE)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
RESOLVER_SOURCE = ROOT / "skills/finngen-phewas-skill/scripts/variant_resolution.py"
RESOLVER_SPEC = importlib.util.spec_from_file_location("bounded_variant_resolver", RESOLVER_SOURCE)
resolver = importlib.util.module_from_spec(RESOLVER_SPEC)
sys.modules[RESOLVER_SPEC.name] = resolver
RESOLVER_SPEC.loader.exec_module(resolver)


class Response:
    def __init__(self, chunks=(), status=200, content_type="application/json"):
        self.status_code = status
        self.headers = {"content-type": content_type}
        self.encoding = "utf-8"
        self.chunks = chunks
        self.consumed = 0
        self.closed = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise helper.requests.HTTPError(str(self.status_code))

    def iter_content(self, chunk_size):
        for chunk in self.chunks:
            self.consumed += 1
            yield chunk

    def close(self):
        self.closed = True


class Session:
    def __init__(self, response):
        self.response = response
        self.headers = {}
        self.calls = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response

    def close(self):
        self.closed = True


class GenericRestSafety(unittest.TestCase):
    def execute(self, response, **payload):
        session = Session(response)
        value = {"base_url": "https://approved.example/api", "path": "records", **payload}
        with patch.object(helper.requests, "Session", return_value=session):
            result = helper.execute(value)
        return result, session

    def test_foreign_origin_is_rejected_before_session_creation(self):
        for path in ("https://other.example/records", "//other.example/records", "http://approved.example/records"):
            with self.subTest(path=path), patch.object(helper.requests, "Session") as create:
                with self.assertRaises(ValueError):
                    helper.execute({"base_url": "https://approved.example/api", "path": path,
                                    "headers": {"X-API-Key": "synthetic-test-value"}})
                create.assert_not_called()

    def test_absolute_same_origin_and_relative_paths_keep_compatibility(self):
        self.assertEqual(helper._build_url("https://approved.example/api", "records"),
                         "https://approved.example/api/records")
        self.assertEqual(helper._build_url("https://approved.example/api", "/records"),
                         "https://approved.example/api/records")
        self.assertEqual(helper._build_url("https://approved.example/api", "https://approved.example:443/records"),
                         "https://approved.example:443/records")

    def test_invalid_base_urls_are_rejected(self):
        for base in ("file:///tmp/data", "https://user:password@approved.example", "https://approved.example?query=x", "https://approved.example/#fragment"):
            with self.subTest(base=base), self.assertRaises(ValueError):
                helper._build_url(base, "records")

    def test_redirect_is_not_followed_or_read(self):
        response = Response((b"must not read",), status=302)
        result, session = self.execute(response, headers={"X-API-Key": "synthetic-test-value"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "redirect_refused")
        self.assertEqual(len(session.calls), 1)
        self.assertIs(session.calls[0][2]["allow_redirects"], False)
        self.assertIs(session.calls[0][2]["stream"], True)
        self.assertEqual(response.consumed, 0)
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_response_limit_stops_stream_and_closes_resources(self):
        response = Response((b"123456", b"789012", b"not consumed"))
        with patch.object(helper, "MAX_RESPONSE_BYTES", 10):
            result, session = self.execute(response)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "response_too_large")
        self.assertEqual(response.consumed, 2)
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_valid_json_and_text_remain_compact(self):
        response = Response((b'{"results":[{"id":1},', b'{"id":2}]}'))
        result, session = self.execute(response, max_items=1)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["records"], [{"id": 1}])
        self.assertTrue(result["truncated"])
        self.assertEqual(result["record_count_available"], 2)
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)
        result, _ = self.execute(Response((b"plain text",), content_type="text/plain"))
        self.assertEqual(result["text_head"], "plain text")

    def test_invalid_json_still_closes_resources(self):
        response = Response((b"{broken",))
        result, session = self.execute(response)
        self.assertEqual(result["error"]["code"], "invalid_response")
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_json_encoding_and_invalid_text_charset_are_handled(self):
        result, _ = self.execute(Response(('{"id": 1}'.encode("utf-16"),)))
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["summary"], {"id": 1})
        response = Response((b"plain text",), content_type="text/plain")
        response.encoding = "not-a-real-encoding"
        result, _ = self.execute(response)
        self.assertEqual(result["text_head"], "plain text")

    def test_http_error_closes_response_and_session(self):
        response = Response(status=500)
        result, session = self.execute(response)
        self.assertEqual(result["error"]["code"], "network_error")
        self.assertEqual(response.consumed, 0)
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_http_errors_do_not_echo_credential_bearing_urls(self):
        response = Response(status=500)
        failure = helper.requests.HTTPError(
            "500 error at https://approved.example/records?api_key=synthetic-secret", response=response,
        )
        with patch.object(response, "raise_for_status", side_effect=failure):
            result, session = self.execute(response)
        message = result["error"]["message"]
        self.assertIn("HTTPError", message)
        self.assertIn("500", message)
        self.assertNotIn("synthetic-secret", message)
        self.assertNotIn("https://", message)
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_invalid_headers_do_not_echo_header_values(self):
        session = Session(Response())
        failure = helper.requests.exceptions.InvalidHeader("Invalid header value b'synthetic-secret\\n'")
        with patch.object(helper.requests, "Session", return_value=session), \
                patch.object(session, "request", side_effect=failure):
            result = helper.execute({"base_url": "https://approved.example", "path": "records",
                                     "headers": {"X-API-Key": "synthetic-secret\n"}})
        self.assertEqual(result["error"]["code"], "network_error")
        self.assertIn("InvalidHeader", result["error"]["message"])
        self.assertNotIn("synthetic-secret", result["error"]["message"])
        self.assertTrue(session.closed)

    def test_real_request_preparation_cannot_echo_invalid_header(self):
        with patch.object(helper.requests.sessions, "get_netrc_auth", return_value=None), \
                patch.object(helper.requests.sessions.Session, "send", side_effect=AssertionError("no network")) as send:
            result = helper.execute({"base_url": "https://approved.example", "path": "records",
                                     "headers": {"X-API-Key": "synthetic-secret\n"}})
        send.assert_not_called()
        self.assertEqual(result["error"]["code"], "network_error")
        self.assertIn("InvalidHeader", result["error"]["message"])
        self.assertNotIn("synthetic-secret", result["error"]["message"])

    def test_excessively_nested_json_returns_structured_error(self):
        result, session = self.execute(Response((b"[" * 10000 + b"0" + b"]" * 10000,)))
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_response")
        self.assertTrue(session.response.closed)
        self.assertTrue(session.closed)

    def test_bool_is_not_an_integer_limit(self):
        for key in ("timeout_sec", "max_items", "max_depth"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                helper.parse_input({"base_url": "https://approved.example", "path": "records", key: True})

    def test_raw_output_refuses_linked_ancestor_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            outside = base / "outside"
            outside.mkdir()
            link = base / "linked"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                helper._save_raw_output("data", str(link / "new" / "raw.json"), "https://approved.example", "json")
            self.assertEqual(list(outside.iterdir()), [])

    def test_all_thirty_generic_copies_match(self):
        marker = b'"""Generic compact REST client for ChatGPT-imported skills."""'
        paths = [path for path in (ROOT / "skills").glob("*/scripts/rest_request.py")
                 if marker in path.read_bytes() and b"EQTLCAT_BASE_URL" not in path.read_bytes()]
        self.assertEqual(len(paths), 30)
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), SOURCE.read_bytes())


class VariantResolverRequestSafety(unittest.TestCase):
    def test_only_expected_https_origins_can_be_requested(self):
        for url in ("http://rest.ensembl.org/variation/human/rs1", "https://other.example/path",
                    "https://user:password@rest.ensembl.org/path", "https://rest.ensembl.org:444/path"):
            with self.subTest(url=url), patch.object(resolver.requests, "get") as request:
                with self.assertRaises(resolver.VariantResolutionError) as raised:
                    resolver._get_json(url)
                self.assertEqual(raised.exception.code, "invalid_input")
                request.assert_not_called()

    def test_resolver_refuses_redirects_before_reading(self):
        response = Response((b"not consumed",), status=307)
        with patch.object(resolver.requests, "get", return_value=response) as request:
            with self.assertRaises(resolver.VariantResolutionError) as raised:
                resolver._get_json("https://rest.ensembl.org/variation/human/rs1")
        self.assertEqual(raised.exception.code, "redirect_refused")
        self.assertEqual(request.call_count, 1)
        self.assertIs(request.call_args.kwargs["allow_redirects"], False)
        self.assertIs(request.call_args.kwargs["stream"], True)
        self.assertEqual(response.consumed, 0)
        self.assertTrue(response.closed)

    def test_resolver_response_limit_aborts_stream(self):
        response = Response((b"123456", b"789012", b"not consumed"))
        with patch.object(resolver.requests, "get", return_value=response), \
                patch.object(resolver, "MAX_RESPONSE_BYTES", 10):
            with self.assertRaises(resolver.VariantResolutionError) as raised:
                resolver._get_json("https://rest.ensembl.org/path")
        self.assertEqual(raised.exception.code, "response_too_large")
        self.assertEqual(response.consumed, 2)
        self.assertTrue(response.closed)

    def test_resolver_reads_bounded_json_and_closes_response(self):
        response = Response((b'{"mappings":', b'[]}'))
        with patch.object(resolver.requests, "get", return_value=response):
            result = resolver._get_json("https://grch37.rest.ensembl.org/path")
        self.assertEqual(result, {"mappings": []})
        self.assertTrue(response.closed)

    def test_resolver_invalid_json_returns_structured_error(self):
        response = Response((b"{broken",))
        with patch.object(resolver.requests, "get", return_value=response):
            with self.assertRaises(resolver.VariantResolutionError) as raised:
                resolver._get_json("https://rest.ensembl.org/path")
        self.assertEqual(raised.exception.code, "invalid_response")
        self.assertTrue(response.closed)

    def test_resolver_invalid_timeout_fails_before_request(self):
        for timeout in (True, False, float("inf"), float("nan"), -1, 0, "15"):
            with self.subTest(timeout=timeout), patch.object(resolver.requests, "get") as request:
                with self.assertRaises(resolver.VariantResolutionError) as raised:
                    resolver._get_json("https://rest.ensembl.org/path", timeout=timeout)
                self.assertEqual(raised.exception.code, "invalid_input")
                request.assert_not_called()

    def test_all_five_resolver_copies_match(self):
        paths = list((ROOT / "skills").glob("*/scripts/variant_resolution.py"))
        self.assertEqual(len(paths), 5)
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), RESOLVER_SOURCE.read_bytes())


if __name__ == "__main__":
    unittest.main()
