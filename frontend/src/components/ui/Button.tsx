import type { ElementType, ReactNode, ComponentPropsWithoutRef } from 'react';
import { cn } from '../../utils/cn';

export type ButtonVariant = 'primary' | 'secondary' | 'accent' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonOwnProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: ReactNode;
  className?: string;
  as?: ElementType;
}

export type ButtonProps<C extends ElementType = 'button'> = ButtonOwnProps & {
  as?: C;
} & Omit<ComponentPropsWithoutRef<C>, keyof ButtonOwnProps | 'as'>;

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-dark shadow-sm shadow-primary/20',
  secondary: 'bg-surface-elevated text-text border border-border hover:border-border-light hover:bg-surface',
  accent: 'bg-accent text-white hover:bg-accent-dark shadow-sm shadow-accent/20',
  danger: 'bg-danger/15 text-danger border border-danger/30 hover:bg-danger hover:text-white',
  ghost: 'bg-transparent text-text-muted hover:text-text hover:bg-surface-elevated',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-2.5 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
};

const Button = <C extends ElementType = 'button'>(props: ButtonProps<C>) => {
  const {
    as,
    variant = 'primary',
    size = 'md',
    loading = false,
    className,
    children,
    disabled,
    ...rest
  } = props;

  const Component: ElementType = as ?? 'button';
  const isButton = Component === 'button';

  return (
    <Component
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...rest}
      {...(isButton ? { disabled: Boolean(disabled || loading) } : {})}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="animate-spin inline-block border-2 border-current border-t-transparent rounded-full w-3.5 h-3.5"
        />
      )}
      {children}
    </Component>
  );
};

export default Button;
