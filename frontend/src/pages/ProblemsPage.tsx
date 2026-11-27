// src/pages/ProblemsPage.tsx
import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, ArrowRight } from 'lucide-react';
import { getAllProblems, getUniqueTags, getUniqueDifficulties } from '../services/problemService';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const PAGE_SIZE = 10;

const ProblemsPage: React.FC = () => {
  const allProblems = useMemo(() => getAllProblems(), []);
  const [search, setSearch] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string>('');
  const [page, setPage] = useState(1);

  const difficulties = getUniqueDifficulties();
  const tags = getUniqueTags();

  const filtered = useMemo(() => {
    return allProblems.filter((p) => {
      const matchesSearch = p.title.toLowerCase().includes(search.toLowerCase());
      const matchesDiff = selectedDifficulty ? p.difficulty === selectedDifficulty : true;
      const matchesTag = selectedTag ? p.tags.includes(selectedTag) : true;
      return matchesSearch && matchesDiff && matchesTag;
    });
  }, [allProblems, search, selectedDifficulty, selectedTag]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  const paginated = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page]);

  React.useEffect(() => {
    setPage(1);
  }, [search, selectedDifficulty, selectedTag]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-1">Problems</h1>
        <p className="text-sm text-text-muted">
          Problem catalogue is ready for backend catalogue API integration.
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-3">
        <input
          type="text"
          placeholder="Search problems..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 text-sm rounded-lg border border-border bg-surface text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary w-full md:w-72"
        />
        <div className="flex flex-wrap gap-2">
          <select
            aria-label="Filter by difficulty"
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Difficulties</option>
            {difficulties.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by tag"
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Tags</option>
            {tags.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Problem list or genuine empty state */}
      {paginated.length === 0 ? (
        <div className="text-center py-16 px-4 rounded-2xl border border-dashed border-border bg-surface/50">
          <FolderOpen className="w-10 h-10 text-text-muted mx-auto mb-3" />
          <p className="text-lg font-semibold text-white mb-1">No problems available yet.</p>
          <p className="text-sm text-text-muted max-w-md mx-auto mb-6">
            The backend does not currently provide a problem catalogue endpoint. Start solving immediately by entering your own problem statement on the Home page.
          </p>
          <Button as={Link} to="/" variant="primary">
            Enter Custom Problem
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {paginated.map((p) => (
            <div key={p.id} className="border border-border rounded-xl p-4 bg-surface">
              <h2 className="text-lg font-medium mb-2 text-primary-light">
                <Link to={`/problems/${p.id}`} className="hover:underline">
                  {p.title}
                </Link>
              </h2>
              <div className="flex flex-wrap items-center gap-1.5 mb-2">
                <Badge variant="success">{p.difficulty}</Badge>
                {p.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
              <p className="text-sm text-text-muted mb-3">{p.description}</p>
              <Button as={Link} to={`/problems/${p.id}`} variant="primary" size="sm">
                Solve
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Pagination controls */}
      {filtered.length > 0 && (
        <div className="flex justify-center items-center mt-6 gap-4">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-text-muted">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};

export default ProblemsPage;
