import { AlertCircle, X } from "lucide-react";

interface ToastProps {
  message: string;
  onClose: () => void;
}

export function Toast({ message, onClose }: ToastProps) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-start gap-3 rounded-lg border border-red-800 bg-[#161a22] p-4 shadow-xl">
      <AlertCircle size={18} className="mt-0.5 shrink-0 text-red-400" />
      <span className="text-sm text-[#e8eaed]">{message}</span>
      <button onClick={onClose} className="ml-2 text-[#8b93a0] hover:text-[#e8eaed]">
        <X size={16} />
      </button>
    </div>
  );
}
