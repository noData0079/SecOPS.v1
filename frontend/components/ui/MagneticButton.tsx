"use client";

import { motion, HTMLMotionProps } from 'framer-motion';
import React from 'react';

interface MagneticButtonProps extends HTMLMotionProps<"button"> {
  children: React.ReactNode;
}

export const MagneticButton: React.FC<MagneticButtonProps> = ({ children, className = "", ...props }) => (
  <motion.button
    whileHover={{ scale: 1.05, boxShadow: "0px 0px 20px rgba(0, 255, 255, 0.5)" }}
    whileTap={{ scale: 0.95 }}
    transition={{ type: "spring", stiffness: 400, damping: 10 }}
    className={`px-8 py-4 bg-cyan-950/80 border border-sovereign-cyan text-sovereign-cyan rounded-lg font-mono uppercase tracking-widest backdrop-blur-sm ${className}`}
    {...props}
  >
    {children}
  </motion.button>
);
