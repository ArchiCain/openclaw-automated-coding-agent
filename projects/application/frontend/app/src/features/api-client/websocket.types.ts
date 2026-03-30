export interface ChatMessage {
  message: string;
  agentId: string;
  threadId?: string;
}

export interface ChatChunk {
  chunk: string;
  threadId: string;
}

export interface ChatComplete {
  threadId: string;
}

export interface ChatError {
  error: string;
  threadId?: string;
}

export interface HistoryUpdate {
  conversations: unknown[];
}
