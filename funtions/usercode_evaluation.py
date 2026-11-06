# import requests
# import json
# import re

# # ─── Type Inference from Python values ───────────────────────────────────────

# def infer_type(val):
#     if isinstance(val, bool):
#         return {"base": "bool"}
#     elif isinstance(val, int):
#         return {"base": "int"}
#     elif isinstance(val, float):
#         return {"base": "float"}
#     elif isinstance(val, str):
#         return {"base": "string"}
#     elif isinstance(val, list):
#         if len(val) == 0:
#             return {"base": "list", "of": {"base": "int"}}
#         inner = infer_type(val[0])
#         return {"base": "list", "of": inner}
#     elif isinstance(val, dict):
#         return {"base": "dict"}
#     return {"base": "any"}


# # ─── Harness Classes ──────────────────────────────────────────────────────────

# class PythonHarness:
#     def parse(self, k, t):
#         return f"{k} = _input['{k}']"

#     def call(self, func_name, input_keys):
#         kwargs = ", ".join(f'"{k}": {k}' for k in input_keys)
#         return f"result = {func_name}(**{{{kwargs}}})"

#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         parse_lines = "\n".join(self.parse(k, None) for k in input_keys)
#         return (
#             "import json\n"
#             "_input = json.loads(input())\n"
#             f"{parse_lines}\n\n"
#             f"{usercode}\n\n"
#             f"{self.call(func_name, input_keys)}\n"
#             "print(json.dumps(result))"
#         )


# class JavaScriptHarness:
#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         parse_lines = "\n".join(f"const {k} = _input['{k}'];" for k in input_keys)
#         call        = f"const result = {func_name}({', '.join(input_keys)});"
#         return (
#             "const _input = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8').trim());\n"
#             f"{parse_lines}\n\n"
#             f"{usercode}\n\n"
#             f"{call}\n"
#             "console.log(JSON.stringify(result));"
#         )


# class TypeScriptHarness:
#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         parse_lines = "\n".join(f"const {k} = _input['{k}'];" for k in input_keys)
#         call        = f"const result = {func_name}({', '.join(input_keys)});"
#         return (
#             "import * as fs from 'fs';\n"
#             "const _input: any = JSON.parse(fs.readFileSync('/dev/stdin','utf8').trim());\n"
#             f"{parse_lines}\n\n"
#             f"{usercode}\n\n"
#             f"{call}\n"
#             "console.log(JSON.stringify(result));"
#         )


# class RubyHarness:
#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         parse_lines = "\n".join(f"{k} = _input['{k}']" for k in input_keys)
#         call        = f"result = {func_name}({', '.join(input_keys)})"
#         return (
#             "require 'json'\n"
#             "_input = JSON.parse(gets.chomp)\n"
#             f"{parse_lines}\n\n"
#             f"{usercode}\n\n"
#             f"{call}\n"
#             "puts result.to_json"
#         )


# class GoHarness:
#     GO_TYPES = {
#         "bool":   "bool",
#         "int":    "int",
#         "float":  "float64",
#         "string": "string",
#     }

#     def go_type(self, t):
#         base = t["base"]
#         if base == "list":
#             return f"[]{self.go_type(t['of'])}"
#         return self.GO_TYPES.get(base, "interface{}")

#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         types  = {k: infer_type(input_dict[k]) for k in input_keys}
#         fields = "\n\t".join(
#             f'{k.capitalize()} {self.go_type(types[k])} `json:"{k}"`'
#             for k in input_keys
#         )
#         decls = "\n\t".join(f"{k} := inp.{k.capitalize()}" for k in input_keys)
#         call  = f"result := {func_name}({', '.join(input_keys)})"

#         return f"""package main

# import (
#     "encoding/json"
#     "fmt"
#     "os"
# )

# type Input struct {{
#     {fields}
# }}

# {usercode}

# func main() {{
#     var inp Input
#     json.NewDecoder(os.Stdin).Decode(&inp)
#     {decls}
#     {call}
#     out, _ := json.Marshal(result)
#     fmt.Println(string(out))
# }}
# """


# class JavaHarness:
#     def java_type(self, t):
#         base = t["base"]
#         if base == "list":
#             inner = t["of"]["base"]
#             if inner == "int":    return "int[]"
#             if inner == "float":  return "double[]"
#             if inner == "string": return "String[]"
#             if inner == "list":   return "int[][]"
#         return {"int": "int", "float": "double",
#                 "string": "String", "bool": "boolean"}.get(base, "Object")

