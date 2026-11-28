// src/types/ai.ts
// Types matching backend app/schemas/suggestion.py

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface SuggestionRequest {
  problem: string;
  user_code: string;
  eval_result: Record<string, unknown>;
  language?: string;
  testcases?: Array<{ input: unknown; expected_output: unknown }>;
  feedback_focus?: string;
  conversation_history?: ConversationTurn[];
  model?: string;
}

export interface SuggestionResponse {
  mistake_type: string;
  issue: string;
  hint: string;
  complexity?: string | null;
  optimization?: string | null;
  model_used?: string | null;
}

export interface AiMentorMessage {
  id: string;
  role: 'user' | 'assistant';
  text?: string;
  suggestion?: SuggestionResponse;
  error?: string;
}
