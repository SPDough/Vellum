// Types for the knowledge-repository chat (backend: POST /api/v1/rag/knowledge/ask)

export interface KnowledgeAskRequest {
  query: string;
  filters?: Record<string, string> | null;
  min_trust?: string | null;
}

export interface Citation {
  document_id: string;
  document_title: string;
  section?: string | null;
  trust_level?: string | null;
  chunk_index: number;
}

export interface KnowledgeAskResponse {
  query: string;
  answer: string;
  route: string; // "simple" | "complex"
  iterations: number;
  citations: Citation[];
}