#     def java_parse(self, k, t):
#         base = t["base"]
#         if base == "list":
#             inner = t["of"]["base"]
#             if inner == "int":    return f'int[] {k} = gson.fromJson(obj.get("{k}"), int[].class);'
#             if inner == "float":  return f'double[] {k} = gson.fromJson(obj.get("{k}"), double[].class);'
#             if inner == "string": return f'String[] {k} = gson.fromJson(obj.get("{k}"), String[].class);'
#             if inner == "list":   return f'int[][] {k} = gson.fromJson(obj.get("{k}"), int[][].class);'
#         if base == "int":    return f'int {k} = obj.get("{k}").getAsInt();'
#         if base == "float":  return f'double {k} = obj.get("{k}").getAsDouble();'
#         if base == "string": return f'String {k} = obj.get("{k}").getAsString();'
#         if base == "bool":   return f'boolean {k} = obj.get("{k}").getAsBoolean();'
#         return f'Object {k} = obj.get("{k}");'

#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         types       = {k: infer_type(input_dict[k]) for k in input_keys}
#         parse_lines = "\n        ".join(self.java_parse(k, types[k]) for k in input_keys)
#         call        = ", ".join(input_keys)

#         return f"""import com.google.gson.*;
# import java.util.*;
# import java.io.*;

# public class Main {{
#     {usercode}

#     public static void main(String[] args) throws Exception {{
#         Gson gson = new Gson();
#         BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
#         JsonObject obj = gson.fromJson(br.readLine(), JsonObject.class);
#         {parse_lines}
#         Object result = new Main().{func_name}({call});
#         System.out.println(gson.toJson(result));
#     }}
# }}
# """


# class CppHarness:
#     def cpp_type(self, t):
#         base = t["base"]
#         if base == "list":
#             return f"vector<{self.cpp_type(t['of'])}>"
#         return {"int": "int", "float": "double",
#                 "string": "string", "bool": "bool"}.get(base, "auto")

#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         types = {k: infer_type(input_dict[k]) for k in input_keys}
#         decls = "\n    ".join(
#             f"{self.cpp_type(types[k])} {k} = j[\"{k}\"];"
#             for k in input_keys
#         )
#         call = ", ".join(input_keys)

#         return f"""#include <bits/stdc++.h>
# #include <nlohmann/json.hpp>
# using json = nlohmann::json;
# using namespace std;

# {usercode}

# int main() {{
#     string line;
#     getline(cin, line);
#     json j = json::parse(line);
#     {decls}
#     auto result = {func_name}({call});
#     cout << json(result).dump() << endl;
#     return 0;
# }}
# """


# class CSharpHarness:
#     def cs_type(self, t):
#         base = t["base"]
#         if base == "list":
#             return f"{self.cs_type(t['of'])}[]"
#         return {"int": "int", "float": "double",
#                 "string": "string", "bool": "bool"}.get(base, "object")

#     def cs_parse(self, k, t):
#         base = t["base"]
#         if base == "list":
#             return f'var {k} = obj["{k}"].ToObject<{self.cs_type(t)}>();'
#         if base == "int":    return f'int {k} = obj["{k}"].Value<int>();'
#         if base == "float":  return f'double {k} = obj["{k}"].Value<double>();'
#         if base == "string": return f'string {k} = obj["{k}"].Value<string>();'
#         if base == "bool":   return f'bool {k} = obj["{k}"].Value<bool>();'
#         return f'var {k} = obj["{k}"];'

#     def wrap(self, usercode, input_keys, input_dict, func_name):
#         types       = {k: infer_type(input_dict[k]) for k in input_keys}
#         parse_lines = "\n            ".join(self.cs_parse(k, types[k]) for k in input_keys)
#         call        = ", ".join(input_keys)

#         return f"""using System;
# using Newtonsoft.Json;
# using Newtonsoft.Json.Linq;

# public class Solution {{
#     {usercode}

#     static void Main() {{
#         JObject obj = JObject.Parse(Console.ReadLine());
#         {parse_lines}
#         var result = new Solution().{func_name}({call});
#         Console.WriteLine(JsonConvert.SerializeObject(result));
#     }}
# }}
# """


# # ─── Registry ─────────────────────────────────────────────────────────────────

