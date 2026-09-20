from __future__ import annotations

import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from investment_intelligence.http import FetchError, get_json  # noqa: E402


class HttpTests(unittest.TestCase):
    def test_error_context_omits_url_userinfo_and_query(self) -> None:
        def failing_opener(request, *, timeout):
            raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=None)

        with self.assertRaises(FetchError) as raised:
            get_json("https://user:pass@example.invalid/data?credential=private", opener=failing_opener)
        message = str(raised.exception)
        self.assertIn("example.invalid", message)
        self.assertNotIn("user", message)
        self.assertNotIn("pass", message)
        self.assertNotIn("credential", message)


if __name__ == "__main__":
    unittest.main()
