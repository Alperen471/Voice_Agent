export type ConversationStatus = "active" | "completed" | "failed";

export interface TranscriptItem {
  id: string;
  type: string;
  role?: "user" | "assistant" | "system" | "developer";
  content?: string[];
  created_at?: number;
  interrupted?: boolean;
}

export interface Transcript {
  items: TranscriptItem[];
}

export interface ConversationSummary {
  id: string;
  status: ConversationStatus;
  started_at: string;
  ended_at: string | null;
  has_recording: boolean;
  turn_count: number;
}

export interface ConversationDetail {
  id: string;
  status: ConversationStatus;
  started_at: string;
  ended_at: string | null;
  transcript: Transcript | null;
  recording_url: string | null;
  error_message: string | null;
}

export interface StartConversationResponse {
  conversation_id: string;
  room_name: string;
  token: string;
  url: string;
}