# HARNESS_REGISTRY = {
#     71: PythonHarness(),
#     63: JavaScriptHarness(),
#     74: TypeScriptHarness(),
#     72: RubyHarness(),
#     60: GoHarness(),
#     62: JavaHarness(),
#     54: CppHarness(), 53: CppHarness(), 52: CppHarness(),
#     51: CSharpHarness(),
# }

# FUNC_PATTERNS = {
#     71: r'def\s+(\w+)\s*\(',
#     63: r'(?:function\s+(\w+)|const\s+(\w+)\s*=)',
#     74: r'(?:function\s+(\w+)|const\s+(\w+)\s*=)',
#     72: r'def\s+(\w+)\s*\(',
#     60: r'func\s+(\w+)\s*\(',
#     62: r'(?:public|private|protected)\s+\S+\s+(\w+)\s*\(',
#     54: r'\w[\w<>]*\s+(\w+)\s*\(',
#     53: r'\w[\w<>]*\s+(\w+)\s*\(',
#     51: r'(?:public|private)\s+\S+\s+(\w+)\s*\(',
# }


# # ─── Function Name Detector ───────────────────────────────────────────────────

# def detect_func_name(usercode, language_id):
#     pattern = FUNC_PATTERNS.get(language_id, r'(\w+)\s*\(')
#     match   = re.search(pattern, usercode)
#     if match:
#         return next((g for g in match.groups() if g), "solution")
#     return "solution"


# # ─── Main Evaluator ───────────────────────────────────────────────────────────

# def usercode_evaluation(usercode, testcases, language_id):
#     harness_builder = HARNESS_REGISTRY.get(language_id)
#     if not harness_builder:
#         return {"status": "Error", "message": f"Language ID {language_id} not supported yet"}

#     func_name    = detect_func_name(usercode, language_id)
#     sample_input = testcases[0]['input']
#     input_keys   = list(sample_input.keys())

#     # Build harness ONCE, reuse for all testcases
#     harness = harness_builder.wrap(usercode, input_keys, sample_input, func_name)

#     print(f"✅ Harness built for language={language_id}, func='{func_name}'")
#     print(f"🚀 Running {len(testcases)} testcases...\n")

#     for i, tc in enumerate(testcases):
#         input_dict = tc['input']
#         expected   = tc['expected_output']

#         res = requests.post(
#             "https://ce.judge0.com/submissions?wait=true",
#             headers={"Content-Type": "application/json"},
#             json={
#                 "language_id": language_id,
#                 "source_code": harness,
#                 "stdin":       json.dumps(input_dict)
#             }
#         )

#         data   = res.json()
#         status = data["status"]["description"]

#         # ── Compilation / Syntax Error → stop immediately ──────────────
#         if status == "Compilation Error":
#             return {
#                 "status":  "Compilation Error",
#                 "message": "Fix your code before running test cases.",
#                 "error":   data.get("compile_output", "Unknown compile error")
#             }

#         # ── Runtime Error → stop immediately ───────────────────────────
#         if status in ("Runtime Error (NZEC)", "Runtime Error (SIGSEGV)",
#                       "Runtime Error (SIGFPE)", "Runtime Error (SIGABRT)",
#                       "Runtime Error (Other)"):
#             return {
#                 "status":   status,
#                 "testcase": i + 1,
#                 "input":    input_dict,
#                 "message":  f"Runtime error on testcase {i + 1}.",
#                 "error":    data.get("stderr", "Unknown runtime error")
#             }

#         # ── Time Limit Exceeded → stop immediately ──────────────────────
#         if status == "Time Limit Exceeded":
#             return {
#                 "status":   "Time Limit Exceeded",
#                 "testcase": i + 1,
#                 "input":    input_dict,
#                 "message":  f"Time limit exceeded on testcase {i + 1}. Optimize your code."
#             }

#         # ── Any other non-accepted status → stop immediately ────────────
#         if status != "Accepted":
#             return {
#                 "status":   status,
#                 "testcase": i + 1,
#                 "input":    input_dict,
#                 "message":  f"Unexpected error on testcase {i + 1}.",
#                 "error":    data.get("stderr") or data.get("compile_output") or "Unknown error"
#             }

