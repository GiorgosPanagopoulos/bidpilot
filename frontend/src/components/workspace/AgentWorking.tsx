import { motion } from "framer-motion";

const STEPS = [
  "Extracting requirements from document…",
  "Analysing capability gaps…",
  "Retrieving relevant clauses…",
  "Drafting sections with citations…",
  "Running self-check…",
];

export function AgentWorking() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-16">
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-2 w-2 rounded-full bg-[#c9a84c]"
            animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
            transition={{ duration: 1.2, delay: i * 0.2, repeat: Infinity }}
          />
        ))}
      </div>
      <div className="space-y-2 text-center">
        {STEPS.map((step, i) => (
          <motion.p
            key={step}
            className="text-xs text-[#8b93a0]"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.5, duration: 0.4 }}
          >
            {step}
          </motion.p>
        ))}
      </div>
      <p className="text-xs text-[#8b93a0]">
        This may take up to 60 seconds&nbsp;·&nbsp;
        <span className="text-[#c9a84c]/60">SSE streaming can be added when backend supports it</span>
      </p>
    </div>
  );
}
