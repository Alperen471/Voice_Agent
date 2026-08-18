"use client";

import Link from "next/link";
import { listConversations } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { ErrorPanel } from "@/components/ErrorPanel";
import { PageHeader } from "@/components/PageHeader";
import { Skeleton } from "@/components/Skeleton";
import { ConversationRow } from "./_components/ConversationRow";

export default function ConversationsPage() {
  const { data, error, loading, reload } = useAsync(listConversations, []);

  return (
    <div className="flex flex-1 flex-col gap-5">
      <PageHeader
        title="Konuşmalar"
        action={
          <Link
            href="/conversations/new"
            className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-opacity hover:opacity-90"
          >
            Yeni Konuşma
          </Link>
        }
      />

      {error ? (
        <ErrorPanel message={error} onRetry={reload} />
      ) : loading || !data ? (
        <Skeleton className="h-40" />
      ) : data.conversations.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500 dark:border-zinc-700">
          Henüz kaydedilmiş bir konuşma yok.
        </div>
      ) : (
        <ul className="divide-y divide-zinc-200 overflow-hidden rounded-xl border border-zinc-200 bg-surface dark:divide-zinc-800 dark:border-zinc-800">
          {data.conversations.map((c) => (
            <li key={c.id}>
              <ConversationRow conversation={c} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
