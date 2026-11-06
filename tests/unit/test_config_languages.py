import unittest
from app.core.config import Settings, get_settings
from app.core.languages import (
    resolve_language_id,
    get_language_info,
    get_supported_languages,
    SUPPORTED_LANGUAGES,
)


class TestConfigAndLanguages(unittest.TestCase):
    def test_settings_initialization(self):
        settings = get_settings()
        self.assertIsInstance(settings, Settings)
        self.assertTrue(hasattr(settings, "GROQ_MODEL"))
        self.assertTrue(hasattr(settings, "JUDGE0_URL"))
        self.assertEqual(settings.API_V1_STR, "/api/v1")

    def test_language_resolution(self):
        self.assertEqual(resolve_language_id(71), 71)
        self.assertEqual(resolve_language_id("71"), 71)
        self.assertEqual(resolve_language_id("Python 3"), 71)
        self.assertEqual(resolve_language_id("py"), 71)
        self.assertEqual(resolve_language_id("c++"), 54)
        self.assertEqual(resolve_language_id("cpp"), 54)
        self.assertEqual(resolve_language_id("javascript"), 63)
        self.assertEqual(resolve_language_id("typescript"), 74)
        self.assertEqual(resolve_language_id("java"), 62)
        self.assertEqual(resolve_language_id("go"), 60)
        self.assertEqual(resolve_language_id("c#"), 51)

    def test_unsupported_language_raises_value_error(self):
        with self.assertRaises(ValueError):
            resolve_language_id("pascal")
        with self.assertRaises(ValueError):
            resolve_language_id("invalid_lang_xyz")

    def test_get_language_info(self):
        info = get_language_info("Python 3")
        self.assertIsNotNone(info)
        self.assertEqual(info.id, 71)
        self.assertEqual(info.monaco_id, "python")
        self.assertEqual(info.extension, ".py")

        invalid_info = get_language_info("unknown")
        self.assertIsNone(invalid_info)

    def test_get_supported_languages(self):
        langs = get_supported_languages()
        self.assertEqual(len(langs), len(SUPPORTED_LANGUAGES))
        ids = [l["id"] for l in langs]
        self.assertIn(71, ids)
        self.assertIn(54, ids)


if __name__ == "__main__":
    unittest.main()
