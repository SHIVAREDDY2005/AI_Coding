import React, { useEffect, useState } from 'react';
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
  AlertTriangle,
  X,
  Pencil,
  Save,
  FileCode2,
} from 'lucide-react';
import Button from '../components/ui/Button';
import LanguageSelector from '../features/editor/LanguageSelector';
import CodeEditor from '../features/editor/CodeEditor';
import { TestcaseConsole } from '../features/execution/TestcaseConsole';
import { useLanguages } from '../hooks/useLanguages';
import { useCodeDraft } from '../hooks/useCodeDraft';
import { useCodeExecution } from '../hooks/useCodeExecution';
import { useTestcases } from '../hooks/useTestcases';
import { useAiMentor } from '../hooks/useAiMentor';
import { buildFunctionTemplate } from '../utils/functionSignature';

type MobileView = 'problem' | 'code' | 'console';

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
  const [mobileView, setMobileView] = useState<MobileView>('code');
  const [validationError, setValidationError] = useState<string | null>(null);

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
    suggestion,
    loading: aiLoading,
    error: aiError,
    requestHelp,
    clearSuggestion,
  } = useAiMentor();

  const selectedLanguage = languages.find((l) => l.id === selectedLangId) ?? null;

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

    await run({
      code,
      language: selectedLanguage.id,
      language_id: selectedLanguage.id,
      testcases: check.payload,
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
            onClick={() => void requestHelp(question, code, result)}
            title={!code.trim() ? 'Write some code first to get AI mentoring' : 'Get AI mentoring hint'}
          >
            <Sparkles className="w-3.5 h-3.5 text-primary-light" />
            AI Help
          </Button>

          <Button
            type="button"
            variant="danger"
            size="sm"
            onClick={resetDraft}
            disabled={!code}
            title="Clear current language draft"
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

      {/* Main Split Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-[620px]">
        {/* Left Panel: Problem Statement & Explicit AI Mentor */}
        <section
          className={`lg:col-span-5 flex flex-col gap-3 min-h-0 ${
            mobileView === 'problem' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          <div className="flex-1 flex flex-col border border-border rounded-xl bg-surface overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 bg-surface-dark border-b border-border">
              <h2 className="text-sm font-semibold text-white">Problem Statement</h2>
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
            </div>
            <div className="p-4 overflow-y-auto custom-scrollbar flex-1">
              {editingProblem ? (
                <div className="flex flex-col gap-3 h-full">
                  <p className="text-xs text-text-muted">
                    Refine your problem statement with explicit <strong>Input Format</strong>,{' '}
                    <strong>Expected Output</strong>, and <strong>Constraints</strong> for accurate AI test generation.
                  </p>
                  <textarea
                    value={problemDraft}
                    onChange={(e) => setProblemDraft(e.target.value)}
                    rows={12}
                    placeholder="Enter problem description, input format, output format, and constraints..."
                    className="w-full flex-1 p-3 rounded-lg border border-border bg-surface-dark text-text text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary resize-y"
                  />
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingProblem(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      disabled={!problemDraft.trim()}
                      onClick={saveProblemEdit}
                    >
                      <Save className="w-3.5 h-3.5" />
                      Save Problem
                    </Button>
                  </div>
                </div>
              ) : question ? (
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-text">
                  {question}
                </pre>
              ) : (
                <div className="py-10 text-center text-sm text-text-muted">
                  <p className="mb-3">No problem statement found for this workspace session.</p>
                  <Button as={Link} to="/" variant="primary" size="sm">
                    Enter a Problem Statement
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* AI Mentor Card (Only shown when explicitly requested or errored) */}
          {(suggestion || aiError) && (
            <div className="border border-primary/40 rounded-xl bg-surface p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold text-primary-light">
                  <Sparkles className="w-4 h-4" />
                  <span>AI Mentor Feedback</span>
                </div>
                <button
                  type="button"
                  onClick={clearSuggestion}
                  aria-label="Dismiss AI feedback"
                  className="text-text-muted hover:text-text"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              {aiError ? (
                <div className="flex items-start gap-2 text-xs text-danger">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{aiError}</span>
                </div>
              ) : suggestion ? (
                <div className="space-y-1.5 text-xs">
                  <p>
                    <span className="text-text-muted font-semibold">Category: </span>
                    <span className="px-1.5 py-0.5 rounded bg-primary/15 text-primary-light">
                      {suggestion.mistake_type}
                    </span>
                  </p>
                  <p className="text-text">
                    <span className="text-text-muted font-semibold">Issue: </span>
                    {suggestion.issue}
                  </p>
                  <p className="text-accent">
                    <span className="font-semibold">Hint: </span>
                    {suggestion.hint}
                  </p>
                </div>
              ) : null}
            </div>
          )}
        </section>

        {/* Right Panel: Monaco Code Editor + Testcase Console */}
        <div className="lg:col-span-7 flex flex-col gap-3 min-h-0">
          {/* Monaco Editor */}
          <section
            className={`flex-1 flex flex-col border border-border rounded-xl bg-surface overflow-hidden min-h-[340px] ${
              mobileView === 'code' ? 'flex' : 'hidden lg:flex'
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2 bg-surface-dark border-b border-border text-xs text-text-muted">
              <span>
                Editor{' '}
                {selectedLanguage ? (
                  <span className="text-text font-medium">
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
                    onClick={() => setCode(buildFunctionTemplate(selectedLanguage.id, testcases))}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-primary/15 border border-primary/30 text-primary-light hover:bg-primary/25 transition-colors"
                    title="Insert empty function signature matching your selected language and test cases"
                  >
                    <FileCode2 className="w-3.5 h-3.5" />
                    Insert Function Template
                  </button>
                )}
              </div>
            </div>
            <div className="flex-1 min-h-[300px]">
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

          {/* Bottom Console */}
          <section className={mobileView === 'console' ? 'block' : 'hidden lg:block'}>
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
        </div>
      </div>
    </div>
  );
};

export default WorkspacePage;
