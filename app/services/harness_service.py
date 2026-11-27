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
            return f"""package main
import ("encoding/json"; "fmt"; "os")
type Input struct {{ {fields} }}
{code}
func main() {{
    var inp Input
    json.NewDecoder(os.Stdin).Decode(&inp)
    {decls}
    result := {fn}({', '.join(keys)})
    out, _ := json.Marshal(result)
    fmt.Println(string(out))
}}"""
        go_t = self.go_type(infer_type(sample))
        return f"""package main
import ("encoding/json"; "fmt"; "os")
{code}
func main() {{
    var data {go_t}
    json.NewDecoder(os.Stdin).Decode(&data)
    result := {fn}(data)
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
            read_block = f"""JsonObject obj = gson.fromJson(br.readLine(), JsonObject.class);
        {parse}"""
        else:
            jtype = self.java_type(infer_type(sample))
            boxed = {"int": "Integer", "double": "Double", "boolean": "Boolean"}.get(jtype, jtype)
            read_block = f"{jtype} _input = gson.fromJson(br.readLine(), {boxed}.class);"
            call = "_input"
        return f"""import com.google.gson.*; import java.util.*; import java.io.*;
public class Main {{
    {code}
    public static void main(String[] args) throws Exception {{
        Gson gson = new Gson();
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        {read_block}
        Object result = new Main().{fn}({call});
        System.out.println(gson.toJson(result));
    }}
}}"""


class CppHarness(BaseHarness):
    def cpp_type(self, t: dict) -> str:
        if t["base"] == "list":
            return f"vector<{self.cpp_type(t['of'])}>"
        return {"int": "int", "float": "double", "string": "string", "bool": "bool"}.get(t["base"], "int")

    def build(self, code: str, keys: list[str], sample: Any, fn: str) -> str:
        if isinstance(sample, dict) and keys:
            types = {k: infer_type(sample[k]) for k in keys}
            decls = "\n    ".join(
                f'{self.cpp_type(types[k])} {k} = _json::from_val<{self.cpp_type(types[k])}>(_j.obj["{k}"]);'
                for k in keys
            )
            call = ", ".join(keys)
        else:
            ctype = self.cpp_type(infer_type(sample))
            decls = f"{ctype} _input = _json::from_val<{ctype}>(_j);"
            call = "_input"

        return f"""#include <bits/stdc++.h>
using namespace std;

