import unittest
from funtions.usercode_evaluation import resolve_language_id


class TestLanguageMapping(unittest.TestCase):
    def test_direct_integer(self):
        self.assertEqual(resolve_language_id(71), 71)
        self.assertEqual(resolve_language_id(54), 54)

    def test_numeric_string(self):
        self.assertEqual(resolve_language_id("71"), 71)
        self.assertEqual(resolve_language_id(" 54 "), 54)

    def test_python_aliases(self):
        self.assertEqual(resolve_language_id("python"), 71)
        self.assertEqual(resolve_language_id("Python 3"), 71)
        self.assertEqual(resolve_language_id("python3"), 71)
        self.assertEqual(resolve_language_id("py"), 71)

    def test_cpp_aliases(self):
        self.assertEqual(resolve_language_id("cpp"), 54)
        self.assertEqual(resolve_language_id("c++"), 54)
        self.assertEqual(resolve_language_id("C++ 17"), 54)

    def test_js_ts_java(self):
        self.assertEqual(resolve_language_id("javascript"), 63)
        self.assertEqual(resolve_language_id("js"), 63)
        self.assertEqual(resolve_language_id("typescript"), 74)
        self.assertEqual(resolve_language_id("ts"), 74)
        self.assertEqual(resolve_language_id("java"), 62)

    def test_unsupported_language_raises_error(self):
        with self.assertRaises(ValueError):
            resolve_language_id("brainfuck")
        with self.assertRaises(ValueError):
            resolve_language_id("non_existent_lang")


if __name__ == "__main__":
    unittest.main()
