import type { TranscriptItem } from "@/lib/types";

function extractText(item: TranscriptItem): string {
  if (!item.content) return "";
  return item.content.filter((part): part is string => typeof part === "string").join(" ");
}

export function TranscriptList({ items }: { items: TranscriptItem[] }) {
  const messages = items.filter((item) => item.type === "message" && item.role !== "system");

  if (messages.length === 0) {
    return <p className="text-sm text-zinc-500">Transkript bulunamadı.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {messages.map((item) => (
        <div
          key={item.id}
          className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            item.role === "assistant"
              ? "self-start rounded-bl-sm bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
              : "self-end rounded-br-sm bg-accent text-accent-foreground"
          }`}
        >
          {extractText(item)}
        </div>
      ))}
    </div>
  );
}
