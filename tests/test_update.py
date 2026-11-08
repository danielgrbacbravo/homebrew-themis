import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("update", pathlib.Path(__file__).parents[1] / "scripts/update.py")
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class FormulaUpdateTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        update.ROOT = pathlib.Path(self.workspace.name)
        self.archive = b"source fixture"
        self.expected = hashlib.sha256(self.archive).hexdigest()
        self.tag = "v0.1.0"
        update.fetch = self.fetch
        self.formula = update.ROOT / "Formula/themis.rb"

    def fetch(self, url):
        if url.endswith("latest"):
            return json.dumps(dict(tag_name=self.tag, draft=False, prerelease=False)).encode()
        if url.endswith("SHA256SUMS"):
            return f"{self.expected}  themis_{self.tag[1:]}_source.tar.gz\n".encode()
        return self.archive

    def test_verified_source_is_pinned_and_builds_from_vendor(self):
        update.main()
        formula = self.formula.read_text()
        self.assertIn(self.expected, formula)
        self.assertIn("/v0.1.0/themis_0.1.0_source.tar.gz", formula)
        self.assertIn('ENV["GOFLAGS"] = "-mod=vendor"', formula)

    def test_bad_checksum_does_not_write_formula(self):
        self.archive = b"tampered source"
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            update.main()
        self.assertFalse(self.formula.exists())

    def test_updates_never_downgrade_a_published_formula(self):
        update.main()
        before = self.formula.read_bytes()
        self.tag = "v0.0.9"
        update.main()
        self.assertEqual(before, self.formula.read_bytes())

    def test_unexpected_tag_is_rejected(self):
        self.tag = 'v0.1.0"; malicious'
        with self.assertRaisesRegex(ValueError, "semantic version"):
            update.main()
        self.assertFalse(self.formula.exists())


if __name__ == "__main__":
    unittest.main()
