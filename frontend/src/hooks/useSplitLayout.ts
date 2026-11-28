// src/hooks/useSplitLayout.ts
import { useState, useEffect, useRef } from 'react';
import type React from 'react';

const LEFT_WIDTH_KEY = 'workspace-split:left-width';
const EDITOR_HEIGHT_KEY = 'workspace-split:editor-height';
const DEFAULT_LEFT_WIDTH = 36;
const DEFAULT_EDITOR_HEIGHT = 60;

export const useSplitLayout = () => {
  const splitContainerRef = useRef<HTMLDivElement | null>(null);
  const rightColumnRef = useRef<HTMLDivElement | null>(null);
  const dragModeRef = useRef<'horizontal' | 'vertical' | null>(null);

  const [leftWidthPct, setLeftWidthPct] = useState<number>(() => {
    try {
      const saved = Number(localStorage.getItem(LEFT_WIDTH_KEY));
      return Number.isFinite(saved) && saved >= 22 && saved <= 60 ? saved : DEFAULT_LEFT_WIDTH;
    } catch {
      return DEFAULT_LEFT_WIDTH;
    }
  });

  const [editorHeightPct, setEditorHeightPct] = useState<number>(() => {
    try {
      const saved = Number(localStorage.getItem(EDITOR_HEIGHT_KEY));
      return Number.isFinite(saved) && saved >= 30 && saved <= 82 ? saved : DEFAULT_EDITOR_HEIGHT;
    } catch {
      return DEFAULT_EDITOR_HEIGHT;
    }
  });

  useEffect(() => {
    const onPointerMove = (e: PointerEvent) => {
      if (!dragModeRef.current) return;
      if (dragModeRef.current === 'horizontal' && splitContainerRef.current) {
        const rect = splitContainerRef.current.getBoundingClientRect();
        if (rect.width > 0) {
          const pct = ((e.clientX - rect.left) / rect.width) * 100;
          const clamped = Math.min(60, Math.max(22, pct));
          setLeftWidthPct(clamped);
          try {
            localStorage.setItem(LEFT_WIDTH_KEY, String(Math.round(clamped)));
          } catch {
            // Ignore storage errors
          }
        }
      } else if (dragModeRef.current === 'vertical' && rightColumnRef.current) {
        const rect = rightColumnRef.current.getBoundingClientRect();
        if (rect.height > 0) {
          const pct = ((e.clientY - rect.top) / rect.height) * 100;
          const clamped = Math.min(82, Math.max(30, pct));
          setEditorHeightPct(clamped);
          try {
            localStorage.setItem(EDITOR_HEIGHT_KEY, String(Math.round(clamped)));
          } catch {
            // Ignore storage errors
          }
        }
      }
    };

    const onPointerUp = () => {
      if (dragModeRef.current) {
        dragModeRef.current = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, []);

  const startDrag = (mode: 'horizontal' | 'vertical') => (e: React.PointerEvent) => {
    e.preventDefault();
    dragModeRef.current = mode;
    document.body.style.cursor = mode === 'horizontal' ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';
  };

  const resetLeftWidth = () => setLeftWidthPct(DEFAULT_LEFT_WIDTH);
  const resetEditorHeight = () => setEditorHeightPct(DEFAULT_EDITOR_HEIGHT);

  return {
    splitContainerRef,
    rightColumnRef,
    leftWidthPct,
    editorHeightPct,
    startDrag,
    resetLeftWidth,
    resetEditorHeight,
  };
};
