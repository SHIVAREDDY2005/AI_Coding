// src/features/workspace/ProblemPanel.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Save } from 'lucide-react';
import Button from '../../components/ui/Button';

interface ProblemPanelProps {
  question: string;
  editingProblem: boolean;
  problemDraft: string;
  onChangeDraft: (val: string) => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
}

export const ProblemPanel: React.FC<ProblemPanelProps> = ({
  question,
  editingProblem,
  problemDraft,
  onChangeDraft,
  onCancelEdit,
  onSaveEdit,
}) => {
  return (
    <div className="p-4 overflow-y-auto custom-scrollbar flex-1 min-h-0">
      {editingProblem ? (
        <div className="flex flex-col gap-3 h-full">
          <p className="text-xs text-text-muted">
            Name parameters in <strong>Input Format</strong> (e.g.{' '}
            <code className="text-text">arr = [1, 2, 3], target = 5</code>), specify the return value in{' '}
            <strong>Output Format</strong> (e.g. <code className="text-text">true</code> or{' '}
            <code className="text-text">10</code>), and include <strong>Constraints</strong>.
          </p>
          <textarea
            value={problemDraft}
            onChange={(e) => onChangeDraft(e.target.value)}
            rows={12}
            placeholder="Enter problem description, input format, output format, and constraints..."
            className="w-full flex-1 p-3 rounded-lg border border-border bg-surface-dark text-text text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary resize-y"
          />
          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={onCancelEdit}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={!problemDraft.trim()}
              onClick={onSaveEdit}
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
  );
};
