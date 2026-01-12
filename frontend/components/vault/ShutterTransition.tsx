import { motion } from 'framer-motion';

export const ShutterTransition = ({ isChanging }: { isChanging: boolean }) => (
  <motion.div
    initial={{ scaleY: 0 }}
    animate={{ scaleY: isChanging ? 1 : 0 }}
    transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
    className="fixed inset-0 bg-cyan-950 z-50 origin-top"
  />
);
