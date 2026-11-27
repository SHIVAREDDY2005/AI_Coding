// src/features/editor/CodeEditor.tsx
import React, { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import type { LanguageInfo } from '../../types/language';

export interface CodeEditorProps {
  language: LanguageInfo | null;
  code: string;
  onChange: (value: string) => void;
  fontSize?: number;
  minimap?: boolean;
  loading?: boolean;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  language,
  code,
  onChange,
  fontSize = 14,
  minimap = false,
  loading = false,
}) => {
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);
  const monacoRef = useRef<Parameters<OnMount>[1] | null>(null);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    editor.updateOptions({
      automaticLayout: true,
      wordWrap: 'on',
      minimap: { enabled: minimap },
      fontSize,
      tabSize: 4,
      insertSpaces: true,
      scrollBeyondLastLine: false,
      padding: { top: 12, bottom: 12 },
    });
  };

  // Sync editor options dynamically when fontSize or minimap changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        fontSize,
        minimap: { enabled: minimap },
      });
    }
  }, [fontSize, minimap]);

  // Update Monaco language mode when selected language changes
  useEffect(() => {
    if (editorRef.current && monacoRef.current && language?.monaco_id) {
      const model = editorRef.current.getModel();
      if (model) {
        monacoRef.current.editor.setModelLanguage(model, language.monaco_id);
      }
    }
  }, [language]);

  return (
    <Editor
      height="100%"
      defaultLanguage={language?.monaco_id ?? 'plaintext'}
      language={language?.monaco_id ?? 'plaintext'}
      value={code}
      onChange={(value) => onChange(value ?? '')}
      theme="vs-dark"
      loading={
        <div className="flex items-center justify-center h-full text-sm text-text-muted">
          {loading ? 'Loading language metadata...' : 'Initializing Monaco Editor...'}
        </div>
      }
      options={{
        automaticLayout: true,
        wordWrap: 'on',
        minimap: { enabled: minimap },
        fontSize,
        scrollBeyondLastLine: false,
        padding: { top: 12, bottom: 12 },
      }}
      onMount={handleEditorDidMount}
    />
  );
};

export default CodeEditor;
