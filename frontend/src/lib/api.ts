import type {
  ConversationDetail,
  ConversationSummary,
  StartConversationResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Sunucuya bağlanılamadı. Backend'in çalıştığından emin olun.",
      "network_error",
      0,
    );
  }

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const message = body?.error?.message ?? "Beklenmeyen bir hata oluştu.";
    const code = body?.error?.code ?? "unknown_error";
    throw new ApiError(message, code, response.status);
  }

  return body as T;
}

export function getSystemPrompt() {
  return request<{ content: string }>("/api/system-prompt");
}

export function updateSystemPrompt(content: string) {
  return request<{ content: string }>("/api/system-prompt", {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

export function startConversation() {
  return request<StartConversationResponse>("/api/conversations", {
    method: "POST",
  });
}

export function listConversations() {
  return request<{ conversations: ConversationSummary[] }>("/api/conversations");
}

export function getConversation(id: string) {
  return request<ConversationDetail>(`/api/conversations/${id}`);
}
