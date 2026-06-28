import { useState, useEffect } from 'react';

const MOBILE = 768;
const TABLET = 1024;

function getBreakpoint(width: number) {
  return {
    isMobile: width < MOBILE,
    isTablet: width >= MOBILE && width < TABLET,
    isDesktop: width >= TABLET,
  };
}

export function useBreakpoint() {
  const [bp, setBp] = useState(() =>
    typeof window !== 'undefined' ? getBreakpoint(window.innerWidth) : { isMobile: false, isTablet: false, isDesktop: true }
  );

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE - 1}px)`);
    const handler = () => setBp(getBreakpoint(window.innerWidth));
    handler();
    mq.addEventListener('change', handler);
    window.addEventListener('resize', handler);
    return () => {
      mq.removeEventListener('change', handler);
      window.removeEventListener('resize', handler);
    };
  }, []);

  return bp;
}
