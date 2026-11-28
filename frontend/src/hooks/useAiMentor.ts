// src/hooks/useAiMentor.ts
import { useState, useCallback, useRef } from 'react';
import { generateSuggestion } from '../services/suggestionService';
import { extractApiErrorMessage } from '../services/apiClient';
import type { AiMentorMessage, ConversationTurn, SuggestionResponse } from '../types/ai';
import type { JudgeExecutionResponse } from '../types/judge';
import type { EditableTestcase } from './useTestcases';

export interface AiHelpParams {
  problem: string;
  userCode: string;
  language?: string;
  testcases?: EditableTestcase[];
  evalResult: JudgeExecutionResponse | null;
  feedbackFocus?: string;
  displayPrompt?: string;
}

function createMsgId(): string {
  return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function serializeTestcasesForAi(
  testcases?: EditableTestcase[]
): Array<{ input: unknown; expected_output: unknown }> | undefined {
  if (!testcases || testcases.length === 0) return undefined;
  const parsed: Array<{ input: unknown; expected_output: unknown }> = [];
  for (const tc of testcases) {
    if (!tc.inputText.trim() || !tc.expectedText.trim()) continue;
    try {
      parsed.push({
        input: JSON.parse(tc.inputText),
        expected_output: JSON.parse(tc.expectedText),
      });
    } catch {
      // Skip invalid JSON cases
    }
  }
  return parsed.length > 0 ? parsed : undefined;
}

function toConversationHistory(messages: AiMentorMessage[]): ConversationTurn[] {
  return messages
    .filter((m) => !m.error)
    .map((m) => {
      if (m.role === 'user') {
        return { role: 'user' as const, content: m.text ?? '' };
      }
      const s = m.suggestion;
      const summary = s
        ? `[${s.mistake_type}] ${s.issue} | Guidance: ${s.hint}${s.optimization ? ` | Optimization: ${s.optimization}` : ''}`
        : '';
      return { role: 'assistant' as const, content: summary };
    })
    .filter((t) => t.content.trim().length > 0);
}

export const useAiMentor = () => {
  const [messages, setMessages] = useState<AiMentorMessage[]>([]);
  const [suggestion, setSuggestion] = useState<SuggestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const messagesRef = useRef<AiMentorMessage[]>([]);

  const requestHelp = useCallback(
    async ({
      problem,
      userCode,
      language,
      testcases,
      evalResult,
      feedbackFocus,
      displayPrompt,
    }: AiHelpParams) => {
      if (!problem.trim() || problem.trim().length < 3) {
        setError('A problem statement is required for AI Help.');
        return;
      }
      if (!userCode.trim()) {
        setError('Write some code in the editor first before requesting AI Help.');
        return;
      }
      if (inFlightRef.current) return;

      const userLabel =
        displayPrompt?.trim() ||
        feedbackFocus?.trim() ||
        'Review my current code & test cases';
      const userMsg: AiMentorMessage = {
        id: createMsgId(),
        role: 'user',
        text: userLabel,
      };
      const priorHistory = toConversationHistory(messagesRef.current);
      const nextWithUser = [...messagesRef.current, userMsg];
      messagesRef.current = nextWithUser;
      setMessages(nextWithUser);

      inFlightRef.current = true;
      setLoading(true);
      setError(null);

      try {
        const payloadEval: Record<string, unknown> = evalResult
          ? {
              summary: evalResult.summary,
              results: evalResult.results,
              detected_function: evalResult.detected_function,
            }
          : { status: 'Not yet executed on current code; analyze code directly against the workspace test cases.' };

        const res = await generateSuggestion({
          problem: problem.trim(),
          user_code: userCode,
          language,
          testcases: serializeTestcasesForAi(testcases),
          eval_result: payloadEval,
          feedback_focus: feedbackFocus?.trim() || undefined,
          conversation_history: priorHistory.length > 0 ? priorHistory : undefined,
        });
        setSuggestion(res);
        const assistantMsg: AiMentorMessage = {
          id: createMsgId(),
          role: 'assistant',
          suggestion: res,
        };
        const updated = [...messagesRef.current, assistantMsg];
        messagesRef.current = updated;
        setMessages(updated);
      } catch (err: unknown) {
        const msg = extractApiErrorMessage(err, 'Failed to get AI mentoring feedback');
        setError(msg);
        const errMsg: AiMentorMessage = {
          id: createMsgId(),
          role: 'assistant',
          error: msg,
        };
        const updated = [...messagesRef.current, errMsg];
        messagesRef.current = updated;
        setMessages(updated);
      } finally {
        inFlightRef.current = false;
        setLoading(false);
      }
    },
    []
  );

  const clearSuggestion = useCallback(() => {
    messagesRef.current = [];
    setMessages([]);
    setSuggestion(null);
    setError(null);
  }, []);

  return { messages, suggestion, loading, error, requestHelp, clearSuggestion };
};
