"use client";

import { useEffect } from "react";

export default function ErrorPage({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Beklenmeyen bir hata oluştu</h2>
      <p className="max-w-sm text-sm text-zinc-600 dark:text-zinc-400">
        Sayfa yüklenirken bir sorun çıktı. Tekrar denemek sorunu çözebilir.
      </p>
      <button
        onClick={() => retry()}
        className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-opacity hover:opacity-90"
      >
        Tekrar Dene
      </button>
    </div>
  );
}
