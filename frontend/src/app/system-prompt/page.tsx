"use client";

import { useState } from "react";
import { toast } from "sonner";
import { ApiError, getSystemPrompt, updateSystemPrompt } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { ErrorPanel } from "@/components/ErrorPanel";
import { PageHeader } from "@/components/PageHeader";
import { Skeleton } from "@/components/Skeleton";

export default function SystemPromptPage() {
  const { data, error, loading, reload } = useAsync(getSystemPrompt, []);
  const [draft, setDraft] = useState<string | null>(null);
  const [savedSnapshot, setSavedSnapshot] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const baseline = savedSnapshot ?? data?.content ?? "";
  const content = draft ?? baseline;
  const isDirty = content !== baseline;

  const handleSave = async () => {
    setSaving(true);
    try {
      const result = await updateSystemPrompt(content);
      setSavedSnapshot(result.content);
      setDraft(null);
      toast.success("Sistem promptu kaydedildi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Sistem promptu kaydedilemedi.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-5">
      <PageHeader
        title="Sistem Promptu"
        description="Asistanın görüşme başında izleyeceği talimatlar. Değişiklikler bir sonraki görüşmede geçerli olur."
      />

      {loading ? (
        <Skeleton className="h-72" />
      ) : error ? (
        <ErrorPanel message={error} onRetry={reload} />
      ) : (
        <>
          <textarea
            value={content}
            onChange={(e) => setDraft(e.target.value)}
            rows={16}
            spellCheck={false}
            className="w-full flex-1 resize-y rounded-xl border border-zinc-300 bg-surface p-4 font-mono text-sm text-zinc-900 shadow-sm outline-none transition-colors focus:border-accent dark:border-zinc-700 dark:text-zinc-100"
          />
          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={!isDirty || saving}
              className="rounded-full bg-accent px-5 py-2 text-sm font-medium text-accent-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {saving ? "Kaydediliyor..." : "Kaydet"}
            </button>
            {isDirty && !saving && (
              <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                Kaydedilmemiş değişiklikler var
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
