// src/components/ui/Badge.tsx
import React from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  children: React.ReactNode;
}

const variantClasses: Record<string, string> = {
  primary: 'bg-primary text-white',
  secondary: 'bg-surface text-text',
  success: 'bg-accent text-white',
  warning: 'bg-warning text-white',
  danger: 'bg-danger text-white',
};

const Badge: React.FC<BadgeProps> = ({ variant = 'primary', className, children, ...rest }) => {
  return (
    <span
      className={cn(
        'inline-block px-2 py-0.5 rounded-full text-xs font-medium',
        variantClasses[variant] ?? variantClasses.primary,
        className
      )}
      {...rest}
    >
      {children}
    </span>
  );
};

export default Badge;
