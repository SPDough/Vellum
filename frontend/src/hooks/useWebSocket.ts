import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/store';

interface WebSocketMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  sourceId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
  connectionStats: {
    attempts: number;
    lastConnected: Date | null;
    lastDisconnected: Date | null;
  };
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    sourceId,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectInterval = 5000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStats, setConnectionStats] = useState({
    attempts: 0,
    lastConnected: null as Date | null,
    lastDisconnected: null as Date | null,
  });

  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const shouldReconnectRef = useRef(true);

  const { user } = useAuthStore();

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NODE_ENV === 'development' 
      ? 'localhost:8000' 
      : window.location.host;
    
    const baseUrl = `${protocol}//${host}/api/v1/data-sandbox`;
    
    if (sourceId) {
      return `${baseUrl}/sources/${sourceId}/ws?user_id=${user?.id || 'anonymous'}`;
    } else {
      return `${baseUrl}/ws?user_id=${user?.id || 'anonymous'}`;
    }
  }, [sourceId, user?.id]);

  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionStats(prev => ({
          ...prev,
          attempts: prev.attempts + 1,
          lastConnected: new Date(),
        }));
        
        reconnectCountRef.current = 0;
        onConnect?.();
        
        // Send initial ping
        ws.send(JSON.stringify({ type: 'ping' }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionStats(prev => ({
          ...prev,
          lastDisconnected: new Date(),
        }));
        
        websocketRef.current = null;
        onDisconnect?.();

        // Attempt to reconnect if connection was not closed manually
        if (shouldReconnectRef.current && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      websocketRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [getWebSocketUrl, onConnect, onDisconnect, onError, onMessage, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message);
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const heartbeatInterval = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 30000); // Send ping every 30 seconds

    return () => {
      clearInterval(heartbeatInterval);
    };
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    connectionStats,
  };
};

// Hook for subscribing to specific data source updates
export const useDataSourceWebSocket = (sourceId: string, onDataUpdate?: (data: any) => void) => {
  const [latestData, setLatestData] = useState<any>(null);
  const [updateCount, setUpdateCount] = useState(0);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'data_update' && message.source_id === sourceId) {
      setLatestData(message.data);
      setUpdateCount(prev => prev + 1);
      onDataUpdate?.(message.data);
    }
  }, [sourceId, onDataUpdate]);

  const websocket = useWebSocket({
    sourceId,
    onMessage: handleMessage,
  });

  return {
    ...websocket,
    latestData,
    updateCount,
  };
};

// Hook for global system updates
export const useSystemWebSocket = () => {
  const [workflowUpdates, setWorkflowUpdates] = useState<any[]>([]);
  const [mcpUpdates, setMcpUpdates] = useState<any[]>([]);
  const [agentUpdates, setAgentUpdates] = useState<any[]>([]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'workflow_update':
        setWorkflowUpdates(prev => [message, ...prev.slice(0, 49)]); // Keep last 50
        break;
      case 'mcp_stream_update':
        setMcpUpdates(prev => [message, ...prev.slice(0, 49)]);
        break;
      case 'agent_result_update':
        setAgentUpdates(prev => [message, ...prev.slice(0, 49)]);
        break;
    }
  }, []);

  const websocket = useWebSocket({
    onMessage: handleMessage,
  });

  return {
    ...websocket,
    workflowUpdates,
    mcpUpdates,
    agentUpdates,
  };
};