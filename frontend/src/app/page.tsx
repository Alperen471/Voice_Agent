import Link from "next/link";
import type { ReactNode } from "react";

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth={1.75} stroke="currentColor" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.25 6.75c0 8.284 6.716 15 15 15h1.5a2.25 2.25 0 0 0 2.25-2.25v-1.372a1.5 1.5 0 0 0-1.157-1.46l-3.65-.913a1.5 1.5 0 0 0-1.516.438l-.81.94a11.288 11.288 0 0 1-5.22-5.22l.94-.81a1.5 1.5 0 0 0 .438-1.516l-.913-3.65a1.5 1.5 0 0 0-1.46-1.157H4.5A2.25 2.25 0 0 0 2.25 6.75Z"
      />
    </svg>
  );
}

function ListIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth={1.75} stroke="currentColor" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12M8.25 17.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
    </svg>
  );
}

function PencilIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth={1.75} stroke="currentColor" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
      />
    </svg>
  );
}

const CARDS: { href: string; title: string; description: string; icon: ReactNode }[] = [
  {
    href: "/conversations/new",
    title: "Yeni Konuşma Başlat",
    description: "Mikrofonunuzla sesli asistanla canlı bir görüşme başlatın.",
    icon: <PhoneIcon />,
  },
  {
    href: "/conversations",
    title: "Konuşma Geçmişi",
    description: "Tamamlanmış görüşmelerin transkriptini ve ses kaydını görüntüleyin.",
    icon: <ListIcon />,
  },
  {
    href: "/system-prompt",
    title: "Sistem Promptu",
    description: "Asistanın talimatlarını görüntüleyin ve düzenleyin.",
    icon: <PencilIcon />,
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col gap-10">
      <div className="flex flex-col gap-2">
        <span className="text-xs font-semibold tracking-wide text-accent uppercase">LiveKit Sesli Asistan</span>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Sesli Asistan Paneli
        </h1>
        <p className="max-w-lg text-sm text-zinc-600 dark:text-zinc-400">
          Sesli asistanınızı buradan yönetin: sistem promptunu düzenleyin, canlı bir görüşme başlatın veya
          geçmiş konuşmaları inceleyin.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group flex flex-col gap-3 rounded-2xl border border-zinc-200 bg-white p-5 transition-all hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
              {card.icon}
            </span>
            <div>
              <h2 className="font-medium text-zinc-900 dark:text-zinc-50">{card.title}</h2>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{card.description}</p>
            </div>
            <span className="mt-auto text-sm font-medium text-accent opacity-0 transition-opacity group-hover:opacity-100">
              Git →
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
