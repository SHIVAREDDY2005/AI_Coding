// src/types/judge.ts
// Types that EXACTLY match the FastAPI backend schemas in app/schemas/judge.py

/** A single testcase as sent in requests (matches backend TestCase schema) */
export interface JudgeTestCase {
  input: unknown; // any JSON value
  expected_output: unknown; // any JSON value
}

/** Request body for POST /api/v1/judge/evaluate */
export interface JudgeExecutionRequest {
  code: string;
  /** Language name, alias, or Judge0 integer ID. Backend accepts either `language` or `language_id`. */
  language: string | number;
  language_id?: string | number;
  testcases: JudgeTestCase[];
}

/** A single testcase result (matches backend JudgeTestCaseResult schema) */
export interface JudgeTestCaseResult {
  testcase: number;
  status: string;
  passed: boolean;
  input?: unknown;
  expected?: unknown;
  actual?: unknown;
  error?: string;
  raw?: string;
  time?: string;
  memory?: number;
}

/** Summary section of the judge response */
export interface JudgeSummary {
  passed: number;
  total: number;
  ran: number;
  verdict: string;
}

/** Full response from POST /api/v1/judge/evaluate */
export interface JudgeExecutionResponse {
  summary: JudgeSummary;
  results: JudgeTestCaseResult[];
  detected_function: string;
  language_id: number;
}
