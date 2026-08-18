"use client";

import { useCallback } from "react";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import { getConversation } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { ErrorPanel } from "@/components/ErrorPanel";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/Skeleton";
import { RecordingPlayer } from "./_components/RecordingPlayer";
import { TranscriptList } from "./_components/TranscriptList";

export default function ConversationDetailPage() {
  const params = useParams<{ id: string }>();
  const fetcher = useCallback(() => getConversation(params.id), [params.id]);
  const { data: conversation, error, loading, reload } = useAsync(fetcher, [params.id]);

  if (error) return <ErrorPanel message={error} onRetry={reload} />;
  if (loading || !conversation) {
    return (
      <div className="flex flex-1 flex-col gap-5">
        <Skeleton className="h-16" />
        <Skeleton className="h-24" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-6">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Konuşma</h1>
          <StatusBadge status={conversation.status} />
        </div>
        <span className="font-mono text-xs text-zinc-500">{conversation.id}</span>
        <span className="text-sm text-zinc-600 dark:text-zinc-400">
          {format(new Date(conversation.started_at), "d MMMM yyyy HH:mm", { locale: tr })}
          {conversation.ended_at && ` – ${format(new Date(conversation.ended_at), "HH:mm", { locale: tr })}`}
        </span>
      </div>

      {conversation.status === "active" && (
        <ErrorPanel
          message="Bu konuşma hâlâ devam ediyor ya da transkript henüz kaydedilmedi. Birkaç saniye sonra yenileyin."
          onRetry={reload}
        />
      )}

      {conversation.status === "failed" && conversation.error_message && (
        <ErrorPanel message={conversation.error_message} />
      )}

      <RecordingPlayer url={conversation.recording_url} />

      <div className="flex flex-col gap-3">
        <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Transkript</h2>
        <TranscriptList items={conversation.transcript?.items ?? []} />
      </div>
    </div>
  );
}
