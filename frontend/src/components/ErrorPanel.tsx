interface ErrorPanelProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorPanel({ message, onRetry }: ErrorPanelProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-red-200/70 bg-red-50 px-6 py-8 text-center dark:border-red-900/40 dark:bg-red-950/20">
      <p className="text-sm font-medium text-red-700 dark:text-red-400">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-full bg-red-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-700"
        >
          Tekrar Dene
        </button>
      )}
    </div>
  );
}
