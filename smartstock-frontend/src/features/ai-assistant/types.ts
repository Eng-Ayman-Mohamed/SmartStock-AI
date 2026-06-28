export type ChatMode = 'nl_query' | 'rag';

export interface Citation {
  document: string;
  page: number;
  document_id?: number | null;
  chunk_text?: string;
}

export interface ChatResponse {
  answer: string;
  sources: Citation[];
  engine: 'nl_query' | 'rag' | 'auto';
  mode: ChatMode;
  conversation_id?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'ai';
  text: string;
  mode?: ChatMode;
  engine?: ChatResponse['engine'];
  sources?: Citation[];
  timestamp: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationDetail extends Conversation {
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    engine: string;
    mode: string;
    sources: Citation[];
    created_at: string;
  }>;
}
