import React, { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Menu, X, Code2 } from 'lucide-react';
import { fetchHealth } from '../../services/healthService';

const Navbar: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    let active = true;
    const check = async () => {
      try {
        await fetchHealth();
        if (active) setBackendStatus('online');
      } catch {
        if (active) setBackendStatus('offline');
      }
    };
    void check();
    return () => {
      active = false;
    };
  }, []);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `block px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-primary/15 text-primary-light'
        : 'text-text-muted hover:text-text hover:bg-surface-elevated'
    }`;

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface/90 backdrop-blur">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 text-base font-bold text-text hover:text-white">
            <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-primary/20 text-primary-light border border-primary/30">
              <Code2 className="w-4 h-4" />
            </span>
            <span>AI Coding Platform</span>
          </Link>

          <nav aria-label="Primary navigation" className="hidden md:flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              Home
            </NavLink>
            <NavLink to="/problems" className={navLinkClass}>
              Problems
            </NavLink>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <span
            className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border border-border bg-surface-dark text-text-muted"
            title="FastAPI Backend Status"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-accent'
                  : backendStatus === 'offline'
                  ? 'bg-danger'
                  : 'bg-warning animate-pulse'
              }`}
            />
            {backendStatus === 'online'
              ? 'API Connected'
              : backendStatus === 'offline'
              ? 'API Offline'
              : 'Checking API...'}
          </span>

          <button
            type="button"
            className="md:hidden p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface-elevated"
            onClick={() => setOpen((prev) => !prev)}
            aria-label="Toggle navigation menu"
            aria-expanded={open}
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {open && (
          <nav aria-label="Mobile navigation" className="w-full md:hidden pt-3 pb-1 border-t border-border mt-2.5 flex flex-col gap-1">
            <NavLink to="/" end className={navLinkClass} onClick={() => setOpen(false)}>
              Home
            </NavLink>
            <NavLink to="/problems" className={navLinkClass} onClick={() => setOpen(false)}>
              Problems
            </NavLink>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Navbar;
