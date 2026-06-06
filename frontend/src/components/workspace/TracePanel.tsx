import { ChevronDown, ChevronUp, Terminal, Wrench } from "lucide-react";
import { useState } from "react";
import type { TraceStep } from "../../api/types";

interface StepCardProps {
  step: TraceStep;
  index: number;
}

function StepCard({ step, index }: StepCardProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-md border border-[#1e2530] bg-[#0f1117]">
      <button
        className="flex w-full items-center gap-2 p-3 text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#1e2530] text-xs text-[#8b93a0]">
          {index + 1}
        </span>
        <Wrench size={12} className="shrink-0 text-[#c9a84c]" />
        <span className="text-xs font-medium text-[#e8eaed]">{step.action}</span>
        <span className="ml-auto shrink-0">
          {open ? <ChevronUp size={12} className="text-[#8b93a0]" /> : <ChevronDown size={12} className="text-[#8b93a0]" />}
        </span>
      </button>
      {open && (
        <div className="space-y-2 border-t border-[#1e2530] p-3 text-xs">
          {step.thought && (
            <div>
              <p className="mb-1 font-medium text-[#8b93a0]">Thought</p>
              <p className="text-[#8b93a0] leading-relaxed">{step.thought}</p>
            </div>
          )}
          <div>
            <p className="mb-1 font-medium text-[#8b93a0]">Input</p>
            <pre className="overflow-x-auto rounded bg-[#161a22] p-2 text-[#e8eaed]">
              {step.action_input}
            </pre>
          </div>
          <div>
            <p className="mb-1 font-medium text-[#8b93a0]">Observation</p>
            <pre className="overflow-x-auto rounded bg-[#161a22] p-2 text-[#e8eaed] max-h-32">
              {step.observation}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

interface TracePanelProps {
  steps: TraceStep[];
}

export function TracePanel({ steps }: TracePanelProps) {
  const [panelOpen, setPanelOpen] = useState(false);

  return (
    <div className="rounded-lg border border-[#1e2530] bg-[#161a22]">
      <button
        className="flex w-full items-center gap-2 p-4"
        onClick={() => setPanelOpen((v) => !v)}
      >
        <Terminal size={14} className="text-[#8b93a0]" />
        <span className="text-sm font-medium text-[#e8eaed]">ReAct trace</span>
        <span className="ml-1 text-xs text-[#8b93a0]">({steps.length} steps)</span>
        <span className="ml-auto">
          {panelOpen ? <ChevronUp size={14} className="text-[#8b93a0]" /> : <ChevronDown size={14} className="text-[#8b93a0]" />}
        </span>
      </button>
      {panelOpen && (
        <div className="space-y-2 border-t border-[#1e2530] p-4">
          {steps.map((step, i) => (
            <StepCard key={i} step={step} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
