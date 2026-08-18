import Link from "next/link";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import { StatusBadge } from "@/components/StatusBadge";
import type { ConversationSummary } from "@/lib/types";

export function ConversationRow({ conversation }: { conversation: ConversationSummary }) {
  return (
    <Link
      href={`/conversations/${conversation.id}`}
      className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
    >
      <div className="flex flex-col gap-1">
        <span className="font-mono text-xs text-zinc-500 dark:text-zinc-500">{conversation.id}</span>
        <span className="text-sm text-zinc-700 dark:text-zinc-300">
          {format(new Date(conversation.started_at), "d MMMM yyyy HH:mm", { locale: tr })}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-zinc-500 dark:text-zinc-400">{conversation.turn_count} mesaj</span>
        {conversation.has_recording && (
          <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-medium text-accent">
            Kayıt
          </span>
        )}
        <StatusBadge status={conversation.status} />
      </div>
    </Link>
  );
}