#         # ── Accepted → parse output ─────────────────────────────────────
#         try:
#             actual = json.loads(data["stdout"].strip())
#         except Exception as e:
#             return {
#                 "status":   "Output Parse Error",
#                 "testcase": i + 1,
#                 "input":    input_dict,
#                 "message":  f"Could not parse output on testcase {i + 1}.",
#                 "error":    str(e),
#                 "raw":      data["stdout"].strip()
#             }

#         # ── Wrong Answer → stop immediately ────────────────────────────
#         if actual != expected:
#             return {
#                 "status":   "Wrong Answer",
#                 "testcase": i + 1,
#                 "input":    input_dict,
#                 "expected": expected,
#                 "actual":   actual,
#                 "message":  f"Wrong answer on testcase {i + 1}."
#             }

#         print(f"  ✅ TC {i + 1} passed")

#     # ── All passed ──────────────────────────────────────────────────────
#     return {
#         "status":  "All Passed",
#         "message": f"All {len(testcases)} testcases passed! 🎉"
#     }


# # ─── Pretty Print ─────────────────────────────────────────────────────────────

# def print_results(result):
#     print("\n" + "=" * 50)

#     if result["status"] == "All Passed":
#         print(f"🎉 {result['message']}")

#     elif result["status"] == "Compilation Error":
#         print(f"❌ Compilation Error — fix your code first!")
#         print(f"   {result['error']}")

#     elif result["status"] == "Wrong Answer":
#         print(f"❌ Wrong Answer on Testcase {result['testcase']}")
#         print(f"   Input    : {result['input']}")
#         print(f"   Expected : {result['expected']}")
#         print(f"   Got      : {result['actual']}")

#     elif result["status"] == "Time Limit Exceeded":
#         print(f"⏱️  Time Limit Exceeded on Testcase {result['testcase']}")
#         print(f"   Input    : {result['input']}")
#         print(f"   Message  : {result['message']}")

#     elif "Runtime Error" in result["status"]:
#         print(f"💥 {result['status']} on Testcase {result['testcase']}")
#         print(f"   Input    : {result['input']}")
#         print(f"   Error    : {result['error']}")

#     elif result["status"] == "Output Parse Error":
#         print(f"⚠️  Output Parse Error on Testcase {result['testcase']}")
#         print(f"   Error    : {result['error']}")
#         print(f"   Raw      : {result['raw']}")

#     else:
#         print(f"❌ {result['status']}: {result.get('message', '')}")
#         if "error" in result:
#             print(f"   Error    : {result['error']}")

#     print("=" * 50)


# # ─── Run ──────────────────────────────────────────────────────────────────────

# user_code = """vector<int> optimal_solve(vector<int>& nums, int target) {
#     unordered_map<int, int> num_dict;
#     for (int i = 0; i < nums.size(); i++) {
#         int complement = target - nums[i];
#         if (num_dict.find(complement) != num_dict.end()) {
#             return {num_dict[complement], i};
#         }
#         num_dict[nums[i]] = i;
#     }
#     return {};
# }"""

# final_testcases = [
#     {'input': {'target': 9,'nums': [2, 7, 11, 15]},           'expected_output': [1, 1]},
#     {'input': {'nums': [3, 2, 4],        'target': 6},           'expected_output': [1, 2]},
#     {'input': {'nums': [3, 3],           'target': 6},           'expected_output': [0, 1]},
#     {'input': {'nums': [-1, 0, 1],       'target': 0},           'expected_output': [0, 2]},
#     {'input': {'nums': [0, 0, 3],        'target': 0},           'expected_output': [0, 1]},
#     {'input': {'nums': [5, 7, 11, 15],   'target': 12},          'expected_output': [0, 1]},
#     {'input': {'nums': [1000000000, 1000000000, 1000000000],     'target': 2000000000},  'expected_output': [0, 1]},
#     {'input': {'nums': [-1000000000, -1000000000, -1000000000],  'target': -2000000000}, 'expected_output': [0, 1]},
#     {'input': {'nums': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],          'target': 2},           'expected_output': [0, 1]},
#     {'input': {'nums': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],          'target': 0},           'expected_output': [0, 1]},
#     {'input': {'nums': [1000000000, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 1000000000},  'expected_output': [0, 1]},
#     {'input': {'nums': [1000000000, 1000000000, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 2000000000}, 'expected_output': [0, 1]},
#     {'input': {'nums': [0, 0, 0, 0, 0, 0, 0, 0, 1000000000, 1000000000], 'target': 2000000000}, 'expected_output': [8, 9]},
#     {'input': {'nums': [-1000000000, 1000000000, 0, 0, 0, 0, 0, 0, 0, 0], 'target': 0}, 'expected_output': [0, 1]},
# ]

