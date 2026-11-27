// src/utils/functionSignature.ts
import type { EditableTestcase } from '../hooks/useTestcases';

interface ParamInfo {
  name: string;
  sample: unknown;
}

function sanitizeIdentifier(raw: string, index: number): string {
  const cleaned = raw.replace(/[^a-zA-Z0-9_]/g, '_');
  if (!cleaned) return `arg${index + 1}`;
  return /^[0-9]/.test(cleaned) ? `_${cleaned}` : cleaned;
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
    if (Array.isArray(val[0])) {
      const inner = inferJavaType(val[0]);
      return `${inner}[]`;
    }
    if (typeof val[0] === 'boolean') return 'boolean[]';
    if (typeof val[0] === 'string') return 'String[]';
    if (typeof val[0] === 'number') return Number.isInteger(val[0]) ? 'int[]' : 'double[]';
    return 'Object[]';
  }
  return 'Object';
}

function inferCsType(val: unknown): string {
  if (typeof val === 'boolean') return 'bool';
  if (typeof val === 'number') return Number.isInteger(val) ? 'int' : 'double';
  if (typeof val === 'string') return 'string';
  if (Array.isArray(val)) {
    if (val.length === 0) return 'int[]';
    return `${inferCsType(val[0])}[]`;
  }
  return 'object';
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

function isBetterSample(current: unknown, candidate: unknown): boolean {
  if (current === null || current === undefined) return candidate !== null && candidate !== undefined;
  if (Array.isArray(current) && current.length === 0 && Array.isArray(candidate) && candidate.length > 0) {
    return true;
  }
  return false;
}

function extractParamsFromTestcases(testcases: EditableTestcase[]): ParamInfo[] {
  const parsedInputs: unknown[] = [];
  for (const tc of testcases) {
    if (!tc.inputText.trim()) continue;
    try {
      parsedInputs.push(JSON.parse(tc.inputText));
    } catch {
      continue;
    }
  }

  if (parsedInputs.length === 0) {
    return [{ name: 'data', sample: null }];
  }

  const first = parsedInputs[0];
  if (first && typeof first === 'object' && !Array.isArray(first)) {
    const keys = Object.keys(first as Record<string, unknown>);
    if (keys.length > 0) {
      return keys.map((rawKey, idx) => {
        let sample = (first as Record<string, unknown>)[rawKey];
        for (let i = 1; i < parsedInputs.length; i++) {
          const item = parsedInputs[i];
          if (item && typeof item === 'object' && !Array.isArray(item)) {
            const candidate = (item as Record<string, unknown>)[rawKey];
            if (isBetterSample(sample, candidate)) {
              sample = candidate;
            }
          }
        }
        return { name: sanitizeIdentifier(rawKey, idx), sample };
      });
    }
  }

  let sample = first;
  for (let i = 1; i < parsedInputs.length; i++) {
    if (isBetterSample(sample, parsedInputs[i])) {
      sample = parsedInputs[i];
    }
  }
  return [{ name: 'data', sample }];
}

function extractParamsFromProblem(problem?: string): ParamInfo[] | null {
  if (!problem || !problem.trim()) return null;
  const inputSectionMatch = problem.match(
    /(?:input\s*format|input)\s*:\s*([\s\S]*?)(?=\n\s*(?:output\s*format|output|constraints?|example|note)\s*:|$)/i
  );
  const section = inputSectionMatch ? inputSectionMatch[1] : problem;

  const found: ParamInfo[] = [];
  const seen = new Set<string>();
  const assignRegex = /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=/g;
  let match: RegExpExecArray | null;
  while ((match = assignRegex.exec(section)) !== null) {
    const rawName = match[1];
    if (!seen.has(rawName)) {
      seen.add(rawName);
      found.push({ name: sanitizeIdentifier(rawName, found.length), sample: null });
    }
  }
  return found.length > 0 ? found : null;
}

/**
 * Builds an empty function-signature stub matching backend HarnessService expectations
 * for the selected language and real testcase input structure.
 */
export function buildFunctionTemplate(
  languageId: number,
  testcases: EditableTestcase[],
  problem?: string
): string {
  const hasParsedTestcase = testcases.some((tc) => {
    if (!tc.inputText.trim()) return false;
    try {
      JSON.parse(tc.inputText);
      return true;
    } catch {
      return false;
    }
  });
  const params = hasParsedTestcase
    ? extractParamsFromTestcases(testcases)
    : (extractParamsFromProblem(problem) ?? [{ name: 'data', sample: null }]);
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
      const inferred = params.map((p) => ({ name: p.name, type: inferCppType(p.sample) }));
      if (inferred.some((p) => p.type === 'auto')) {
        const tmplDecls = inferred
          .map((p, idx) => (p.type === 'auto' ? `typename T${idx}` : null))
          .filter(Boolean)
          .join(', ');
        const tmplParams = inferred
          .map((p, idx) => `${p.type === 'auto' ? `T${idx}` : p.type} ${p.name}`)
          .join(', ');
        return `template <${tmplDecls}>\nauto solve(${tmplParams}) {\n    // Return your answer\n}\n`;
      }
      const cppParams = inferred.map((p) => `${p.type} ${p.name}`).join(', ');
      return `auto solve(${cppParams}) {\n    // Return your answer\n}\n`;
    }

    case 51: { // C#
      const csParams = params.map((p) => `${inferCsType(p.sample)} ${p.name}`).join(', ');
      return `public object Solve(${csParams}) {\n    // Return your answer\n    return null;\n}\n`;
    }

    default:
      return `def solve(${names}):\n    pass\n`;
  }
}
