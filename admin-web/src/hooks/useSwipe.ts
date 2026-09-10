/**
 * useSwipe Hook
 * Detect touch-based swipe gestures for enhanced mobile navigation.
 */
import { useState, type TouchEvent } from 'react';

interface SwipeInput {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  minSwipeDistance?: number;
}

interface SwipeOutput {
  onTouchStart: (e: TouchEvent) => void;
  onTouchMove: (e: TouchEvent) => void;
  onTouchEnd: () => void;
}

export function useSwipe({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  minSwipeDistance = 50,
}: SwipeInput): SwipeOutput {
  const [touchStart, setTouchStart] = useState({ x: 0, y: 0 });
  const [touchEnd, setTouchEnd] = useState({ x: 0, y: 0 });

  const onTouchStart = (e: TouchEvent) => {
    setTouchEnd({ x: 0, y: 0 }); // Reset
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    });
  };

  const onTouchMove = (e: TouchEvent) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    });
  };

  const onTouchEnd = () => {
    if (!touchStart.x || !touchEnd.x) return;

    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = touchStart.y - touchEnd.y;
    const isHorizontal = Math.abs(distanceX) > Math.abs(distanceY);

    if (isHorizontal) {
      if (distanceX > minSwipeDistance) {
        onSwipeLeft?.();
      } else if (distanceX < -minSwipeDistance) {
        onSwipeRight?.();
      }
    } else {
      if (distanceY > minSwipeDistance) {
        onSwipeUp?.();
      } else if (distanceY < -minSwipeDistance) {
        onSwipeDown?.();
      }
    }
  };

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  };
}
