// src/features/execution/TestcaseConsole.tsx
import React, { useState, useEffect } from 'react';
import { Sparkles, Plus, Trash2, CheckCircle2, XCircle, AlertTriangle, Terminal, ChevronDown, ChevronUp } from 'lucide-react';
import Button from '../../components/ui/Button';
import type { EditableTestcase } from '../../hooks/useTestcases';
import type { JudgeExecutionResponse, JudgeTestCaseResult } from '../../types/judge';

type ConsoleTab = 'testcases' | 'results' | 'output';

interface TestcaseConsoleProps {
  problem: string;
  testcases: EditableTestcase[];
  generating: boolean;
  generationError: string | null;
  modelUsed: string | null;
  validationError: string | null;
  onGenerateTestcases: () => void;
  onAddTestcase: () => void;
  onUpdateTestcase: (id: string, field: 'inputText' | 'expectedText', value: string) => void;
  onRemoveTestcase: (id: string) => void;
  onClearTestcases: () => void;
  execResult: JudgeExecutionResponse | null;
  execLoading: boolean;
  execError: string | null;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  onEditProblem?: () => void;
}

function isValidJson(text: string): boolean {
  if (!text.trim()) return false;
  try {
    JSON.parse(text);
    return true;
  } catch {
    return false;
  }
}

function formatJsonValue(val: unknown): string {
  if (val === undefined || val === null) return String(val);
  if (typeof val === 'string') return JSON.stringify(val);
  try {
    return JSON.stringify(val, null, 2);
  } catch {
    return String(val);
  }
}

