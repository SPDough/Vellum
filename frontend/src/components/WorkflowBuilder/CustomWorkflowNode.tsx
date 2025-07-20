import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  IconButton,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  PlayArrow as PlayArrowIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { Handle, Position, NodeProps } from 'reactflow';
import { WorkflowNodeType } from '@/types/workflow';

interface CustomNodeData {
  label: string;
  nodeType: WorkflowNodeType;
  icon: React.ReactNode;
  description?: string;
  config?: Record<string, any>;
  status?: 'idle' | 'running' | 'success' | 'error';
}

const CustomWorkflowNode: React.FC<NodeProps<CustomNodeData>> = ({ 
  data, 
  selected, 
  id 
}) => {
  const getStatusColor = () => {
    switch (data.status) {
      case 'running': return 'info.main';
      case 'success': return 'success.main';
      case 'error': return 'error.main';
      default: return 'grey.400';
    }
  };

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running': return <PlayArrowIcon sx={{ fontSize: 16 }} />;
      case 'success': return <CheckCircleIcon sx={{ fontSize: 16 }} />;
      case 'error': return <ErrorIcon sx={{ fontSize: 16 }} />;
      default: return null;
    }
  };

  const getNodeColor = () => {
    switch (data.nodeType) {
      case WorkflowNodeType.MCP_CALL:
      case WorkflowNodeType.DATA_SOURCE:
        return '#8b5cf6'; // Purple for data sources
      case WorkflowNodeType.TRANSFORM:
      case WorkflowNodeType.FILTER:
      case WorkflowNodeType.AGGREGATE:
        return '#06b6d4'; // Cyan for processing
      case WorkflowNodeType.DATA_SINK:
      case WorkflowNodeType.EMAIL:
      case WorkflowNodeType.WEBHOOK:
        return '#10b981'; // Green for outputs
      case WorkflowNodeType.CONDITION:
      case WorkflowNodeType.LOOP:
        return '#f59e0b'; // Amber for logic
      default:
        return '#6b7280'; // Gray for others
    }
  };

  const nodeColor = getNodeColor();
  const hasInputs = ![
    WorkflowNodeType.START,
    WorkflowNodeType.DATA_SOURCE,
    WorkflowNodeType.MCP_CALL
  ].includes(data.nodeType);
  
  const hasOutputs = ![
    WorkflowNodeType.END,
    WorkflowNodeType.DATA_SINK,
    WorkflowNodeType.EMAIL,
    WorkflowNodeType.WEBHOOK
  ].includes(data.nodeType);

  return (
    <>
      {/* Input Handle */}
      {hasInputs && (
        <Handle
          type="target"
          position={Position.Left}
          id="input"
          style={{
            width: 12,
            height: 12,
            backgroundColor: nodeColor,
            border: '2px solid white',
          }}
        />
      )}

      {/* Node Body */}
      <Paper
        elevation={selected ? 8 : 2}
        sx={{
          minWidth: 200,
          maxWidth: 250,
          border: selected ? 2 : 1,
          borderColor: selected ? 'primary.main' : 'divider',
          borderRadius: 2,
          overflow: 'hidden',
          bgcolor: 'background.paper',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: (theme) => theme.shadows[4],
          }
        }}
      >
        {/* Header */}
        <Box
          sx={{
            bgcolor: nodeColor,
            color: 'white',
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(255,255,255,0.2)' }}>
            {React.cloneElement(data.icon as React.ReactElement, { 
              sx: { fontSize: 20, color: 'white' } 
            })}
          </Avatar>
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                color: 'white',
                lineHeight: 1.2,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {data.label}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255,255,255,0.8)',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                fontWeight: 500,
              }}
            >
              {data.nodeType.replace('_', ' ')}
            </Typography>
          </Box>
          {data.status && (
            <Box sx={{ color: 'white' }}>
              {getStatusIcon()}
            </Box>
          )}
        </Box>

        {/* Content */}
        <Box sx={{ p: 1.5 }}>
          {data.description && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{
                display: 'block',
                lineHeight: 1.3,
                mb: 1,
              }}
            >
              {data.description}
            </Typography>
          )}

          {/* Configuration Summary */}
          {data.config && Object.keys(data.config).length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                Configuration:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(data.config).slice(0, 2).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}: ${String(value).substring(0, 10)}${String(value).length > 10 ? '...' : ''}`}
                    size="small"
                    variant="outlined"
                    sx={{
                      fontSize: '0.6rem',
                      height: 20,
                      '& .MuiChip-label': { px: 1 }
                    }}
                  />
                ))}
                {Object.keys(data.config).length > 2 && (
                  <Chip
                    label={`+${Object.keys(data.config).length - 2}`}
                    size="small"
                    variant="outlined"
                    sx={{
                      fontSize: '0.6rem',
                      height: 20,
                      '& .MuiChip-label': { px: 1 }
                    }}
                  />
                )}
              </Box>
            </Box>
          )}

          {/* MCP Server specific info */}
          {data.nodeType === WorkflowNodeType.MCP_CALL && data.config?.mcp_server_id && (
            <Box sx={{ mt: 1 }}>
              <Chip
                label={`Server: ${data.config.mcp_server_id}`}
                size="small"
                color="primary"
                variant="filled"
                sx={{
                  fontSize: '0.7rem',
                  height: 22,
                }}
              />
            </Box>
          )}
        </Box>
      </Paper>

      {/* Output Handle */}
      {hasOutputs && (
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          style={{
            width: 12,
            height: 12,
            backgroundColor: nodeColor,
            border: '2px solid white',
          }}
        />
      )}

      {/* Conditional outputs for decision nodes */}
      {data.nodeType === WorkflowNodeType.CONDITION && (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            style={{
              width: 12,
              height: 12,
              backgroundColor: '#10b981',
              border: '2px solid white',
              left: '25%',
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            style={{
              width: 12,
              height: 12,
              backgroundColor: '#ef4444',
              border: '2px solid white',
              left: '75%',
            }}
          />
        </>
      )}
    </>
  );
};

export default CustomWorkflowNode;