// src/types/testcase.ts
// Types matching backend app/schemas/testcase.py

/** Single testcase as returned by the generate endpoint */
export interface GeneratedTestCase {
  input: unknown;        // any JSON value
  expected_output: unknown; // any JSON value
}

/** Request for POST /api/v1/testcases/generate */
export interface TestcaseGenerateRequest {
  problem: string; // min 5 chars
  model?: string;  // optional Groq model override
}

/** Response from POST /api/v1/testcases/generate */
export interface TestcaseGenerateResponse {
  testcases: GeneratedTestCase[];
  count: number;
  model_used: string;
}
