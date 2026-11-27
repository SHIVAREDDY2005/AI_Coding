// src/types/ai.ts
// Types matching backend app/schemas/suggestion.py

export interface SuggestionRequest {
  problem: string;
  user_code: string;
  eval_result: Record<string, unknown>;
  model?: string;
}

export interface SuggestionResponse {
  mistake_type: string;
  issue: string;
  hint: string;
  model_used?: string | null;
}
