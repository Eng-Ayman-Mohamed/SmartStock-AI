export type ChatMode = 'auto' | 'nl_query' | 'rag';

export interface Citation {
  document: string;
  page: number;
  chunk_text?: string;
}

export interface ChatResponse {
  answer: string;
  sources: Citation[];
  engine: 'nl_query' | 'rag' | 'auto';
  mode: ChatMode;
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
