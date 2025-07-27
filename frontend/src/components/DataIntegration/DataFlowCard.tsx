import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  Avatar,
  LinearProgress,
  Button,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  AccountTree as AccountTreeIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';

import { DataFlow, DataFlowStatus } from '@/types/data';

interface DataFlowCardProps {
  flow: DataFlow;
  onStart?: (flow: DataFlow) => void;
  onPause?: (flow: DataFlow) => void;
  onView?: (flow: DataFlow) => void;
}

const DataFlowCard: React.FC<DataFlowCardProps> = ({
  flow,
  onStart,
  onPause,
  onView,
}) => {
  const getStatusIcon = () => {
    switch (flow.status) {
      case DataFlowStatus.ACTIVE:
        return <PlayArrowIcon sx={{ color: 'success.main' }} />;
      case DataFlowStatus.PAUSED:
        return <PauseIcon sx={{ color: 'warning.main' }} />;
      case DataFlowStatus.ERROR:
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      case DataFlowStatus.RUNNING:
        return <TimelineIcon sx={{ color: 'info.main' }} />;
      default:
        return <CheckCircleIcon sx={{ color: 'grey.500' }} />;
    }
  };

  const getStatusColor = () => {
    switch (flow.status) {
      case DataFlowStatus.ACTIVE: return 'success';
      case DataFlowStatus.PAUSED: return 'warning';
      case DataFlowStatus.ERROR: return 'error';
      case DataFlowStatus.RUNNING: return 'info';
      default: return 'default';
    }
  };

  const formatNextRun = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffMs < 0) return 'Overdue';
    if (diffHours < 1) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h ${diffMins}m`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ${diffHours % 24}h`;
  };

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const successRate = (flow.metrics.records_success / flow.metrics.records_processed) * 100;

  return (
    <Card 
      sx={{ 
        borderRadius: 3,
        border: flow.status === DataFlowStatus.ACTIVE ? 2 : 1,
        borderColor: flow.status === DataFlowStatus.ACTIVE ? 'success.main' : 'divider',
        '&:hover': {
          boxShadow: (theme) => theme.shadows[4],
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out'
        }
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar sx={{ 
              width: 40, 
              height: 40, 
              bgcolor: 'primary.light',
              color: 'primary.dark'
            }}>
              <AccountTreeIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                {flow.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {flow.data_types.join(', ')}
              </Typography>
            </Box>
          </Box>
          <Chip
            icon={getStatusIcon()}
            label={flow.status}
            color={getStatusColor() as any}
            size="small"
            sx={{ textTransform: 'capitalize' }}
          />
        </Box>

        {/* Description */}
        {flow.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.4 }}>
            {flow.description}
          </Typography>
        )}

        {/* Success Rate Progress */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Success Rate
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {successRate.toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={successRate}
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 3,
                bgcolor: successRate > 95 ? 'success.main' : 
                         successRate > 90 ? 'warning.main' : 'error.main'
              }
            }}
          />
        </Box>

        {/* Metrics Grid */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Records Processed
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {flow.metrics.records_processed.toLocaleString()}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Processing Time
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {formatDuration(flow.metrics.processing_time_ms)}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Data Quality
            </Typography>
            <Typography variant="body2" sx={{ 
              fontWeight: 600, 
              color: flow.metrics.data_quality_score > 95 ? 'success.main' : 'warning.main'
            }}>
              {flow.metrics.data_quality_score.toFixed(1)}%
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Next Run
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {formatNextRun(flow.next_run)}
            </Typography>
          </Box>
        </Box>

        {/* Source & Target Systems */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Sources:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {flow.source_servers.slice(0, 2).map((source) => (
                <Chip
                  key={source}
                  label={source.split('-')[0]}
                  size="small"
                  variant="outlined"
                  sx={{ 
                    fontSize: '0.7rem',
                    height: 20,
                    textTransform: 'capitalize',
                    borderColor: 'primary.main',
                    color: 'primary.main'
                  }}
                />
              ))}
              {flow.source_servers.length > 2 && (
                <Chip
                  label={`+${flow.source_servers.length - 2}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Targets:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {flow.target_systems.map((target) => (
                <Chip
                  key={target}
                  label={target.replace('-', ' ')}
                  size="small"
                  variant="filled"
                  sx={{ 
                    fontSize: '0.7rem',
                    height: 20,
                    textTransform: 'capitalize',
                    bgcolor: 'secondary.light',
                    color: 'secondary.dark'
                  }}
                />
              ))}
            </Box>
          </Box>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => onView?.(flow)}
            sx={{ borderRadius: 2 }}
          >
            View Details
          </Button>
          {flow.status === DataFlowStatus.ACTIVE ? (
            <Button
              size="small"
              variant="contained"
              startIcon={<PauseIcon />}
              onClick={() => onPause?.(flow)}
              sx={{ borderRadius: 2 }}
            >
              Pause
            </Button>
          ) : (
            <Button
              size="small"
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => onStart?.(flow)}
              sx={{ borderRadius: 2 }}
            >
              Start
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default DataFlowCard;
