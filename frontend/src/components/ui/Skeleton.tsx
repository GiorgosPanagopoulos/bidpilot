export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-[#1e2530] ${className}`}
      aria-hidden="true"
    />
  );
}
