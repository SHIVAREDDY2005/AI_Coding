import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="border-t border-border bg-surface-dark py-3 text-center">
      <p className="text-xs text-text-muted">
        © {new Date().getFullYear()} AI Coding Platform · Local browser drafts · Powered by FastAPI &amp; Judge0
      </p>
    </footer>
  );
};

export default Footer;
