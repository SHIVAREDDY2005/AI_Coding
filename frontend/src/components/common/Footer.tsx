import React from 'react';
import { Code2 } from 'lucide-react';

const CURRENT_YEAR = new Date().getFullYear();

const Footer: React.FC = () => {
  return (
    <footer className="border-t border-border bg-surface-dark/90">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-text-muted">
        <div className="flex items-center gap-2">
          <Code2 className="w-3.5 h-3.5 text-primary-light" />
          <span>
            © {CURRENT_YEAR} <strong className="font-medium text-text">AI Coding Platform</strong> · FastAPI · Judge0 · Monaco
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span>
            Developed by{' '}
            <a
              href="https://github.com/SHIVAREDDY2005"
              target="_blank"
              rel="noreferrer"
              className="font-medium text-text hover:text-primary-light transition-colors"
            >
              Surkanti Shiva Reddy
            </a>
          </span>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
