// src/utils/functionSignature.ts
import type { EditableTestcase } from '../hooks/useTestcases';

interface ParamInfo {
  name: string;
  sample: unknown;
}

function inferCppType(val: unknown): string {
  if (typeof val === 'boolean') return 'bool';
  if (typeof val === 'number') return Number.isInteger(val) ? 'int' : 'double';
  if (typeof val === 'string') return 'string';
  if (Array.isArray(val)) {
    const inner = val.length > 0 ? inferCppType(val[0]) : 'int';
    return `vector<${inner}>`;
  }
  return 'auto';
}

function inferJavaType(val: unknown): string {
  if (typeof val === 'boolean') return 'boolean';
  if (typeof val === 'number') return Number.isInteger(val) ? 'int' : 'double';
  if (typeof val === 'string') return 'String';
  if (Array.isArray(val)) {
    if (val.length === 0) return 'int[]';
    if (Array.isArray(val[0])) return 'int[][]';
    if (typeof val[0] === 'string') return 'String[]';
    if (typeof val[0] === 'number') return Number.isInteger(val[0]) ? 'int[]' : 'double[]';
    return 'Object[]';
  }
  return 'Object';
}

function inferGoType(val: unknown): string {
  if (typeof val === 'boolean') return 'bool';
  if (typeof val === 'number') return Number.isInteger(val) ? 'int' : 'float64';
  if (typeof val === 'string') return 'string';
  if (Array.isArray(val)) {
    const inner = val.length > 0 ? inferGoType(val[0]) : 'int';
    return `[]${inner}`;
  }
  return 'interface{}';
}

function inferTsType(val: unknown): string {
  if (typeof val === 'boolean') return 'boolean';
  if (typeof val === 'number') return 'number';
  if (typeof val === 'string') return 'string';
  if (Array.isArray(val)) {
    const inner = val.length > 0 ? inferTsType(val[0]) : 'number';
    return `${inner}[]`;
  }
  return 'unknown';
}

function extractParamsFromTestcases(testcases: EditableTestcase[]): ParamInfo[] {
  for (const tc of testcases) {
    if (!tc.inputText.trim()) continue;
    try {
      const parsed = JSON.parse(tc.inputText);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        const entries = Object.entries(parsed as Record<string, unknown>);
        if (entries.length > 0) {
          return entries.map(([name, sample]) => ({ name, sample }));
        }
      }
      return [{ name: 'data', sample: parsed }];
    } catch {
      continue;
    }
  }
  return [{ name: 'data', sample: null }];
}

/**
 * Builds an empty function-signature stub matching backend HarnessService expectations
 * for the selected language and real testcase input structure.
 */
export function buildFunctionTemplate(languageId: number, testcases: EditableTestcase[]): string {
  const params = extractParamsFromTestcases(testcases);
  const names = params.map((p) => p.name).join(', ');

  switch (languageId) {
    case 71: // Python 3
      return `def solve(${names}):\n    # Return your answer (do not use input() or print())\n    pass\n`;

    case 63: // JavaScript (Node.js)
      return `function solve(${names}) {\n  // Return your answer\n}\n`;

    case 74: { // TypeScript
      const tsParams = params.map((p) => `${p.name}: ${inferTsType(p.sample)}`).join(', ');
      return `function solve(${tsParams}): unknown {\n  // Return your answer\n  return null;\n}\n`;
    }

    case 72: // Ruby
      return `def solve(${names})\n  # Return your answer\nend\n`;

    case 60: { // Go
      const goParams = params.map((p) => `${p.name} ${inferGoType(p.sample)}`).join(', ');
      return `func solve(${goParams}) interface{} {\n\t// Return your answer\n\treturn nil\n}\n`;
    }

    case 62: { // Java
      const javaParams = params.map((p) => `${inferJavaType(p.sample)} ${p.name}`).join(', ');
      return `public Object solve(${javaParams}) {\n    // Return your answer\n    return null;\n}\n`;
    }

    case 54: // C++ 17
    case 53:
    case 52: {
      const cppParams = params.map((p) => `${inferCppType(p.sample)} ${p.name}`).join(', ');
      return `auto solve(${cppParams}) {\n    // Return your answer\n}\n`;
    }

    case 51: { // C#
      const csParams = params.map((p) => `${inferJavaType(p.sample).replace('String', 'string').replace('boolean', 'bool')} ${p.name}`).join(', ');
      return `public object Solve(${csParams}) {\n    // Return your answer\n    return null;\n}\n`;
    }

    default:
      return `def solve(${names}):\n    pass\n`;
  }
}
