"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ApiError, startConversation } from "@/lib/api";
import { VoiceCall } from "@/components/VoiceCall";
import { ErrorPanel } from "@/components/ErrorPanel";
import type { StartConversationResponse } from "@/lib/types";

type CallState =
  | { status: "idle" }
  | { status: "connecting" }
  | { status: "in-call"; session: StartConversationResponse }
  | { status: "ending" }
  | { status: "error"; message: string };

export default function NewConversationPage() {
  const router = useRouter();
  const [state, setState] = useState<CallState>({ status: "idle" });

  const handleStart = async () => {
    setState({ status: "connecting" });
    try {
      const session = await startConversation();
      setState({ status: "in-call", session });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Görüşme başlatılamadı.";
      setState({ status: "error", message });
    }
  };

  const handleEnded = (conversationId: string) => {
    setState({ status: "ending" });
    setTimeout(() => router.push(`/conversations/${conversationId}`), 1500);
  };

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 text-center">
      {state.status === "idle" && (
        <>
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-accent-soft text-accent">
            <svg viewBox="0 0 24 24" fill="none" strokeWidth={1.5} stroke="currentColor" className="h-9 w-9">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Yeni Konuşma</h1>
            <p className="mt-2 max-w-md text-sm text-zinc-600 dark:text-zinc-400">
              Görüşmeyi başlattığınızda tarayıcınız mikrofon erişimi isteyecek. Asistan sizi karşılayacaktır.
            </p>
          </div>
          <button
            onClick={handleStart}
            className="rounded-full bg-accent px-8 py-3 text-sm font-medium text-accent-foreground transition-opacity hover:opacity-90"
          >
            Görüşmeyi Başlat
          </button>
        </>
      )}

      {state.status === "connecting" && <p className="text-sm text-zinc-600 dark:text-zinc-400">Bağlanılıyor...</p>}

      {state.status === "error" && (
        <ErrorPanel message={state.message} onRetry={() => setState({ status: "idle" })} />
      )}

      {state.status === "in-call" && (
        <VoiceCall
          token={state.session.token}
          serverUrl={state.session.url}
          onEnded={() => handleEnded(state.session.conversation_id)}
          onError={(message) => toast.error(message)}
        />
      )}

      {state.status === "ending" && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">Görüşme sonlandırılıyor, kayıt hazırlanıyor...</p>
      )}
    </div>
  );
}
