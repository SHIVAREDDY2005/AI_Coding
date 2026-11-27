// src/types/api.ts
/**
 * API response and request types matching the FastAPI backend.
 */

export interface HealthResponse {
  status: string;
}

export interface Language {
  id: number;
  name: string;
  version: string;
}

export interface LanguagesResponse {
  languages: Language[];
}

export interface GenerateSolutionRequest {
  problemId: string;
  language: string;
}

export interface SolutionResponse {
  solution: string;
  language: string;
}

export interface GenerateTestcasesRequest {
  problemId: string;
  language: string;
}

export interface Testcase {
  input: string;
  output: string;
}

export interface TestcasesResponse {
  testcases: Testcase[];
}

export interface ValidateTestcasesRequest {
  problemId: string;
  testcases: Testcase[];
}

export interface ValidationResult {
  valid: boolean;
  errors?: string[];
}

export interface JudgeExecuteRequest {
  languageId: number;
  sourceCode: string;
  stdin?: string;
}

export interface JudgeExecuteResponse {
  stdout: string;
  stderr?: string;
  token: string;
  status: {
    id: number;
    description: string;
  };
  time?: string;
  memory?: string;
}

export interface SuggestionRequest {
  problemId: string;
  userCode: string;
}

export interface SuggestionResponse {
  suggestions: string[];
}
