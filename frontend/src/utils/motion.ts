import { type Variants, type Transition } from "framer-motion";

/* ============================================================
   小红薯医生 Framer Motion Presets
   Reusable animation variants and transition configs
   ============================================================ */

// --------------- Transition Presets ---------------

export const springGentle: Transition = {
  type: "spring",
  stiffness: 120,
  damping: 20,
  mass: 1,
};

export const springBouncy: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 15,
  mass: 0.8,
};

export const springStiff: Transition = {
  type: "spring",
  stiffness: 400,
  damping: 30,
  mass: 0.8,
};

export const easeOut: Transition = {
  type: "tween",
  ease: [0.4, 0, 0.2, 1],
  duration: 0.4,
};

// --------------- Variants ---------------

/** Fade in from below — the workhorse entrance animation */
export const fadeInUp: Variants = {
  hidden: {
    opacity: 0,
    y: 30,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 120,
      damping: 20,
    },
  },
};

/** Simple opacity fade */
export const fadeIn: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

/** Container that staggers its children */
export const staggerContainer: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.05,
    },
  },
};

/** Scale in from slightly smaller */
export const scaleIn: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.9,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 20,
    },
  },
};

/** Slide in from the left */
export const slideInLeft: Variants = {
  hidden: {
    opacity: 0,
    x: -60,
  },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 120,
      damping: 20,
    },
  },
};

/** Slide in from the right */
export const slideInRight: Variants = {
  hidden: {
    opacity: 0,
    x: 60,
  },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 120,
      damping: 20,
    },
  },
};

/** Full-page route transition variant */
export const pageTransition: Variants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.25,
      ease: [0.4, 0, 1, 1],
    },
  },
};

/** Card hover interaction — use with whileHover */
export const cardHover = {
  scale: 1.02,
  boxShadow: "0 12px 32px rgba(0, 0, 0, 0.10)",
  transition: {
    type: "spring" as const,
    stiffness: 300,
    damping: 20,
  },
};

/** Card tap interaction — use with whileTap */
export const cardTap = {
  scale: 0.98,
  transition: {
    type: "spring" as const,
    stiffness: 400,
    damping: 25,
  },
};

// --------------- Helper Functions ---------------

/**
 * Animate a number counting up from 0 to `target` over `duration` ms.
 * Uses requestAnimationFrame for smooth 60fps animation.
 *
 * @param target  - The final number to reach
 * @param duration - Animation duration in milliseconds (default 1500)
 * @param onUpdate - Callback invoked on each frame with the current value
 * @param onComplete - Optional callback when animation finishes
 * @returns A cancel function to stop the animation
 */
export function countUp(
  target: number,
  duration: number = 1500,
  onUpdate: (value: number) => void,
  onComplete?: () => void,
): () => void {
  let startTime: number | null = null;
  let animationId: number;
  let cancelled = false;

  const step = (timestamp: number) => {
    if (cancelled) return;

    if (startTime === null) {
      startTime = timestamp;
    }

    const elapsed = timestamp - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out cubic for a satisfying deceleration
    const easedProgress = 1 - Math.pow(1 - progress, 3);
    const currentValue = Math.round(easedProgress * target);

    onUpdate(currentValue);

    if (progress < 1) {
      animationId = requestAnimationFrame(step);
    } else {
      onUpdate(target); // ensure exact final value
      onComplete?.();
    }
  };

  animationId = requestAnimationFrame(step);

  return () => {
    cancelled = true;
    cancelAnimationFrame(animationId);
  };
}
