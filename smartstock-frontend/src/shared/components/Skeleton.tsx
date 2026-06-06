interface SkeletonProps {
  className?: string;
  lines?: number;
}

export default function Skeleton({ className = '', lines }: SkeletonProps) {
  if (lines) {
    return (
      <div className="space-y-3" aria-hidden="true">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`h-4 rounded-md bg-gray-100 animate-skeleton ${
              i === lines - 1 ? 'w-3/4' : 'w-full'
            }`}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`rounded-md bg-gray-100 animate-skeleton ${className}`}
      aria-hidden="true"
    />
  );
}