# language_id = 54

# result = usercode_evaluation(user_code, final_testcases, language_id)
# print(result)


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import requests
import json
import re

app = FastAPI(title="Code Judge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your frontend domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

JUDGE0_URL = "https://ce.judge0.com/submissions?wait=true"
JUDGE0_HEADERS = {"Content-Type": "application/json"}

# ─── Models ───────────────────────────────────────────────────────────────────

class TestCase(BaseModel):
    input: dict[str, Any]
    expected_output: Any

class JudgeRequest(BaseModel):
    code: str
    testcases: list[TestCase]
    language_id: int

# ─── Type Inference ───────────────────────────────────────────────────────────

def infer_type(val):
    if isinstance(val, bool):   return {"base": "bool"}
    if isinstance(val, int):    return {"base": "int"}
    if isinstance(val, float):  return {"base": "float"}
    if isinstance(val, str):    return {"base": "string"}
    if isinstance(val, list):
        inner = infer_type(val[0]) if val else {"base": "int"}
        return {"base": "list", "of": inner}
    if isinstance(val, dict):   return {"base": "dict"}
    return {"base": "any"}

# ─── Harness Builders ─────────────────────────────────────────────────────────

class PythonHarness:
    def build(self, code, keys, sample, fn):
        parse = "\n".join(f"{k} = _input['{k}']" for k in keys)
        call  = f"result = {fn}(**{{{', '.join(f'\"{ k}\": {k}' for k in keys)}}})"
        return (
            "import json\n_input = json.loads(input())\n"
            f"{parse}\n\n{code}\n\n{call}\nprint(json.dumps(result))"
        )

class JavaScriptHarness:
    def build(self, code, keys, sample, fn):
        parse = "\n".join(f"const {k} = _input['{k}'];" for k in keys)
        call  = f"const result = {fn}({', '.join(keys)});"
        return (
            "const _input = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8').trim());\n"
            f"{parse}\n\n{code}\n\n{call}\nconsole.log(JSON.stringify(result));"
        )

class TypeScriptHarness:
    def build(self, code, keys, sample, fn):
        parse = "\n".join(f"const {k} = _input['{k}'];" for k in keys)
        call  = f"const result = {fn}({', '.join(keys)});"
        return (
            "import * as fs from 'fs';\n"
            "const _input: any = JSON.parse(fs.readFileSync('/dev/stdin','utf8').trim());\n"
            f"{parse}\n\n{code}\n\n{call}\nconsole.log(JSON.stringify(result));"
        )

class RubyHarness:
    def build(self, code, keys, sample, fn):
        parse = "\n".join(f"{k} = _input['{k}']" for k in keys)
        call  = f"result = {fn}({', '.join(keys)})"
        return (
            "require 'json'\n_input = JSON.parse(gets.chomp)\n"
            f"{parse}\n\n{code}\n\n{call}\nputs result.to_json"
        )

class GoHarness:
    GO_TYPES = {"bool": "bool", "int": "int", "float": "float64", "string": "string"}

    def go_type(self, t):
        if t["base"] == "list": return f"[]{self.go_type(t['of'])}"
        return self.GO_TYPES.get(t["base"], "interface{}")

    def build(self, code, keys, sample, fn):
        types  = {k: infer_type(sample[k]) for k in keys}
        fields = "\n\t".join(
            f'{k.capitalize()} {self.go_type(types[k])} `json:"{k}"`' for k in keys
        )
        decls = "\n\t".join(f"{k} := inp.{k.capitalize()}" for k in keys)
        call  = f"result := {fn}({', '.join(keys)})"
        return f"""package main
import ("encoding/json"; "fmt"; "os")
type Input struct {{ {fields} }}
{code}
func main() {{
    var inp Input
    json.NewDecoder(os.Stdin).Decode(&inp)
    {decls}
    {call}
    out, _ := json.Marshal(result)
    fmt.Println(string(out))
}}"""

class JavaHarness:
    def java_type(self, t):
        b = t["base"]
        if b == "list":
            inner = t["of"]["base"]
            return {"int":"int[]","float":"double[]","string":"String[]","list":"int[][]"}.get(inner,"Object[]")
        return {"int":"int","float":"double","string":"String","bool":"boolean"}.get(b,"Object")

    def java_parse(self, k, t):
        b = t["base"]
        if b == "list":
            inner = t["of"]["base"]
            cls = {"int":"int[]","float":"double[]","string":"String[]","list":"int[][]"}.get(inner,"Object[]")
            return f'{cls} {k} = gson.fromJson(obj.get("{k}"), {cls}.class);'
        if b == "int":    return f'int {k} = obj.get("{k}").getAsInt();'
        if b == "float":  return f'double {k} = obj.get("{k}").getAsDouble();'
        if b == "string": return f'String {k} = obj.get("{k}").getAsString();'
        if b == "bool":   return f'boolean {k} = obj.get("{k}").getAsBoolean();'
        return f'Object {k} = obj.get("{k}");'

    def build(self, code, keys, sample, fn):
        types  = {k: infer_type(sample[k]) for k in keys}
        parse  = "\n        ".join(self.java_parse(k, types[k]) for k in keys)
        call   = ", ".join(keys)
        return f"""import com.google.gson.*; import java.util.*; import java.io.*;
public class Main {{
    {code}
    public static void main(String[] args) throws Exception {{
        Gson gson = new Gson();
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        JsonObject obj = gson.fromJson(br.readLine(), JsonObject.class);
        {parse}
        Object result = new Main().{fn}({call});
        System.out.println(gson.toJson(result));
    }}
}}"""

class CppHarness:
    def cpp_type(self, t):
        if t["base"] == "list": return f"vector<{self.cpp_type(t['of'])}>"
        return {"int":"int","float":"double","string":"string","bool":"bool"}.get(t["base"],"auto")

    def build(self, code, keys, sample, fn):
        types = {k: infer_type(sample[k]) for k in keys}
        decls = "\n    ".join(f"{self.cpp_type(types[k])} {k} = j[\"{k}\"];" for k in keys)
        return f"""#include <bits/stdc++.h>
#include <nlohmann/json.hpp>
using json = nlohmann::json;
using namespace std;

{code}

int main() {{
    string line;
    getline(cin, line);
    json j = json::parse(line);
    {decls}
    auto result = {fn}({', '.join(keys)});
    cout << json(result).dump() << endl;
    return 0;
}}"""

class CSharpHarness:
    def cs_type(self, t):
        if t["base"] == "list": return f"{self.cs_type(t['of'])}[]"
        return {"int":"int","float":"double","string":"string","bool":"bool"}.get(t["base"],"object")

    def cs_parse(self, k, t):
        b = t["base"]
        if b == "list":   return f'var {k} = obj["{k}"].ToObject<{self.cs_type(t)}>();'
        if b == "int":    return f'int {k} = obj["{k}"].Value<int>();'
        if b == "float":  return f'double {k} = obj["{k}"].Value<double>();'
        if b == "string": return f'string {k} = obj["{k}"].Value<string>();'
        if b == "bool":   return f'bool {k} = obj["{k}"].Value<bool>();'
        return f'var {k} = obj["{k}"];'

    def build(self, code, keys, sample, fn):
        types = {k: infer_type(sample[k]) for k in keys}
        parse = "\n            ".join(self.cs_parse(k, types[k]) for k in keys)
        return f"""using System; using Newtonsoft.Json; using Newtonsoft.Json.Linq;
public class Solution {{
    {code}
    static void Main() {{
        JObject obj = JObject.Parse(Console.ReadLine());
        {parse}
        var result = new Solution().{fn}({', '.join(keys)});
        Console.WriteLine(JsonConvert.SerializeObject(result));
    }}
}}"""

# ─── Registry & Func Detection ────────────────────────────────────────────────

HARNESS_REGISTRY = {
    71: PythonHarness(),
    63: JavaScriptHarness(),
    74: TypeScriptHarness(),
    72: RubyHarness(),
    60: GoHarness(),
    62: JavaHarness(),
    54: CppHarness(), 53: CppHarness(), 52: CppHarness(),
    51: CSharpHarness(),
}

FUNC_PATTERNS = {
    71: r'def\s+(\w+)\s*\(',
    63: r'(?:function\s+(\w+)|const\s+(\w+)\s*=)',
    74: r'(?:function\s+(\w+)|const\s+(\w+)\s*=)',
    72: r'def\s+(\w+)\s*\(',
    60: r'func\s+(\w+)\s*\(',
    62: r'(?:public|private|protected)\s+\S+\s+(\w+)\s*\(',
    54: r'\w[\w<>]*\s+(\w+)\s*\(',
    53: r'\w[\w<>]*\s+(\w+)\s*\(',
    51: r'(?:public|private)\s+\S+\s+(\w+)\s*\(',
}

def detect_func_name(code: str, language_id: int) -> str:
    pattern = FUNC_PATTERNS.get(language_id, r'(\w+)\s*\(')
    m = re.search(pattern, code)
    if m:
        return next((g for g in m.groups() if g), "solution")
    return "solution"

# ─── Judge0 Submission ────────────────────────────────────────────────────────

def submit_to_judge0(source_code: str, language_id: int, stdin: str) -> dict:
    try:
        res = requests.post(
            JUDGE0_URL,
            headers=JUDGE0_HEADERS,
            json={"language_id": language_id, "source_code": source_code, "stdin": stdin},
            timeout=30,
        )
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Judge0 unreachable: {str(e)}")

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "Code Judge API is running"}