export const TestcaseConsole: React.FC<TestcaseConsoleProps> = ({
  problem,
  testcases,
  generating,
  generationError,
  modelUsed,
  validationError,
  onGenerateTestcases,
  onAddTestcase,
  onUpdateTestcase,
  onRemoveTestcase,
  onClearTestcases,
  execResult,
  execLoading,
  execError,
  collapsed = false,
  onToggleCollapse,
  onEditProblem,
}) => {
  const [activeTab, setActiveTab] = useState<ConsoleTab>('testcases');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  // Keep selectedCaseId valid when testcases change
  useEffect(() => {
    if (testcases.length === 0) {
      setSelectedCaseId(null);
      return;
    }
    if (!selectedCaseId || !testcases.some((tc) => tc.id === selectedCaseId)) {
      setSelectedCaseId(testcases[0].id);
    }
  }, [testcases, selectedCaseId]);

  // Switch automatically to Execution Results when an execution finishes or fails
  useEffect(() => {
    if (execResult || execError) {
      setActiveTab('results');
    }
  }, [execResult, execError]);

  const activeCase = testcases.find((tc) => tc.id === selectedCaseId) ?? testcases[0] ?? null;

  return (
    <div className="flex flex-col bg-surface border border-border rounded-xl overflow-hidden">
      {/* Console Tab Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-surface-dark border-b border-border">
        <div role="tablist" aria-label="Testcase and execution console" className="flex items-center gap-1">
          <button
            type="button"
            role="tab"
            id="tab-testcases"
            aria-selected={activeTab === 'testcases'}
            onClick={() => setActiveTab('testcases')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              activeTab === 'testcases'
                ? 'text-white bg-surface-elevated'
                : 'text-text-muted hover:text-text'
            }`}
          >
            Test Cases ({testcases.length})
          </button>
          <button
            type="button"
            role="tab"
            id="tab-results"
            aria-selected={activeTab === 'results'}
            onClick={() => setActiveTab('results')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors inline-flex items-center gap-1.5 ${
              activeTab === 'results'
                ? 'text-white bg-surface-elevated'
                : 'text-text-muted hover:text-text'
            }`}
          >
            Execution Results
            {execResult && (
              <span
                className={`px-1.5 py-0.5 text-[11px] rounded font-semibold ${
                  execResult.summary.verdict === 'All Passed'
                    ? 'bg-accent/20 text-accent'
                    : 'bg-danger/20 text-danger'
                }`}
              >
                {execResult.summary.passed}/{execResult.summary.total}
              </span>
            )}
          </button>
          <button
            type="button"
            role="tab"
            id="tab-output"
            aria-selected={activeTab === 'output'}
            onClick={() => setActiveTab('output')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              activeTab === 'output'
                ? 'text-white bg-surface-elevated'
                : 'text-text-muted hover:text-text'
            }`}
          >
            Output
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'testcases' && (
            <>
              <Button
                type="button"
                variant="primary"
                size="sm"
                loading={generating}
                disabled={generating || !problem.trim()}
                onClick={onGenerateTestcases}
                title={!problem.trim() ? 'A problem statement is required' : 'Generate test cases via AI backend'}
              >
                <Sparkles className="w-3.5 h-3.5" />
                {generating ? 'Generating...' : 'Generate Test Cases'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  onAddTestcase();
                }}
              >
                <Plus className="w-3.5 h-3.5" />
                Add Testcase
              </Button>
              {testcases.length > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onClearTestcases}
                  title="Remove all testcases"
                >
                  Clear
                </Button>
              )}
            </>
          )}
          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface-elevated"
              aria-label={collapsed ? 'Expand console' : 'Collapse console'}
              title={collapsed ? 'Expand console' : 'Collapse console'}
            >
              {collapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Console Body */}
      {!collapsed && (
        <div className="p-4 max-h-[420px] overflow-y-auto custom-scrollbar">
          {/* TEST CASES PANEL */}
          <div role="tabpanel" aria-labelledby="tab-testcases" hidden={activeTab !== 'testcases'}>
            {(generationError || validationError) && (
              <div className="mb-3 p-3 rounded-lg border border-danger/40 bg-danger/10 text-danger text-sm space-y-2">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <p className="font-medium">{generationError ?? validationError}</p>
                    {generationError &&
                      generationError.toLowerCase().includes('invalid problem') && (
                        <p className="text-xs text-text-muted">
                          The AI needs a clear problem specification to avoid guessing. Make sure your problem includes:{' '}
                          <strong className="text-text">Input format</strong>,{' '}
                          <strong className="text-text">Expected output</strong>, and{' '}
                          <strong className="text-text">Constraints</strong>.
                        </p>
                      )}
                  </div>
                </div>
                {generationError &&
                  generationError.toLowerCase().includes('invalid problem') &&
                  onEditProblem && (
                    <Button type="button" variant="secondary" size="sm" onClick={onEditProblem}>
                      Edit Problem Statement
                    </Button>
                  )}
              </div>
            )}

            {modelUsed && testcases.length > 0 && !generationError && (
              <div className="mb-3 flex items-center justify-between text-xs text-text-muted">
                <span>
                  Generated {testcases.length} test case{testcases.length === 1 ? '' : 's'} using{' '}
                  <code className="px-1.5 py-0.5 rounded bg-surface-elevated text-primary-light">{modelUsed}</code>
                </span>
                <span>You can edit or add cases before running.</span>
              </div>
            )}

            {generating && (
              <div className="mb-3 p-3 rounded-lg border border-primary/30 bg-primary/10 text-primary-light text-sm">
                Generating test cases from your problem statement via backend AI...
              </div>
            )}

            {testcases.length === 0 ? (
              <div className="py-8 text-center border border-dashed border-border rounded-lg bg-surface-dark/50">
                <p className="text-sm text-text-muted mb-3">
                  No testcases added yet. Add your input and expected output to evaluate your code.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <Button
                    type="button"
                    variant="primary"
                    size="sm"
                    loading={generating}
                    disabled={generating || !problem.trim()}
                    onClick={onGenerateTestcases}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Generate Test Cases
                  </Button>
                  <Button type="button" variant="secondary" size="sm" onClick={onAddTestcase}>
                    <Plus className="w-3.5 h-3.5" />
                    Add Manual Testcase
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Case Pills */}
                <div className="flex flex-wrap items-center gap-2">
                  {testcases.map((tc, idx) => {
                    const isSelected = activeCase?.id === tc.id;
                    const valid = isValidJson(tc.inputText) && isValidJson(tc.expectedText);
                    return (
                      <div
                        key={tc.id}
                        className={`inline-flex items-center rounded-lg border text-xs font-medium transition-colors ${
                          isSelected
                            ? 'bg-primary/20 border-primary text-white'
                            : 'bg-surface-dark border-border text-text-muted hover:text-text'
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => setSelectedCaseId(tc.id)}
                          className="px-3 py-1.5 inline-flex items-center gap-1.5"
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              valid ? 'bg-accent' : 'bg-warning'
                            }`}
                            title={valid ? 'Valid JSON' : 'Incomplete or invalid JSON'}
                          />
                          Case {idx + 1}
                        </button>
                        <button
                          type="button"
                          onClick={() => onRemoveTestcase(tc.id)}
                          aria-label={`Remove Case ${idx + 1}`}
                          className="pr-2 py-1.5 text-text-muted hover:text-danger"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    );
                  })}
                </div>

                {/* Selected Case Editor */}
                {activeCase && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                          Input (JSON)
                        </label>
                        {activeCase.inputText.trim() && (
                          <span
                            className={`text-xs ${
                              isValidJson(activeCase.inputText) ? 'text-accent' : 'text-danger'
                            }`}
                          >
                            {isValidJson(activeCase.inputText) ? 'Valid JSON' : 'Invalid JSON'}
                          </span>
                        )}
                      </div>
                      <textarea
                        value={activeCase.inputText}
                        onChange={(e) => onUpdateTestcase(activeCase.id, 'inputText', e.target.value)}
                        rows={4}
                        placeholder='e.g. {"nums": [2, 7, 11, 15], "target": 9} or [1, 2, 3]'
                        className="w-full p-3 rounded-lg border border-border bg-surface-dark text-text font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                          Expected Output (JSON)
                        </label>
                        {activeCase.expectedText.trim() && (
                          <span
                            className={`text-xs ${
                              isValidJson(activeCase.expectedText) ? 'text-accent' : 'text-danger'
                            }`}
                          >
                            {isValidJson(activeCase.expectedText) ? 'Valid JSON' : 'Invalid JSON'}
                          </span>
                        )}
                      </div>
                      <textarea
                        value={activeCase.expectedText}
                        onChange={(e) => onUpdateTestcase(activeCase.id, 'expectedText', e.target.value)}
                        rows={4}
                        placeholder='e.g. [0, 1] or 42 or true'
                        className="w-full p-3 rounded-lg border border-border bg-surface-dark text-text font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* EXECUTION RESULTS PANEL */}
          <div role="tabpanel" aria-labelledby="tab-results" hidden={activeTab !== 'results'}>
            {execLoading && (
              <div className="py-8 text-center text-sm text-primary-light">
                Evaluating your code in Judge0 sandbox...
              </div>
            )}

            {!execLoading && execError && (
              <div className="p-4 rounded-lg border border-danger/40 bg-danger/10 text-danger text-sm flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold mb-1">Execution Error</p>
                  <p>{execError}</p>
                </div>
              </div>
            )}

            {!execLoading && !execError && !execResult && (
              <div className="py-8 text-center text-sm text-text-muted">
                No execution results yet. Add or generate test cases and click <strong>Run Tests</strong>.
              </div>
            )}

            {!execLoading && execResult && (
              <div className="space-y-4">
                {/* Summary Banner */}
                <div
                  className={`p-3.5 rounded-lg border flex flex-wrap items-center justify-between gap-3 ${
                    execResult.summary.verdict === 'All Passed'
                      ? 'bg-accent/10 border-accent/40'
                      : 'bg-danger/10 border-danger/40'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    {execResult.summary.verdict === 'All Passed' ? (
                      <CheckCircle2 className="w-5 h-5 text-accent" />
                    ) : (
                      <XCircle className="w-5 h-5 text-danger" />
                    )}
                    <div>
                      <p
                        className={`text-base font-bold ${
                          execResult.summary.verdict === 'All Passed' ? 'text-accent' : 'text-danger'
                        }`}
                      >
                        {execResult.summary.verdict}
                      </p>
                      <p className="text-xs text-text-muted">
                        Passed {execResult.summary.passed} of {execResult.summary.total} test cases (Executed:{' '}
                        {execResult.summary.ran})
                      </p>
                    </div>
                  </div>
                  <div className="text-xs text-text-muted font-mono">
                    Function: <span className="text-text">{execResult.detected_function || 'Not available'}</span>
                  </div>
                </div>

                {/* Per-Testcase Cards */}
                <div className="space-y-3">
                  {execResult.results.map((r: JudgeTestCaseResult) => (
                    <div
                      key={r.testcase}
                      className="border border-border rounded-lg p-3.5 bg-surface-dark space-y-2.5"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-text">Test Case #{r.testcase}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              r.passed
                                ? 'bg-accent/20 text-accent'
                                : 'bg-danger/20 text-danger'
                            }`}
                          >
                            {r.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-text-muted">
                          <span>Time: {r.time ? `${r.time}s` : 'Not available'}</span>
                          <span>
                            Memory: {r.memory !== undefined && r.memory !== null ? `${r.memory} KB` : 'Not available'}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 text-xs">
                        {r.input !== undefined && (
                          <div className="bg-background rounded-md p-2.5 border border-border">
                            <p className="text-text-muted font-semibold mb-1">Input</p>
                            <pre className="font-mono text-text whitespace-pre-wrap break-all">
                              {formatJsonValue(r.input)}
                            </pre>
                          </div>
                        )}
                        {r.expected !== undefined && (
                          <div className="bg-background rounded-md p-2.5 border border-border">
                            <p className="text-text-muted font-semibold mb-1">Expected</p>
                            <pre className="font-mono text-accent whitespace-pre-wrap break-all">
                              {formatJsonValue(r.expected)}
                            </pre>
                          </div>
                        )}
                        {r.actual !== undefined && (
                          <div className="bg-background rounded-md p-2.5 border border-border">
                            <p className="text-text-muted font-semibold mb-1">Actual</p>
                            <pre
                              className={`font-mono whitespace-pre-wrap break-all ${
                                r.passed ? 'text-accent' : 'text-danger'
                              }`}
                            >
                              {formatJsonValue(r.actual)}
                            </pre>
                          </div>
                        )}
                      </div>

                      {r.error && (
                        <div className="bg-danger/10 border border-danger/30 rounded-md p-2.5 text-xs text-danger font-mono whitespace-pre-wrap">
                          {r.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RAW OUTPUT PANEL */}
          <div role="tabpanel" aria-labelledby="tab-output" hidden={activeTab !== 'output'}>
            {!execResult || execResult.results.every((r) => !r.raw && !r.error && r.actual === undefined) ? (
              <div className="py-8 text-center text-sm text-text-muted flex flex-col items-center gap-2">
                <Terminal className="w-5 h-5" />
                <span>No raw execution output available yet. Run tests to view stdout and errors.</span>
              </div>
            ) : (
              <div className="space-y-2">
                {execResult.results.map((r) => (
                  <div key={r.testcase} className="p-3 rounded-lg bg-surface-dark border border-border text-xs font-mono">
                    <div className="text-text-muted mb-1">
                      Case #{r.testcase} — {r.status}
                    </div>
                    {r.raw && <pre className="text-text whitespace-pre-wrap">{r.raw}</pre>}
                    {r.actual !== undefined && (
                      <pre className="text-text whitespace-pre-wrap">stdout: {formatJsonValue(r.actual)}</pre>
                    )}
                    {r.error && <pre className="text-danger whitespace-pre-wrap">error: {r.error}</pre>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
