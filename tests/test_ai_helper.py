import unittest

from agents.ai_helper import ask_ai


class AiHelperTests(unittest.TestCase):
    def test_ask_ai_returns_friendly_error_when_llm_is_unavailable(self):
        result = ask_ai("Say hello")

        self.assertIn("AI Error", result)


if __name__ == "__main__":
    unittest.main()
