import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  IconButton,
  Paper,
  Avatar,
  Chip,
  Button,
  Menu,
  MenuItem,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  Clear as ClearIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import { 
  agentService,
  Agent,
  AgentConversation,
  AgentMessage,
  AgentChatRequest,
} from '@/services/agentService';

interface AgentChatInterfaceProps {
  agent: Agent;
  conversationId?: string;
  onConversationCreate?: (conversation: AgentConversation) => void;
}

const AgentChatInterface: React.FC<AgentChatInterfaceProps> = ({ 
  agent, 
  conversationId,
  onConversationCreate 
}) => {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Fetch or create conversation
  const { data: conversation, isLoading: conversationLoading } = useQuery(
    ['agent-conversation', agent.id, conversationId],
    async () => {
      if (conversationId) {
        return agentService.getConversation(agent.id, conversationId);
      } else {
        const newConversation = await agentService.createConversation(agent.id, 'New Chat');
        onConversationCreate?.(newConversation);
        return newConversation;
      }
    },
    {
      enabled: !!agent.id,
    }
  );

  // Send message mutation
  const sendMessageMutation = useMutation(
    (request: AgentChatRequest) => 
      agentService.chatWithAgent(agent.id, conversation!.id, request),
    {
      onMutate: () => {
        setIsTyping(true);
      },
      onSuccess: () => {
        queryClient.invalidateQueries(['agent-conversation', agent.id, conversation?.id]);
        setMessage('');
        setIsTyping(false);
      },
      onError: () => {
        setIsTyping(false);
      },
    }
  );

  // Clear conversation mutation
  const clearConversationMutation = useMutation(
    () => agentService.deleteConversation(agent.id, conversation!.id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['agent-conversation', agent.id]);
      },
    }
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages]);

  const handleSendMessage = () => {
    if (!message.trim() || !conversation) return;

    const chatRequest: AgentChatRequest = {
      message: message.trim(),
      tools_enabled: true,
    };

    sendMessageMutation.mutate(chatRequest);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClearConversation = () => {
    clearConversationMutation.mutate();
    handleMenuClose();
  };

  const handleExportConversation = () => {
    if (!conversation) return;

    const exportData = {
      agent: agent.name,
      conversation_id: conversation.id,
      title: conversation.title,
      messages: conversation.messages,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${conversation.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    handleMenuClose();
  };

  if (conversationLoading) {
    return (
      <Card sx={{ height: 600, borderRadius: 3 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading conversation...</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!conversation) {
    return (
      <Card sx={{ height: 600, borderRadius: 3 }}>
        <CardContent>
          <Alert severity="error">Failed to load conversation</Alert>
        </CardContent>
      </Card>
    );
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <Card sx={{ height: 600, borderRadius: 3, display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Box sx={{ 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <BotIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {agent.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip 
                label={agent.status} 
                size="small" 
                color={agent.status === 'ACTIVE' ? 'success' : 'default'}
              />
              <Typography variant="caption" color="text.secondary">
                {agent.agent_type}
              </Typography>
            </Box>
          </Box>
        </Box>
        
        <IconButton onClick={handleMenuOpen}>
          <MoreVertIcon />
        </IconButton>
      </Box>

      {/* Messages Area */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'auto', 
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2
      }}>
        {conversation.messages.length === 0 ? (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%',
            flexDirection: 'column',
            gap: 2
          }}>
            <BotIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
            <Typography variant="body1" color="text.secondary" textAlign="center">
              Start a conversation with {agent.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              {agent.description}
            </Typography>
          </Box>
        ) : (
          conversation.messages.map((msg) => (
            <Box
              key={msg.id}
              sx={{
                display: 'flex',
                gap: 2,
                alignItems: 'flex-start',
                flexDirection: msg.role === 'USER' ? 'row-reverse' : 'row',
              }}
            >
              <Avatar sx={{ 
                bgcolor: msg.role === 'USER' ? 'secondary.main' : 'primary.main',
                width: 32,
                height: 32
              }}>
                {msg.role === 'USER' ? <PersonIcon /> : <BotIcon />}
              </Avatar>
              
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: msg.role === 'USER' ? 'primary.light' : 'background.paper',
                  color: msg.role === 'USER' ? 'primary.contrastText' : 'text.primary',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </Typography>
                
                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Tools used:
                    </Typography>
                    {msg.tool_calls.map((tool, index) => (
                      <Chip
                        key={index}
                        label={tool.tool_name}
                        size="small"
                        sx={{ ml: 0.5, mt: 0.5 }}
                      />
                    ))}
                  </Box>
                )}
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {formatTime(msg.timestamp)}
                  {msg.tokens_used > 0 && ` • ${msg.tokens_used} tokens`}
                  {msg.cost_usd > 0 && ` • $${msg.cost_usd.toFixed(4)}`}
                </Typography>
              </Paper>
            </Box>
          ))
        )}
        
        {isTyping && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
              <BotIcon />
            </Avatar>
            <Paper sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="body2" color="text.secondary">
                {agent.name} is typing...
              </Typography>
            </Paper>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder={`Message ${agent.name}...`}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={sendMessageMutation.isLoading}
            variant="outlined"
            size="small"
          />
          <IconButton
            onClick={handleSendMessage}
            disabled={!message.trim() || sendMessageMutation.isLoading}
            color="primary"
            sx={{ mb: 0.5 }}
          >
            {sendMessageMutation.isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          </IconButton>
        </Box>
      </Box>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          queryClient.invalidateQueries(['agent-conversation', agent.id, conversation.id]);
          handleMenuClose();
        }}>
          <RefreshIcon sx={{ mr: 1 }} />
          Refresh
        </MenuItem>
        <MenuItem onClick={handleExportConversation}>
          <DownloadIcon sx={{ mr: 1 }} />
          Export Conversation
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleClearConversation} sx={{ color: 'error.main' }}>
          <ClearIcon sx={{ mr: 1 }} />
          Clear Conversation
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default AgentChatInterface;