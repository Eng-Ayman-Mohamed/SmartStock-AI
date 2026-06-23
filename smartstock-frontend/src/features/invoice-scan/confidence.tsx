type ConfidenceTone = { label: string; className: string; dot: string };

function confidenceTone(value = 0): ConfidenceTone {
  if (value >= 0.9) {
    return {
      label: 'High',
      className: 'bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-200',
      dot: 'bg-green-600 dark:bg-green-400',
    };
  }
  if (value >= 0.7) {
    return {
      label: 'Review',
      className: 'bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200',
      dot: 'bg-amber-600 dark:bg-amber-400',
    };
  }
  return {
    label: 'Please verify',
    className: 'bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-200',
    dot: 'bg-red-600 dark:bg-red-400',
  };
}

export function ConfidenceBadge({ value }: { value?: number }) {
  if (value === undefined || value === null) return null;
  const tone = confidenceTone(value);
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-eyebrow ${tone.className}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${tone.dot}`} />
      {Math.round(value * 100)}% {tone.label}
    </span>
  );
}