@app.get("/languages")
def get_languages():
    return {
        "languages": [
            {"id": 71,  "name": "Python 3"},
            {"id": 54,  "name": "C++ 17"},
            {"id": 63,  "name": "JavaScript (Node.js)"},
            {"id": 74,  "name": "TypeScript"},
            {"id": 62,  "name": "Java"},
            {"id": 72,  "name": "Ruby"},
            {"id": 60,  "name": "Go"},
            {"id": 51,  "name": "C#"},
        ]
    }


@app.post("/judge")
def judge(req: JudgeRequest):
    harness_builder = HARNESS_REGISTRY.get(req.language_id)
    if not harness_builder:
        raise HTTPException(status_code=400, detail=f"Language ID {req.language_id} not supported")

    if not req.testcases:
        raise HTTPException(status_code=400, detail="At least one test case is required")

    sample    = req.testcases[0].input
    keys      = list(sample.keys())
    fn        = detect_func_name(req.code, req.language_id)
    harness   = harness_builder.build(req.code, keys, sample, fn)

    results   = []
    passed    = 0

    for i, tc in enumerate(req.testcases):
        data   = submit_to_judge0(harness, req.language_id, json.dumps(tc.input))
        status = data["status"]["description"]

        # ── Compilation Error → stop immediately ──
        if status == "Compilation Error":
            results.append({
                "testcase": i + 1,
                "status":   "Compilation Error",
                "error":    data.get("compile_output", "").strip(),
                "passed":   False,
            })
            break

        # ── Runtime Error → stop immediately ──
        if "Runtime Error" in status:
            results.append({
                "testcase": i + 1,
                "status":   status,
                "error":    (data.get("stderr") or "").strip(),
                "input":    tc.input,
                "passed":   False,
            })
            break

        # ── TLE → stop immediately ──
        if status == "Time Limit Exceeded":
            results.append({
                "testcase": i + 1,
                "status":   "Time Limit Exceeded",
                "input":    tc.input,
                "passed":   False,
            })
            break

        # ── Other non-accepted ──
        if status != "Accepted":
            results.append({
                "testcase": i + 1,
                "status":   status,
                "error":    (data.get("stderr") or data.get("compile_output") or "").strip(),
                "passed":   False,
            })
            break

        # ── Parse output ──
        try:
            actual = json.loads(data["stdout"].strip())
        except Exception as e:
            results.append({
                "testcase": i + 1,
                "status":   "Output Parse Error",
                "error":    str(e),
                "raw":      data["stdout"].strip(),
                "passed":   False,
            })
            break

        # ── Compare ──
        is_correct = actual == tc.expected_output
        if is_correct:
            passed += 1

        results.append({
            "testcase": i + 1,
            "status":   "Accepted" if is_correct else "Wrong Answer",
            "input":    tc.input,
            "expected": tc.expected_output,
            "actual":   actual,
            "passed":   is_correct,
            "time":     data.get("time"),
            "memory":   data.get("memory"),
        })

        if not is_correct:
            break   # stop on first wrong answer (change to `continue` to run all)

    return {
        "summary": {
            "passed":  passed,
            "total":   len(req.testcases),
            "ran":     len(results),
            "verdict": "All Passed" if passed == len(req.testcases) else results[-1]["status"],
        },
        "results": results,
        "detected_function": fn,
    }