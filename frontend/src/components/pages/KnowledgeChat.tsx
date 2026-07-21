'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  AutoAwesome as AssistantIcon,
  MenuBook as SourceIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { knowledgeService } from '@/services/knowledgeService';
import { Citation, KnowledgeAskResponse } from '@/types/knowledge';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  route?: string;
  iterations?: number;
  error?: boolean;
}

const EXAMPLE_QUESTIONS = [
  'How does a mezzanine bond accrue interest?',
  'What is the difference between CAPM and APT?',
  'How does diversification reduce portfolio risk?',
];

const TRUST_COLOR: Record<
  string,
  'success' | 'info' | 'warning' | 'default'
> = {
  authoritative: 'success',
  internal_guidance: 'info',
  working_note: 'warning',
  draft: 'default',
};

function trustColor(level?: string | null) {
  return (level && TRUST_COLOR[level]) || 'default';
}

let idCounter = 0;
const nextId = () => `m${Date.now()}_${idCounter++}`;

const CitationList: React.FC<{ citations: Citation[] }> = ({ citations }) => {
  if (!citations.length) return null;
  return (
    <Box sx={{ mt: 1.5 }}>
      <Stack
        direction="row"
        spacing={0.5}
        alignItems="center"
        sx={{ mb: 0.5, color: 'text.secondary' }}
      >
        <SourceIcon sx={{ fontSize: 16 }} />
        <Typography variant="caption" sx={{ fontWeight: 600 }}>
          Sources ({citations.length})
        </Typography>
      </Stack>
      <Stack spacing={0.75}>
        {citations.map((c, i) => (
          <Paper
            key={`${c.document_id}-${c.chunk_index}-${i}`}
            variant="outlined"
            sx={{ p: 1, display: 'flex', alignItems: 'center', gap: 1 }}
          >
            <Typography variant="caption" sx={{ color: 'text.secondary', minWidth: 20 }}>
              [{i + 1}]
            </Typography>
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Typography variant="body2" noWrap title={c.document_title}>
                {c.document_title}
              </Typography>
              {c.section && (
                <Typography variant="caption" color="text.secondary" noWrap title={c.section}>
                  {c.section}
                </Typography>
              )}
            </Box>
            {c.trust_level && (
              <Chip
                label={c.trust_level.replace(/_/g, ' ')}
                size="small"
                color={trustColor(c.trust_level)}
                variant="outlined"
              />
            )}
          </Paper>
        ))}
      </Stack>
    </Box>
  );
};

const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.role === 'user';
  return (
    <Stack
      direction="row"
      spacing={1.5}
      sx={{ flexDirection: isUser ? 'row-reverse' : 'row', alignItems: 'flex-start' }}
    >
      <Box
        sx={{
          mt: 0.5,
          width: 32,
          height: 32,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          bgcolor: isUser ? 'primary.main' : 'secondary.main',
          color: 'white',
        }}
      >
        {isUser ? <PersonIcon fontSize="small" /> : <AssistantIcon fontSize="small" />}
      </Box>
      <Paper
        elevation={0}
        sx={{
          p: 1.5,
          maxWidth: '80%',
          borderRadius: 2,
          border: 1,
          borderColor: message.error ? 'error.light' : 'divider',
          bgcolor: isUser ? 'grey.100' : 'background.paper',
        }}
      >
        {message.error ? (
          <Alert severity="error" sx={{ py: 0 }}>
            {message.text}
          </Alert>
        ) : (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.text}
          </Typography>
        )}

        {message.role === 'assistant' && message.citations && (
          <CitationList citations={message.citations} />
        )}

        {message.role === 'assistant' && message.route && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', mt: 1 }}
          >
            {message.route === 'complex' ? 'Multi-step retrieval' : 'Direct retrieval'}
            {typeof message.iterations === 'number' && message.iterations > 0
              ? ` · ${message.iterations} refinement${message.iterations > 1 ? 's' : ''}`
              : ''}
          </Typography>
        )}
      </Paper>
    </Stack>
  );
};

const KnowledgeChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: (query: string) => knowledgeService.ask(query),
    onSuccess: (res: KnowledgeAskResponse) => {
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: 'assistant',
          text: res.answer || 'No answer was returned.',
          citations: res.citations,
          route: res.route,
          iterations: res.iterations,
        },
      ]);
    },
    onError: (err: any) => {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        'Something went wrong contacting the knowledge repository.';
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: 'assistant', text: String(detail), error: true },
      ]);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, mutation.isPending]);

  const submit = (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || mutation.isPending) return;
    setMessages((prev) => [...prev, { id: nextId(), role: 'user', text: trimmed }]);
    setInput('');
    mutation.mutate(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Knowledge Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ask a natural-language question about securities, accounting treatments, and operations.
          Answers are grounded in the knowledge repository and cite their sources.
        </Typography>
      </Box>

      <Paper
        variant="outlined"
        ref={scrollRef}
        sx={{ flexGrow: 1, overflowY: 'auto', p: 2, mb: 2, bgcolor: 'grey.50' }}
      >
        {messages.length === 0 && !mutation.isPending ? (
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'text.secondary',
              gap: 2,
            }}
          >
            <AssistantIcon sx={{ fontSize: 48, opacity: 0.4 }} />
            <Typography variant="body1">Ask the knowledge repository a question</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="center" useFlexGap>
              {EXAMPLE_QUESTIONS.map((q) => (
                <Chip
                  key={q}
                  label={q}
                  variant="outlined"
                  onClick={() => submit(q)}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Stack>
          </Box>
        ) : (
          <Stack spacing={2}>
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {mutation.isPending && (
              <Stack direction="row" spacing={1.5} alignItems="center" sx={{ color: 'text.secondary' }}>
                <Box
                  sx={{
                    mt: 0.5,
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'secondary.main',
                    color: 'white',
                  }}
                >
                  <AssistantIcon fontSize="small" />
                </Box>
                <CircularProgress size={18} />
                <Typography variant="body2">Searching the knowledge repository…</Typography>
              </Stack>
            )}
          </Stack>
        )}
      </Paper>

      <Divider sx={{ mb: 1.5 }} />
      <Stack direction="row" spacing={1} alignItems="flex-end">
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder="Ask a question…  (Enter to send, Shift+Enter for a new line)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={mutation.isPending}
        />
        <Tooltip title="Send">
          <span>
            <IconButton
              color="primary"
              onClick={() => submit(input)}
              disabled={mutation.isPending || !input.trim()}
              sx={{ mb: 0.5 }}
            >
              <SendIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Stack>
    </Box>
  );
};

export default KnowledgeChat;
