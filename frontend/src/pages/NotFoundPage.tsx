// src/pages/NotFoundPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';

const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8">
      <h1 className="text-5xl font-bold mb-4 text-primary">404</h1>
      <p className="text-lg mb-6 text-text">Page not found.</p>
      <Button as={Link} to="/" variant="primary">
        Go Home
      </Button>
    </div>
  );
};

export default NotFoundPage;
