import unittest
from app.services.harness_service import HarnessService


class TestHarnessService(unittest.TestCase):
    def setUp(self):
        self.service = HarnessService()

    def test_function_name_detection(self):
        py_code = "def custom_solve(a, b): return a + b"
        self.assertEqual(self.service.detect_function_name(py_code, 71), "custom_solve")

        js_code = "function solveJs(arr) { return arr.length; }"
        self.assertEqual(self.service.detect_function_name(js_code, 63), "solveJs")

        js_const_code = "const solveConst = (x) => x * 2;"
        self.assertEqual(self.service.detect_function_name(js_const_code, 63), "solveConst")

        cpp_code = "int mySolution(vector<int>& nums) { return 0; }"
        self.assertEqual(self.service.detect_function_name(cpp_code, 54), "mySolution")

        no_func_code = "x = 42"
        self.assertEqual(self.service.detect_function_name(no_func_code, 71), "solution")

    def test_python_harness_dict_input(self):
        code = "def solve(x, y): return x + y"
        sample = {"x": 10, "y": 20}
        harness = self.service.build_harness(code, 71, sample)
        self.assertIn("import json", harness)
        self.assertIn("x = _input['x']", harness)
        self.assertIn("y = _input['y']", harness)
        self.assertIn("result = solve(", harness)
        self.assertIn("print(json.dumps(result))", harness)

    def test_python_harness_scalar_input(self):
        code = "def solve(n): return n * 2"
        sample = 5
        harness = self.service.build_harness(code, 71, sample)
        self.assertIn("import json", harness)
        self.assertIn("result = solve(_input)", harness)

    def test_javascript_harness_dict_input(self):
        code = "function solve(a, b) { return a + b; }"
        sample = {"a": 1, "b": 2}
        harness = self.service.build_harness(code, 63, sample)
        self.assertIn("const a = _input['a'];", harness)
        self.assertIn("console.log(JSON.stringify(result));", harness)

    def test_cpp_harness(self):
        code = "int solve(int n) { return n * 2; }"
        sample = 5
        harness = self.service.build_harness(code, 54, sample)
        self.assertIn("#include <bits/stdc++.h>", harness)
        self.assertNotIn("nlohmann/json.hpp", harness)
        self.assertIn("cout << _json::dump(result) << endl;", harness)

    def test_go_java_csharp_non_dict_harnesses(self):
        go_harness = self.service.build_harness("func solve(data []int) int { return 0 }", 60, [1, 2, 3])
        self.assertIn("var data []int", go_harness)
        self.assertNotIn("type Input struct", go_harness)

        java_harness = self.service.build_harness("public Object solve(int[] data) { return 0; }", 62, [1, 2, 3])
        self.assertIn("int[] _input = gson.fromJson(br.readLine(), int[].class);", java_harness)
        self.assertNotIn("JsonObject obj", java_harness)

        cs_harness = self.service.build_harness("public object Solve(int[] data) { return 0; }", 51, [1, 2, 3])
        self.assertIn("JToken.Parse(Console.ReadLine()).ToObject<int[]>()", cs_harness)
        self.assertNotIn("JObject.Parse", cs_harness)

    def test_unsupported_language_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.build_harness("print(1)", 99999, 1)


if __name__ == "__main__":
    unittest.main()
