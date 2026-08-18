import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Sayfa bulunamadı</h2>
      <p className="max-w-sm text-sm text-zinc-600 dark:text-zinc-400">
        Aradığınız sayfa mevcut değil veya taşınmış olabilir.
      </p>
      <Link
        href="/"
        className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-opacity hover:opacity-90"
      >
        Ana Sayfaya Dön
      </Link>
    </div>
  );
}
