import { renderHook } from '@testing-library/react';
import { useCarouselScroll } from './useCarouselScroll';
import { describe, it, expect, vi } from 'vitest';

// Mock framer-motion useScroll
vi.mock('framer-motion', async () => {
  const actual = await vi.importActual('framer-motion');
  return {
    ...actual,
    useScroll: () => ({
      scrollYProgress: {
        get: () => 0.5,
      },
    }),
    useTransform: (value: any, mapping: any, output: any) => ({
      get: () => output[0], // simplified mock
    }),
  };
});

describe('useCarouselScroll', () => {
  it('should return initial transform values', () => {
    const { result } = renderHook(() => useCarouselScroll());
    
    // We expect it to return motion values or projected values
    expect(result.current).toBeDefined();
    expect(result.current.rotateX).toBeDefined();
    expect(result.current.z).toBeDefined();
  });
});
