export function RecordingPlayer({ url }: { url: string | null }) {
  if (!url) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-300 p-4 text-sm text-zinc-500 dark:border-zinc-700">
        Bu görüşme için ses kaydı yapılandırılmamış.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-surface p-4 dark:border-zinc-800">
      <h2 className="mb-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">Ses Kaydı</h2>
      <audio controls src={url} className="w-full" />
    </div>
  );
}
