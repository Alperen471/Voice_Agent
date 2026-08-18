import type { ConversationStatus } from "@/lib/types";

const STYLES: Record<ConversationStatus, string> = {
  active: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  completed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
};

const LABELS: Record<ConversationStatus, string> = {
  active: "Devam Ediyor",
  completed: "Tamamlandı",
  failed: "Başarısız",
};

export function StatusBadge({ status }: { status: ConversationStatus }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${STYLES[status]}`}
    >
      {status === "active" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-600" />}
      {LABELS[status]}
    </span>
  );
}
