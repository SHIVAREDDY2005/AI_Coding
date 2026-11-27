// src/features/editor/LanguageSelector.tsx
import React from 'react';
import type { LanguageInfo } from '../../types/language';

interface LanguageSelectorProps {
  languages: LanguageInfo[];
  selectedId: number | null;
  onChange: (id: number) => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  languages,
  selectedId,
  onChange,
  loading = false,
  error = null,
  onRetry,
}) => {
  if (error) {
    return (
      <div className="inline-flex items-center gap-2">
        <span className="text-xs text-danger" title={error}>
          Failed to load languages
        </span>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="text-xs text-primary-light hover:underline"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  return (
    <select
      aria-label="Programming language"
      value={selectedId ?? ''}
      onChange={(e) => {
        const val = Number(e.target.value);
        if (!Number.isNaN(val) && val > 0) {
          onChange(val);
        }
      }}
      disabled={loading || languages.length === 0}
      className="px-3 py-1.5 text-sm rounded-lg border border-border bg-surface-elevated text-text focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
    >
      {loading ? (
        <option value="">Loading languages...</option>
      ) : languages.length === 0 ? (
        <option value="">No languages available</option>
      ) : (
        <>
          <option value="" disabled>
            Select language
          </option>
          {languages.map((lang) => (
            <option key={lang.id} value={lang.id}>
              {lang.name}
            </option>
          ))}
        </>
      )}
    </select>
  );
};

export default LanguageSelector;
