import re
from typing import Any, Optional


def infer_type(val: Any) -> dict[str, Any]:
    if isinstance(val, bool):
        return {"base": "bool"}
    if isinstance(val, int):
        return {"base": "int"}
    if isinstance(val, float):
        return {"base": "float"}
    if isinstance(val, str):
        return {"base": "string"}
    if isinstance(val, list):
        inner = infer_type(val[0]) if val else {"base": "int"}
        return {"base": "list", "of": inner}
    if isinstance(val, dict):
        return {"base": "dict"}
    return {"base": "any"}


class BaseHarness:
    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        raise NotImplementedError


class PythonHarness(BaseHarness):
    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            parse = "\n".join(f"{k} = _input['{k}']" for k in keys)
            call = f"result = {fn}(**{{{', '.join(f'\"{k}\": {k}' for k in keys)}}})"
        else:
            parse = ""
            call = f"result = {fn}(_input)"
        return (
            "import json\n_input = json.loads(input())\n"
            f"{parse}\n\n{code}\n\n{call}\nprint(json.dumps(result))"
        )


class JavaScriptHarness(BaseHarness):
    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            parse = "\n".join(f"const {k} = _input['{k}'];" for k in keys)
            call = f"const result = {fn}({', '.join(keys)});"
        else:
            parse = ""
            call = f"const result = {fn}(_input);"
        return (
            "const _input = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8').trim());\n"
            f"{parse}\n\n{code}\n\n{call}\nconsole.log(JSON.stringify(result));"
        )


class TypeScriptHarness(BaseHarness):
    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            parse = "\n".join(f"const {k} = _input['{k}'];" for k in keys)
            call = f"const result = {fn}({', '.join(keys)});"
        else:
            parse = ""
            call = f"const result = {fn}(_input);"
        return (
            "import * as fs from 'fs';\n"
            "const _input: any = JSON.parse(fs.readFileSync('/dev/stdin','utf8').trim());\n"
            f"{parse}\n\n{code}\n\n{call}\nconsole.log(JSON.stringify(result));"
        )


class RubyHarness(BaseHarness):
    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            parse = "\n".join(f"{k} = _input['{k}']" for k in keys)
            call = f"result = {fn}({', '.join(keys)})"
        else:
            parse = ""
            call = f"result = {fn}(_input)"
        return (
            "require 'json'\n_input = JSON.parse(gets.chomp)\n"
            f"{parse}\n\n{code}\n\n{call}\nputs result.to_json"
        )


class GoHarness(BaseHarness):
    GO_TYPES = {"bool": "bool", "int": "int", "float": "float64", "string": "string"}

    def go_type(self, t: dict) -> str:
        if t["base"] == "list":
            return f"[]{self.go_type(t['of'])}"
        return self.GO_TYPES.get(t["base"], "interface{}")

    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            types = {k: infer_type(sample[k]) for k in keys}
            fields = "\n\t".join(
                f'{k.capitalize()} {self.go_type(types[k])} `json:"{k}"`' for k in keys
            )
            decls = "\n\t".join(f"{k} := inp.{k.capitalize()}" for k in keys)
            call = f"result := {fn}({', '.join(keys)})"
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


class JavaHarness(BaseHarness):
    def java_type(self, t: dict) -> str:
        b = t["base"]
        if b == "list":
            inner = t["of"]["base"]
            return {"int": "int[]", "float": "double[]", "string": "String[]", "list": "int[][]"}.get(
                inner, "Object[]"
            )
        return {"int": "int", "float": "double", "string": "String", "bool": "boolean"}.get(b, "Object")

    def java_parse(self, k: str, t: dict) -> str:
        b = t["base"]
        if b == "list":
            inner = t["of"]["base"]
            cls = {"int": "int[]", "float": "double[]", "string": "String[]", "list": "int[][]"}.get(
                inner, "Object[]"
            )
            return f'{cls} {k} = gson.fromJson(obj.get("{k}"), {cls}.class);'
        if b == "int":
            return f'int {k} = obj.get("{k}").getAsInt();'
        if b == "float":
            return f'double {k} = obj.get("{k}").getAsDouble();'
        if b == "string":
            return f'String {k} = obj.get("{k}").getAsString();'
        if b == "bool":
            return f'boolean {k} = obj.get("{k}").getAsBoolean();'
        return f'Object {k} = obj.get("{k}");'

    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            types = {k: infer_type(sample[k]) for k in keys}
            parse = "\n        ".join(self.java_parse(k, types[k]) for k in keys)
            call = ", ".join(keys)
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


class CppHarness(BaseHarness):
    def cpp_type(self, t: dict) -> str:
        if t["base"] == "list":
            return f"vector<{self.cpp_type(t['of'])}>"
        return {"int": "int", "float": "double", "string": "string", "bool": "bool"}.get(t["base"], "auto")

    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
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


class CSharpHarness(BaseHarness):
    def cs_type(self, t: dict) -> str:
        if t["base"] == "list":
            return f"{self.cs_type(t['of'])}[]"
        return {"int": "int", "float": "double", "string": "string", "bool": "bool"}.get(t["base"], "object")

    def cs_parse(self, k: str, t: dict) -> str:
        b = t["base"]
        if b == "list":
            return f'var {k} = obj["{k}"].ToObject<{self.cs_type(t)}>();'
        if b == "int":
            return f'int {k} = obj["{k}"].Value<int>();'
        if b == "float":
            return f'double {k} = obj["{k}"].Value<double>();'
        if b == "string":
            return f'string {k} = obj["{k}"].Value<string>();'
        if b == "bool":
            return f'bool {k} = obj["{k}"].Value<bool>();'
        return f'var {k} = obj["{k}"];'

    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            types = {k: infer_type(sample[k]) for k in keys}
            parse = "\n            ".join(self.cs_parse(k, types[k]) for k in keys)
            call = ", ".join(keys)
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


class HarnessService:
    """
    Service responsible for inspecting code and assembling execution
    harnesses across multiple programming languages.
    """

    def __init__(self):
        self._registry: dict[int, BaseHarness] = {
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
        self._func_patterns: dict[int, str] = {
            71: r"def\s+(\w+)\s*\(",
            63: r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)",
            74: r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)",
            72: r"def\s+(\w+)\s*\(",
            60: r"func\s+(\w+)\s*\(",
            62: r"(?:public|private|protected)\s+\S+\s+(\w+)\s*\(",
            54: r"\w[\w<>]*\s+(\w+)\s*\(",
            53: r"\w[\w<>]*\s+(\w+)\s*\(",
            51: r"(?:public|private)\s+\S+\s+(\w+)\s*\(",
        }

    def detect_function_name(self, code: str, language_id: int) -> str:
        pattern = self._func_patterns.get(language_id, r"(\w+)\s*\(")
        match = re.search(pattern, code)
        if match:
            return next((g for g in match.groups() if g), "solution")
        return "solution"

    def is_language_supported(self, language_id: int) -> bool:
        return language_id in self._registry

    def build_harness(
        self,
        code: str,
        language_id: int,
        sample_input: Any,
        function_name: Optional[str] = None
    ) -> str:
        builder = self._registry.get(language_id)
        if not builder:
            raise ValueError(f"Language ID {language_id} is not supported by HarnessService")

        fn = function_name or self.detect_function_name(code, language_id)
        keys = list(sample_input.keys()) if isinstance(sample_input, dict) else []
        return builder.build(code, keys, sample_input, fn)
