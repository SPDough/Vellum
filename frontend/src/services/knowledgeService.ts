import { api } from './api';
import {
  KnowledgeAskRequest,
  KnowledgeAskResponse,
} from '@/types/knowledge';

export const knowledgeService = {
  /**
   * Ask a natural-language question of the knowledge repository.
   * Runs the agentic knowledge_lookup pipeline and returns a cited answer.
   */
  async ask(
    query: string,
    options?: { filters?: Record<string, string>; minTrust?: string }
  ): Promise<KnowledgeAskResponse> {
    const body: KnowledgeAskRequest = {
      query,
      filters: options?.filters ?? null,
      min_trust: options?.minTrust ?? null,
    };
    // Knowledge agent can loop (retrieve/grade/rewrite) + synthesize; allow more time.
    return api.post<KnowledgeAskResponse>('/rag/knowledge/ask', body, {
      timeout: 120000,
    });
  },
};
