import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  RotateCcw,
  Copy,
  Check,
  Sparkles,
  Minus,
  Plus,
  Map as MapIcon,
  X,
  Pencil,
  FileCode2,
  Maximize2,
  Minimize2,
  FileText,
  Code2,
} from 'lucide-react';
import Button from '../components/ui/Button';
import LanguageSelector from '../features/editor/LanguageSelector';
import CodeEditor from '../features/editor/CodeEditor';
import { TestcaseConsole } from '../features/execution/TestcaseConsole';
import { ProblemPanel } from '../features/workspace/ProblemPanel';
import { AiMentorChat } from '../features/workspace/AiMentorChat';
import { useLanguages } from '../hooks/useLanguages';
import { useCodeDraft } from '../hooks/useCodeDraft';
import { useCodeExecution } from '../hooks/useCodeExecution';
import { useTestcases } from '../hooks/useTestcases';
import { useAiMentor } from '../hooks/useAiMentor';
import { useSplitLayout } from '../hooks/useSplitLayout';
import { buildFunctionTemplate } from '../utils/functionSignature';

type MobileView = 'problem' | 'code' | 'console';
type LeftTab = 'problem' | 'mentor';

const WorkspacePage: React.FC = () => {
  const { problemId } = useParams<{ problemId: string }>();
  const sessionId = problemId ?? 'unknown';

  const [question, setQuestion] = useState<string>('');
  const [editingProblem, setEditingProblem] = useState(false);
  const [problemDraft, setProblemDraft] = useState('');
  const [copiedProblem, setCopiedProblem] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [fontSize, setFontSize] = useState<number>(14);
  const [minimap, setMinimap] = useState<boolean>(false);
  const [consoleCollapsed, setConsoleCollapsed] = useState<boolean>(false);
  const [editorExpanded, setEditorExpanded] = useState<boolean>(false);
  const [leftTab, setLeftTab] = useState<LeftTab>('problem');
  const [mobileView, setMobileView] = useState<MobileView>('code');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [feedbackFocus, setFeedbackFocus] = useState<string>('auto');
  const [customFeedbackPrompt, setCustomFeedbackPrompt] = useState<string>('');
  const lastRunSignatureRef = useRef<string | null>(null);
  const {
    splitContainerRef,
    rightColumnRef,
    leftWidthPct,
    editorHeightPct,
    startDrag,
    resetLeftWidth,
    resetEditorHeight,
  } = useSplitLayout();

  // Load problem statement saved from HomePage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(`workspace:${sessionId}`);
      setQuestion(stored ?? '');
    } catch {
      setQuestion('');
    }
  }, [sessionId]);

  // Languages from FastAPI GET /api/v1/languages
  const { languages, loading: langsLoading, error: langsError, refetch: refetchLanguages } = useLanguages();

  const [selectedLangId, setSelectedLangId] = useState<number | null>(() => {
    try {
      const savedLang = localStorage.getItem(`workspace-lang:${sessionId}`);
      return savedLang ? Number(savedLang) : null;
    } catch {
      return null;
    }
  });

  // Auto-select first backend language (preferring Python 3 / ID 71) if none selected or invalid
  useEffect(() => {
    if (languages.length === 0) return;
    const exists = selectedLangId !== null && languages.some((l) => l.id === selectedLangId);
    if (!exists) {
      const python = languages.find((l) => l.id === 71 || l.monaco_id === 'python');
      const fallbackId = python ? python.id : languages[0].id;
      setSelectedLangId(fallbackId);
    }
  }, [languages, selectedLangId]);

  const handleLanguageChange = (id: number) => {
    setSelectedLangId(id);
    try {
      localStorage.setItem(`workspace-lang:${sessionId}`, String(id));
    } catch {
      // Ignore storage errors
    }
  };

  // Per-session, per-language draft persistence
  const { code, setCode, resetDraft } = useCodeDraft(sessionId, selectedLangId);

  // Testcase management + AI generation
  const {
    testcases,
    generating,
    generationError,
    modelUsed,
    addTestcase,
    updateTestcase,
    removeTestcase,
    clearTestcases,
    generateFromProblem,
    validateAndBuildPayload,
  } = useTestcases(sessionId);

  // Code execution via POST /api/v1/judge/evaluate
  const { run, loading: execLoading, error: execError, result } = useCodeExecution();

  // Explicit AI Help via POST /api/v1/suggestions/generate
  const {
    messages: aiMessages,
    suggestion,
    loading: aiLoading,
    error: aiError,
    requestHelp,
    clearSuggestion,
  } = useAiMentor();

  const selectedLanguage = languages.find((l) => l.id === selectedLangId) ?? null;
  const autoTemplateRef = useRef<{ key: string; value: string } | null>(null);
  const currentTemplate = selectedLanguage
    ? buildFunctionTemplate(selectedLanguage.id, testcases, question)
    : '';
  const fallbackTemplate = selectedLanguage
    ? buildFunctionTemplate(selectedLanguage.id, [], question)
    : '';
  const bareTemplate = selectedLanguage
    ? buildFunctionTemplate(selectedLanguage.id, [])
    : '';

  // Auto-populate starter function template when editor is empty or unedited template needs updated params
  useEffect(() => {
    if (!selectedLanguage || !currentTemplate) return;
    const draftKey = `${sessionId}:${selectedLanguage.id}`;
    const isEmpty = !code.trim();
    const isUneditedAutoTemplate =
      (autoTemplateRef.current?.key === draftKey && code === autoTemplateRef.current.value) ||
      code === fallbackTemplate ||
      code === bareTemplate;

    if ((isEmpty || isUneditedAutoTemplate) && currentTemplate !== code) {
      autoTemplateRef.current = { key: draftKey, value: currentTemplate };
      setCode(currentTemplate);
    }
  }, [sessionId, selectedLanguage, currentTemplate, fallbackTemplate, bareTemplate, code, setCode]);

  const handleResetToTemplate = () => {
    resetDraft();
    if (selectedLanguage && currentTemplate) {
      const draftKey = `${sessionId}:${selectedLanguage.id}`;
      autoTemplateRef.current = { key: draftKey, value: currentTemplate };
      setCode(currentTemplate);
    }
  };

  const handleRunTests = async () => {
    if (!code.trim()) {
      setValidationError('Editor code cannot be empty.');
      setConsoleCollapsed(false);
      setMobileView('console');
      return;
    }
    if (!selectedLanguage) {
      setValidationError('Please select a supported language.');
      setConsoleCollapsed(false);
      setMobileView('console');
      return;
    }
    const check = validateAndBuildPayload();
    if (!check.valid || !check.payload) {
      setValidationError(check.error ?? 'Invalid test cases.');
      setConsoleCollapsed(false);
      setMobileView('console');
      return;
    }

    setValidationError(null);
    setConsoleCollapsed(false);
    setMobileView('console');
    lastRunSignatureRef.current = JSON.stringify({
      code,
      languageId: selectedLanguage.id,
      testcases: check.payload,
    });

    await run({
      code,
      language: selectedLanguage.id,
      language_id: selectedLanguage.id,
      testcases: check.payload,
    });
  };

  const triggerAiHelp = (overrideFocus?: string, labelOverride?: string) => {
    const activeFocus = overrideFocus ?? feedbackFocus;
    const focusMap: Record<string, string> = {
      auto: '',
      optimize: 'Analyze time and space complexity of my code and explain how to optimize it.',
      debug: 'Find bugs, wrong answers, or runtime/syntax errors in my code against the test cases.',
      edge_cases: 'Check whether my code handles all constraints and edge cases in the test cases.',
    };
    const labelMap: Record<string, string> = {
      auto: 'Review my code & test cases',
      optimize: 'How can I optimize time & space complexity?',
      debug: 'Find bugs or errors in my code',
      edge_cases: 'Check edge cases & constraints',
    };
    const custom = customFeedbackPrompt.trim();
    const resolvedFocus = custom ? custom : (focusMap[activeFocus] ?? activeFocus);
    const displayPrompt = custom || labelOverride || labelMap[activeFocus] || resolvedFocus;

    const currentSignature = selectedLanguage
      ? JSON.stringify({
          code,
          languageId: selectedLanguage.id,
          testcases: testcases.map((tc) => {
            try {
              return { input: JSON.parse(tc.inputText), expected_output: JSON.parse(tc.expectedText) };
            } catch {
              return { input: tc.inputText, expected_output: tc.expectedText };
            }
          }),
        })
      : null;

    const freshEvalResult =
      result && currentSignature && lastRunSignatureRef.current === currentSignature ? result : null;

    setLeftTab('mentor');
    setMobileView('problem');
    if (custom) setCustomFeedbackPrompt('');
    void requestHelp({
      problem: question,
      userCode: code,
      language: selectedLanguage?.name,
      testcases,
      evalResult: freshEvalResult,
      feedbackFocus: resolvedFocus,
      displayPrompt,
    });
  };

  const handleCopyProblem = async () => {
    if (!question) return;
    try {
      await navigator.clipboard.writeText(question);
      setCopiedProblem(true);
      setTimeout(() => setCopiedProblem(false), 1800);
    } catch {
      // Ignore clipboard errors
    }
  };

  const handleCopyCode = async () => {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 1800);
    } catch {
      // Ignore clipboard errors
    }
  };

  const openProblemEditor = () => {
    setProblemDraft(question);
    setEditingProblem(true);
    setLeftTab('problem');
    setMobileView('problem');
  };

  const saveProblemEdit = () => {
    const trimmed = problemDraft.trim();
    if (!trimmed) return;
    setQuestion(trimmed);
    setEditingProblem(false);
    try {
      localStorage.setItem(`workspace:${sessionId}`, trimmed);
    } catch {
      // Ignore storage errors
    }
  };

  return (
    <div className="flex-1 flex flex-col max-w-[1600px] w-full mx-auto px-3 sm:px-4 py-3 gap-3">
      {/* Top Workspace Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2.5 rounded-xl border border-border bg-surface">
        <div className="flex items-center gap-3">
          <Button as={Link} to="/" variant="secondary" size="sm">
            <ArrowLeft className="w-3.5 h-3.5" />
            Home
          </Button>
          <div className="hidden sm:flex flex-col">
            <h1 className="text-sm font-semibold text-white leading-tight">Coding Workspace</h1>
            <span className="text-[11px] text-text-muted">Drafts saved locally in browser</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <LanguageSelector
            languages={languages}
            selectedId={selectedLangId}
            onChange={handleLanguageChange}
            loading={langsLoading}
            error={langsError}
            onRetry={refetchLanguages}
          />

          {/* Editor controls */}
          <div className="hidden lg:flex items-center gap-1 px-2 py-1 rounded-lg border border-border bg-surface-dark">
            <button
              type="button"
              onClick={() => setFontSize((s) => Math.max(11, s - 1))}
              className="p-1 text-text-muted hover:text-text"
              title="Decrease font size"
              aria-label="Decrease font size"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <span className="text-xs text-text-muted px-1 font-mono">{fontSize}px</span>
            <button
              type="button"
              onClick={() => setFontSize((s) => Math.min(22, s + 1))}
              className="p-1 text-text-muted hover:text-text"
              title="Increase font size"
              aria-label="Increase font size"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <span className="w-px h-4 bg-border mx-1" />
            <button
              type="button"
              onClick={() => setMinimap((m) => !m)}
              className={`p-1 rounded ${minimap ? 'text-primary-light bg-primary/15' : 'text-text-muted hover:text-text'}`}
              title="Toggle minimap"
              aria-label="Toggle minimap"
            >
              <MapIcon className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={handleCopyCode}
              disabled={!code}
              className="p-1 text-text-muted hover:text-text disabled:opacity-40"
              title="Copy code"
              aria-label="Copy code"
            >
              {copiedCode ? <Check className="w-3.5 h-3.5 text-accent" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>

          <Button
            type="button"
            variant="secondary"
            size="sm"
            loading={aiLoading}
            disabled={aiLoading || !question.trim() || !code.trim()}
            onClick={() => triggerAiHelp()}
            title={!code.trim() ? 'Write some code first to get AI mentoring' : 'Get AI mentoring feedback on your code & test cases'}
          >
            <Sparkles className="w-3.5 h-3.5 text-primary-light" />
            AI Help
          </Button>

          <Button
            type="button"
            variant="danger"
            size="sm"
            onClick={handleResetToTemplate}
            disabled={!code || code === currentTemplate}
            title="Reset current language draft to starter template"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </Button>

          <Button
            type="button"
            variant="accent"
            size="sm"
            loading={execLoading}
            disabled={execLoading}
            onClick={() => void handleRunTests()}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {execLoading ? 'Running...' : 'Run Tests'}
          </Button>
        </div>
      </div>

      {/* Mobile View Switcher */}
      <div className="flex lg:hidden border border-border rounded-lg bg-surface p-1 gap-1">
        {(['problem', 'code', 'console'] as MobileView[]).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setMobileView(tab)}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md capitalize transition-colors ${
              mobileView === tab ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Main Split Workspace (Resizable LeetCode-style panes) */}
      <div
        ref={splitContainerRef}
        style={{ '--left-width': `${leftWidthPct}%` } as React.CSSProperties}
        className="flex flex-col lg:flex-row gap-3 lg:gap-0 lg:h-[calc(100vh-148px)] lg:min-h-[620px]"
      >
        {/* Left Panel: Tabbed Problem Statement & AI Mentor */}
        {!editorExpanded && (
          <section
            className={`w-full lg:w-[var(--left-width)] lg:shrink-0 flex flex-col min-h-[360px] lg:min-h-0 lg:h-full ${
              mobileView === 'problem' ? 'flex' : 'hidden lg:flex'
            }`}
          >
            <div className="flex-1 flex flex-col border border-border rounded-xl bg-surface overflow-hidden min-h-0">
              <div className="flex items-center justify-between px-3 py-2 bg-surface-dark border-b border-border gap-2">
                <div role="tablist" aria-label="Problem and AI Mentor" className="flex items-center gap-1">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={leftTab === 'problem'}
                    onClick={() => setLeftTab('problem')}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors inline-flex items-center gap-1.5 ${
                      leftTab === 'problem'
                        ? 'bg-surface-elevated text-white'
                        : 'text-text-muted hover:text-text'
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5 text-primary-light" />
                    Description
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={leftTab === 'mentor'}
                    onClick={() => setLeftTab('mentor')}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors inline-flex items-center gap-1.5 ${
                      leftTab === 'mentor'
                        ? 'bg-surface-elevated text-white'
                        : 'text-text-muted hover:text-text'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5 text-primary-light" />
                    AI Mentor
                    {(suggestion || aiError) && (
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${aiError ? 'bg-danger' : 'bg-accent'}`}
                      />
                    )}
                  </button>
                </div>

                {leftTab === 'problem' ? (
                  <div className="flex items-center gap-3">
                    {!editingProblem && (
                      <button
                        type="button"
                        onClick={openProblemEditor}
                        className="inline-flex items-center gap-1 text-xs text-text-muted hover:text-text"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                        Edit
                      </button>
                    )}
                    {question && !editingProblem && (
                      <button
                        type="button"
                        onClick={handleCopyProblem}
                        className="inline-flex items-center gap-1 text-xs text-text-muted hover:text-text"
                      >
                        {copiedProblem ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-accent" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            Copy
                          </>
                        )}
                      </button>
                    )}
                  </div>
                ) : (suggestion || aiError) ? (
                  <button
                    type="button"
                    onClick={clearSuggestion}
                    className="inline-flex items-center gap-1 text-xs text-text-muted hover:text-text"
                  >
                    <X className="w-3.5 h-3.5" />
                    Clear
                  </button>
                ) : null}
              </div>

              <div className="flex-1 min-h-0 flex flex-col">
                {leftTab === 'problem' ? (
                  <ProblemPanel
                    question={question}
                    editingProblem={editingProblem}
                    problemDraft={problemDraft}
                    onChangeDraft={setProblemDraft}
                    onCancelEdit={() => setEditingProblem(false)}
                    onSaveEdit={saveProblemEdit}
                  />
                ) : (
                  <AiMentorChat
                    messages={aiMessages}
                    loading={aiLoading}
                    languageName={selectedLanguage?.name}
                    testcaseCount={testcases.length}
                    hasCode={Boolean(code.trim())}
                    feedbackFocus={feedbackFocus}
                    customPrompt={customFeedbackPrompt}
                    onChangeCustomPrompt={setCustomFeedbackPrompt}
                    onSelectMode={(modeId) => {
                      setFeedbackFocus(modeId);
                      setCustomFeedbackPrompt('');
                      triggerAiHelp(modeId);
                    }}
                    onSend={() => triggerAiHelp()}
                  />
                )}
              </div>
            </div>
          </section>
        )}

        {/* Horizontal Resize Handle */}
        {!editorExpanded && (
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize problem and editor panels"
            onPointerDown={startDrag('horizontal')}
            onDoubleClick={resetLeftWidth}
            title="Drag to resize width (double-click to reset)"
            className="hidden lg:flex w-2.5 shrink-0 cursor-col-resize items-center justify-center group select-none"
          >
            <div className="w-1 h-12 rounded-full bg-border group-hover:bg-primary transition-colors" />
          </div>
        )}

        {/* Right Panel: Monaco Code Editor + Testcase Console */}
        <div
          ref={rightColumnRef}
          style={{ '--editor-height': `${editorHeightPct}%` } as React.CSSProperties}
          className="flex-1 min-w-0 flex flex-col gap-3 lg:gap-0 min-h-0 lg:h-full"
        >
          {/* Monaco Editor */}
          <section
            className={`flex flex-col border border-border rounded-xl bg-surface overflow-hidden min-h-[300px] lg:min-h-[180px] ${
              editorExpanded || consoleCollapsed ? 'flex-1' : 'flex-1 lg:flex-none lg:h-[var(--editor-height)]'
            } ${
              mobileView === 'code' ? 'flex' : 'hidden lg:flex'
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-surface-dark border-b border-border text-xs text-text-muted">
              <span className="inline-flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5 text-accent" />
                <span className="font-semibold text-white">Code</span>
                {selectedLanguage ? (
                  <span className="text-text-muted">
                    · {selectedLanguage.name} ({selectedLanguage.extension ?? ''})
                  </span>
                ) : null}
              </span>
              <div className="flex items-center gap-3">
                <span className="hidden sm:inline">
                  Write a function &amp; return the result (no <code className="text-text">input()</code>)
                </span>
                {selectedLanguage && !code.trim() && (
                  <button
                    type="button"
                    onClick={() => setCode(buildFunctionTemplate(selectedLanguage.id, testcases, question))}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-primary/15 border border-primary/30 text-primary-light hover:bg-primary/25 transition-colors"
                    title="Insert empty function signature matching your selected language and test cases"
                  >
                    <FileCode2 className="w-3.5 h-3.5" />
                    Insert Function Template
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setEditorExpanded((v) => !v)}
                  className="hidden lg:inline-flex items-center gap-1 p-1 rounded hover:bg-surface-elevated text-text-muted hover:text-text"
                  title={editorExpanded ? 'Restore split view' : 'Maximize editor'}
                  aria-label={editorExpanded ? 'Restore split view' : 'Maximize editor'}
                >
                  {editorExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
            <div className="flex-1 min-h-[300px] relative">
              <CodeEditor
                language={selectedLanguage}
                code={code}
                onChange={setCode}
                fontSize={fontSize}
                minimap={minimap}
                loading={langsLoading}
              />
            </div>
          </section>

          {/* Vertical Resize Handle */}
          {!editorExpanded && !consoleCollapsed && (
            <div
              role="separator"
              aria-orientation="horizontal"
              aria-label="Resize editor and console panels"
              onPointerDown={startDrag('vertical')}
              onDoubleClick={resetEditorHeight}
              title="Drag to resize height (double-click to reset)"
              className="hidden lg:flex h-2.5 shrink-0 cursor-row-resize items-center justify-center group select-none"
            >
              <div className="h-1 w-12 rounded-full bg-border group-hover:bg-primary transition-colors" />
            </div>
          )}

          {/* Bottom Console */}
          {!editorExpanded && (
            <section
              className={`${
                consoleCollapsed ? 'shrink-0' : 'flex-1 min-h-[140px] flex flex-col'
              } ${mobileView === 'console' ? 'block' : 'hidden lg:flex'}`}
            >
              <TestcaseConsole
                problem={question}
                testcases={testcases}
                generating={generating}
                generationError={generationError}
                modelUsed={modelUsed}
                validationError={validationError}
                onGenerateTestcases={() => void generateFromProblem(question)}
                onAddTestcase={addTestcase}
                onUpdateTestcase={updateTestcase}
                onRemoveTestcase={removeTestcase}
                onClearTestcases={clearTestcases}
                execResult={result}
                execLoading={execLoading}
                execError={execError}
                collapsed={consoleCollapsed}
                onToggleCollapse={() => setConsoleCollapsed((c) => !c)}
                onEditProblem={openProblemEditor}
              />
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkspacePage;
