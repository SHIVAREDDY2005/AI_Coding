import json
import os
import re
from typing import Any, Union
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

load_dotenv()

JUDGE0_URL = os.getenv("JUDGE0_URL", "https://ce.judge0.com/submissions?wait=true")
JUDGE0_HEADERS = {"Content-Type": "application/json"}

app = FastAPI(title="Code Judge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Language Mapping ─────────────────────────────────────────────────────────

LANGUAGE_NAME_TO_ID = {
    "python": 71,
    "python 3": 71,
    "python3": 71,
    "py": 71,
    "c++": 54,
    "cpp": 54,
    "c++ 17": 54,
    "c++17": 54,
    "javascript": 63,
    "js": 63,
    "node": 63,
    "nodejs": 63,
    "typescript": 74,
    "ts": 74,
    "java": 62,
    "ruby": 72,
    "rb": 72,
    "go": 60,
    "golang": 60,
    "c#": 51,
    "csharp": 51,
    "cs": 51,
}


def resolve_language_id(language: Union[int, str]) -> int:
    """
    Maps language strings (e.g., 'Python 3', 'cpp', '71') to Judge0 language IDs.
    """
    if isinstance(language, int):
        return language
    if isinstance(language, str):
        cleaned = language.strip().lower()
        if cleaned.isdigit():
            return int(cleaned)
        if cleaned in LANGUAGE_NAME_TO_ID:
            return LANGUAGE_NAME_TO_ID[cleaned]
    raise ValueError(f"Unsupported or unrecognized language: '{language}'")


# ─── Models ───────────────────────────────────────────────────────────────────

class TestCase(BaseModel):
    input: Any
    expected_output: Any


class JudgeRequest(BaseModel):
    code: str
    testcases: list[TestCase]
    language_id: Union[int, str]


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
        if isinstance(sample, dict):
            parse = "\n".join(f"{k} = _input['{k}']" for k in keys)
            call  = f"result = {fn}(**{{{', '.join(f'\"{k}\": {k}' for k in keys)}}})"
        else:
            parse = ""
            call  = f"result = {fn}(_input)"
        return (
            "import json\n_input = json.loads(input())\n"
            f"{parse}\n\n{code}\n\n{call}\nprint(json.dumps(result))"
        )


class JavaScriptHarness:
    def build(self, code, keys, sample, fn):
        if isinstance(sample, dict):
            parse = "\n".join(f"const {k} = _input['{k}'];" for k in keys)
            call  = f"const result = {fn}({', '.join(keys)});"
        else:
            parse = ""
            call  = f"const result = {fn}(_input);"
        return (
            "const _input = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8').trim());\n"
            f"{parse}\n\n{code}\n\n{call}\nconsole.log(JSON.stringify(result));"
        )


class TypeScriptHarness:
    def build(self, code, keys, sample, fn):
        if isinstance(sample, dict):
            parse = "\n".join(f"const {k} = _input['{k}'];" for k in keys)
            call  = f"const result = {fn}({', '.join(keys)});"
        else:
            parse = ""
            call  = f"const result = {fn}(_input);"
        return (
            "import * as fs from 'fs';\n"
            "const _input: any = JSON.parse(fs.readFileSync('/dev/stdin','utf8').trim());\n"
            f"{parse}\n\n{code}\n\n{call}\nconsole.log(JSON.stringify(result));"
        )


class RubyHarness:
    def build(self, code, keys, sample, fn):
        if isinstance(sample, dict):
            parse = "\n".join(f"{k} = _input['{k}']" for k in keys)
            call  = f"result = {fn}({', '.join(keys)})"
        else:
            parse = ""
            call  = f"result = {fn}(_input)"
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
        if isinstance(sample, dict):
            types  = {k: infer_type(sample[k]) for k in keys}
            fields = "\n\t".join(
                f'{k.capitalize()} {self.go_type(types[k])} `json:"{k}"`' for k in keys
            )
            decls = "\n\t".join(f"{k} := inp.{k.capitalize()}" for k in keys)
            call  = f"result := {fn}({', '.join(keys)})"
        else:
            fields = 'Data interface{} `json:"data"`'
            decls = "data := inp.Data"
            call = f"result := {fn}(data)"
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
        if isinstance(sample, dict):
            types  = {k: infer_type(sample[k]) for k in keys}
            parse  = "\n        ".join(self.java_parse(k, types[k]) for k in keys)
            call   = ", ".join(keys)
        else:
            parse = "Object _input = gson.fromJson(br.readLine(), Object.class);"
            call = "_input"
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
        if isinstance(sample, dict):
            types = {k: infer_type(sample[k]) for k in keys}
            decls = "\n    ".join(f"{self.cpp_type(types[k])} {k} = j[\"{k}\"];" for k in keys)
            call = ", ".join(keys)
        else:
            decls = "auto _input = j;"
            call = "_input"
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
    auto result = {fn}({call});
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
        if isinstance(sample, dict):
            types = {k: infer_type(sample[k]) for k in keys}
            parse = "\n            ".join(self.cs_parse(k, types[k]) for k in keys)
            call  = ", ".join(keys)
        else:
            parse = "var _input = obj;"
            call = "_input"
        return f"""using System; using Newtonsoft.Json; using Newtonsoft.Json.Linq;
public class Solution {{
    {code}
    static void Main() {{
        JObject obj = JObject.Parse(Console.ReadLine());
        {parse}
        var result = new Solution().{fn}({call});
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
    54: CppHarness(),
    53: CppHarness(),
    52: CppHarness(),
    51: CSharpHarness(),
}

FUNC_PATTERNS = {
    71: r'def\s+(\w+)\s*\(',
    63: r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)',
    74: r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)',
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

def submit_to_judge0(source_code: str, language_id: int, stdin: str, url: str = JUDGE0_URL, headers: dict = None) -> dict:
    if headers is None:
        headers = JUDGE0_HEADERS
    try:
        res = requests.post(
            url,
            headers=headers,
            json={"language_id": language_id, "source_code": source_code, "stdin": stdin},
            timeout=30,
        )
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Judge0 unreachable: {str(e)}")


# ─── Core Reusable Evaluator ─────────────────────────────────────────────────

def evaluate_user_code(
    code: str,
    testcases: list,
    language: Union[int, str],
    judge0_url: str = JUDGE0_URL,
    judge0_headers: dict = None
) -> dict:
    """
    Evaluates user code against test cases using Judge0.
    Can be called directly from CLI or through API routes.
    """
    if judge0_headers is None:
        judge0_headers = JUDGE0_HEADERS

    language_id = resolve_language_id(language)
    harness_builder = HARNESS_REGISTRY.get(language_id)
    if not harness_builder:
        raise ValueError(f"Language ID {language_id} not supported by execution harness")

    if not testcases:
        raise ValueError("At least one testcase is required for evaluation")

    # Normalize testcases to uniform dicts
    normalized_tests = []
    for tc in testcases:
        if isinstance(tc, dict):
            inp = tc.get("input")
            exp = tc.get("expected_output", tc.get("expected"))
        elif hasattr(tc, "input") and hasattr(tc, "expected_output"):
            inp = tc.input
            exp = tc.expected_output
        else:
            continue
        normalized_tests.append({"input": inp, "expected_output": exp})

    if not normalized_tests:
        raise ValueError("No valid test cases found to evaluate")

    sample = normalized_tests[0]["input"]
    keys = list(sample.keys()) if isinstance(sample, dict) else []
    fn = detect_func_name(code, language_id)
    harness = harness_builder.build(code, keys, sample, fn)

    results = []
    passed = 0

    for i, tc in enumerate(normalized_tests):
        data = submit_to_judge0(harness, language_id, json.dumps(tc["input"]), url=judge0_url, headers=judge0_headers)
        status = data.get("status", {}).get("description", "Unknown")

        # Compilation Error → stop immediately
        if status == "Compilation Error":
            results.append({
                "testcase": i + 1,
                "status": "Compilation Error",
                "error": data.get("compile_output", "").strip(),
                "passed": False,
            })
            break

        # Runtime Error → stop immediately
        if "Runtime Error" in status:
            results.append({
                "testcase": i + 1,
                "status": status,
                "error": (data.get("stderr") or "").strip(),
                "input": tc["input"],
                "passed": False,
            })
            break

        # TLE → stop immediately
        if status == "Time Limit Exceeded":
            results.append({
                "testcase": i + 1,
                "status": "Time Limit Exceeded",
                "input": tc["input"],
                "passed": False,
            })
            break

        # Other non-accepted status
        if status != "Accepted":
            results.append({
                "testcase": i + 1,
                "status": status,
                "error": (data.get("stderr") or data.get("compile_output") or "").strip(),
                "passed": False,
            })
            break

        # Parse output
        raw_stdout = data.get("stdout") or ""
        try:
            actual = json.loads(raw_stdout.strip())
        except Exception as e:
            results.append({
                "testcase": i + 1,
                "status": "Output Parse Error",
                "error": str(e),
                "raw": raw_stdout.strip(),
                "passed": False,
            })
            break

        is_correct = (actual == tc["expected_output"])
        if is_correct:
            passed += 1

        results.append({
            "testcase": i + 1,
            "status": "Accepted" if is_correct else "Wrong Answer",
            "input": tc["input"],
            "expected": tc["expected_output"],
            "actual": actual,
            "passed": is_correct,
            "time": data.get("time"),
            "memory": data.get("memory"),
        })

        if not is_correct:
            break

    total = len(normalized_tests)
    verdict = "All Passed" if passed == total else (results[-1]["status"] if results else "No Tests")

    return {
        "summary": {
            "passed": passed,
            "total": total,
            "ran": len(results),
            "verdict": verdict,
        },
        "results": results,
        "detected_function": fn,
    }


# Backwards compatibility alias for existing callers
usercode_evaluation = evaluate_user_code


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
    try:
        return evaluate_user_code(req.code, req.testcases, req.language_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal evaluation error: {str(e)}")
