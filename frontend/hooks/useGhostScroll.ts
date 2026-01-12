"use client";

import { useEffect, RefObject } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export const useGhostScroll = (containerRef: RefObject<HTMLElement>, targetSelector: string = ".axiom-card") => {
  useEffect(() => {
    if (!containerRef.current) return;

    const ctx = gsap.context(() => {
      gsap.from(targetSelector, {
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top 60%", // Adjusted for better visibility
          end: "bottom 80%",
          scrub: 1,
        },
        opacity: 0,
        x: -50,
        stagger: 0.2,
        filter: "blur(10px)",
      });
    }, containerRef);

    return () => ctx.revert();
  }, [containerRef, targetSelector]);
};
