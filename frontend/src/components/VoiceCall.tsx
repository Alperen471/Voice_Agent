"use client";

import "@livekit/components-styles";
import { useMemo } from "react";
import {
  BarVisualizer,
  DisconnectButton,
  LiveKitRoom,
  RoomAudioRenderer,
  StartAudio,
  TrackToggle,
  useConnectionState,
  useTranscriptions,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState, Track } from "livekit-client";

interface VoiceCallProps {
  token: string;
  serverUrl: string;
  onEnded: () => void;
  onError: (message: string) => void;
}

export function VoiceCall({ token, serverUrl, onEnded, onError }: VoiceCallProps) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect
      audio
      video={false}
      onDisconnected={onEnded}
      onError={(err) => onError(err.message || "Bağlantı hatası oluştu.")}
      className="flex w-full max-w-md flex-col items-center gap-6 rounded-2xl border border-zinc-200 bg-surface p-8 shadow-sm dark:border-zinc-800"
    >
      <RoomAudioRenderer />
      <StartAudio
        label="Sesi Etkinleştir"
        className="rounded-full bg-amber-500 px-4 py-2 text-sm font-medium text-white"
      />
      <CallPanel />
    </LiveKitRoom>
  );
}

const STATE_LABELS: Record<string, string> = {
  connecting: "Bağlanılıyor...",
  "pre-connect-buffering": "Bağlanılıyor...",
  initializing: "Hazırlanıyor...",
  idle: "Bekleniyor...",
  listening: "Sizi dinliyor",
  thinking: "Yanıt hazırlanıyor...",
  speaking: "Asistan konuşuyor",
  disconnected: "Bağlantı kesildi",
  failed: "Bağlantı başarısız oldu",
};

function CallPanel() {
  const { state, audioTrack, agent } = useVoiceAssistant();
  const connectionState = useConnectionState();
  const transcriptions = useTranscriptions();

  const sorted = useMemo(
    () => [...transcriptions].sort((a, b) => a.streamInfo.timestamp - b.streamInfo.timestamp),
    [transcriptions],
  );

  const statusLabel =
    connectionState === ConnectionState.Connecting ? "Bağlanılıyor..." : (STATE_LABELS[state] ?? state);

  return (
    <div className="flex w-full flex-col items-center gap-6">
      <div className="flex flex-col items-center gap-3">
        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-accent-soft">
          <BarVisualizer state={state} track={audioTrack} barCount={5} className="h-10 text-accent" />
        </div>
        <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          {statusLabel}
        </span>
      </div>

      <div className="h-44 w-full overflow-y-auto rounded-xl border border-zinc-200 bg-background p-3 text-left text-sm dark:border-zinc-800">
        {sorted.length === 0 ? (
          <p className="text-zinc-400">Konuşma başladığında transkript burada görünecek.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {sorted.map((t) => (
              <p
                key={t.streamInfo.id}
                className={
                  t.participantInfo.identity === agent?.identity
                    ? "text-zinc-900 dark:text-zinc-100"
                    : "font-medium text-accent"
                }
              >
                {t.text}
              </p>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <TrackToggle
          source={Track.Source.Microphone}
          showIcon
          className="rounded-full border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 data-[lk-enabled=false]:border-red-300 data-[lk-enabled=false]:bg-red-100 data-[lk-enabled=false]:text-red-700 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
        />
        <DisconnectButton className="rounded-full bg-red-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700">
          Görüşmeyi Bitir
        </DisconnectButton>
      </div>
    </div>
  );
}