namespace _json {{
struct Val {{
    enum Type {{ NUL, BOOL, NUM, STR, ARR, OBJ }} type = NUL;
    bool b = false;
    double d = 0;
    long long i = 0;
    bool is_int = false;
    string s;
    vector<Val> arr;
    map<string, Val> obj;
}};

struct Parser {{
    const string& src;
    size_t pos = 0;
    void skip() {{ while (pos < src.size() && isspace((unsigned char)src[pos])) ++pos; }}
    string parse_str() {{
        ++pos; // skip '"'
        string out;
        while (pos < src.size() && src[pos] != '"') {{
            if (src[pos] == '\\\\' && pos + 1 < src.size()) {{
                char c = src[++pos];
                if (c == 'n') out += '\\n';
                else if (c == 't') out += '\\t';
                else if (c == 'r') out += '\\r';
                else out += c;
            }} else {{
                out += src[pos];
            }}
            ++pos;
        }}
        if (pos < src.size()) ++pos;
        return out;
    }}
    Val parse() {{
        skip();
        Val v;
        if (pos >= src.size()) return v;
        char c = src[pos];
        if (c == 'n') {{ pos += 4; v.type = Val::NUL; return v; }}
        if (c == 't') {{ pos += 4; v.type = Val::BOOL; v.b = true; return v; }}
        if (c == 'f') {{ pos += 5; v.type = Val::BOOL; v.b = false; return v; }}
        if (c == '"') {{ v.type = Val::STR; v.s = parse_str(); return v; }}
        if (c == '[') {{
            v.type = Val::ARR;
            ++pos; skip();
            while (pos < src.size() && src[pos] != ']') {{
                v.arr.push_back(parse());
                skip();
                if (pos < src.size() && src[pos] == ',') ++pos;
                skip();
            }}
            if (pos < src.size()) ++pos;
            return v;
        }}
        if (c == '{{') {{
            v.type = Val::OBJ;
            ++pos; skip();
            while (pos < src.size() && src[pos] != '}}') {{
                skip();
                string key = parse_str();
                skip();
                if (pos < src.size() && src[pos] == ':') ++pos;
                v.obj[key] = parse();
                skip();
                if (pos < src.size() && src[pos] == ',') ++pos;
                skip();
            }}
            if (pos < src.size()) ++pos;
            return v;
        }}
        size_t start = pos;
        bool has_dot = false;
        if (src[pos] == '-') ++pos;
        while (pos < src.size() && (isdigit((unsigned char)src[pos]) || src[pos] == '.' || src[pos] == 'e' || src[pos] == 'E' || src[pos] == '+' || src[pos] == '-')) {{
            if (src[pos] == '.' || src[pos] == 'e' || src[pos] == 'E') has_dot = true;
            ++pos;
        }}
        string tok = src.substr(start, pos - start);
        v.type = Val::NUM;
        if (!has_dot) {{ v.is_int = true; v.i = stoll(tok); v.d = (double)v.i; }}
        else {{ v.is_int = false; v.d = stod(tok); v.i = (long long)v.d; }}
        return v;
    }}
}};

template <typename T> struct Reader;
template <> struct Reader<int> {{ static int read(const Val& v) {{ return v.is_int ? (int)v.i : (int)v.d; }} }};
template <> struct Reader<long long> {{ static long long read(const Val& v) {{ return v.is_int ? v.i : (long long)v.d; }} }};
template <> struct Reader<double> {{ static double read(const Val& v) {{ return v.is_int ? (double)v.i : v.d; }} }};
template <> struct Reader<bool> {{ static bool read(const Val& v) {{ return v.b; }} }};
template <> struct Reader<string> {{ static string read(const Val& v) {{ return v.s; }} }};
template <typename T> struct Reader<vector<T>> {{
    static vector<T> read(const Val& v) {{
        vector<T> res;
        res.reserve(v.arr.size());
        for (const auto& item : v.arr) res.push_back(Reader<T>::read(item));
        return res;
    }}
}};
template <typename T> T from_val(const Val& v) {{ return Reader<T>::read(v); }}

inline string dump(bool v) {{ return v ? "true" : "false"; }}
inline string dump(int v) {{ return to_string(v); }}
inline string dump(long long v) {{ return to_string(v); }}
inline string dump(size_t v) {{ return to_string(v); }}
inline string dump(double v) {{ ostringstream os; os << v; return os.str(); }}
inline string dump(const string& s) {{
    string out = "\\"";
    for (char c : s) {{
        if (c == '"' || c == '\\\\') {{ out += '\\\\'; out += c; }}
        else if (c == '\\n') out += "\\\\n";
        else out += c;
    }}
    return out + "\\"";
}}
inline string dump(const char* s) {{ return dump(string(s)); }}
template <typename T> string dump(const vector<T>& arr) {{
    string out = "[";
    for (size_t i = 0; i < arr.size(); ++i) {{
        if (i) out += ",";
        out += dump(arr[i]);
    }}
    return out + "]";
}}
}}

{code}

int main() {{
    string line;
    getline(cin, line);
    _json::Val _j = _json::Parser{{line}}.parse();
    {decls}
    auto result = {fn}({call});
    cout << _json::dump(result) << endl;
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
            read_block = f"""JObject obj = JObject.Parse(Console.ReadLine());
        {parse}"""
        else:
            cstype = self.cs_type(infer_type(sample))
            read_block = f"var _input = JToken.Parse(Console.ReadLine()).ToObject<{cstype}>();"
            call = "_input"
        return f"""using System; using Newtonsoft.Json; using Newtonsoft.Json.Linq;
public class Solution {{
    {code}
    static void Main() {{
        {read_block}
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
            52: r"\w[\w<>]*\s+(\w+)\s*\(",
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
