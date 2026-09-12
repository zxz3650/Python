"""05-3 문서의 패턴과 실행 예제를 정상·유사·경계 입력으로 대조한다."""
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("security_regex", ROOT / "examples/05-security-regex/security_regex.py")
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


class SecurityRegexTests(unittest.TestCase):
    def test_web_status_not_url_or_agent(self):
        self.assertEqual([lesson.is_web_error(x) for x in lesson.WEB_LINES], [True, True, False, False])
        self.assertTrue(lesson.is_web_error(lesson.WEB_LINES[0] + "\r\n"))
        self.assertFalse(lesson.is_web_error(lesson.WEB_LINES[0] + " trailing"))
        with self.assertRaises(ValueError):
            lesson.is_web_error("x" * 8193)

    def test_ssh_message_boundaries(self):
        self.assertEqual([lesson.find_ssh_failure(x) is not None for x in lesson.AUTH_LINES], [True, True, False])
        self.assertIsNone(lesson.find_ssh_failure(lesson.AUTH_LINES[0] + " trailing"))
        self.assertIsNone(lesson.find_ssh_failure(lesson.AUTH_LINES[0].replace("sshd[101]", "app[101]")))

    def test_cloudtrail_field_scoping_and_omissions(self):
        rows = [lesson.classify_cloudtrail(x) for x in lesson.load_events(lesson.CLOUDTRAIL_TEXT)]
        self.assertTrue(rows[0]["change_name_candidate"])
        self.assertTrue(rows[0]["cli_version_prefix"])
        self.assertTrue(rows[1]["access_denied_candidate"])
        self.assertFalse(rows[2]["change_name_candidate"])
        self.assertTrue(rows[2]["access_denied_candidate"])
        self.assertTrue(rows[3]["review_event"])
        self.assertFalse(rows[3]["change_name_candidate"])
        self.assertEqual(rows[2]["source_kind"], "IPv6")
        for event in ({}, {"userAgent": None}):
            self.assertFalse(lesson.classify_cloudtrail(event)["cli_version_prefix"])
        with self.assertRaises(TypeError):
            lesson.classify_cloudtrail({"userAgent": []})
        for invalid in ('[]', '{"Records": {}}', '{"Records": [null]}'):
            with self.assertRaises(ValueError):
                lesson.load_events(invalid)
        payload = json.loads(lesson.CLOUDTRAIL_TEXT)
        reordered = json.dumps(payload, sort_keys=True)
        self.assertEqual(payload["Records"], lesson.load_events(reordered))

    def test_identifiers_and_error_boundaries(self):
        self.assertIsNotNone(lesson.ACCOUNT_ID.fullmatch("123456789012"))
        self.assertIsNone(lesson.ACCOUNT_ID.fullmatch("１２３４５６７８９０１２"))
        self.assertIsNone(lesson.ACCOUNT_ID.fullmatch("123456789012\n"))
        self.assertIsNotNone(lesson.SHA256.fullmatch("a" * 64))
        self.assertIsNone(lesson.SHA256.fullmatch("g" * 64))
        self.assertIsNone(lesson.ACCESS_DENIED.fullmatch("AccessDeniedButAllowed"))
        self.assertIsNone(lesson.CLI_AGENT.match("custom aws-cli/2.0.0"))

    def test_document_examples_match_runtime_patterns(self):
        text = (ROOT / "05-text-processing/05-3-regex-basics.md").read_text()
        section = text.split("## 8-1.")[1].split("## 9.")[0]
        namespace = {}
        for code in re.findall(r"\x60{3}python\n(.*?)\x60{3}", section, re.S):
            exec(compile(code, "05-3-doc-example", "exec"), namespace)
        for name in ("WEB_ERROR", "SSH_FAILURE", "CHANGE_EVENT", "ACCESS_DENIED", "CLI_AGENT", "ACCOUNT_ID", "SHA256"):
            self.assertEqual(namespace[name].pattern, getattr(lesson, name).pattern)


if __name__ == "__main__":
    unittest.main()
