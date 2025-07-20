import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Avatar,
  LinearProgress,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';

import { DataStream } from '@/types/data';
import { dataStreamService } from '@/services/dataStreamService';

interface DataStreamMonitorProps {
  streams: DataStream[];
}

const DataStreamMonitor: React.FC<DataStreamMonitorProps> = ({ streams }) => {
  const handleStreamAction = async (streamId: string, action: 'start' | 'pause' | 'stop') => {
    try {
      switch (action) {
        case 'start':
          await dataStreamService.startStream(streamId);
          break;
        case 'pause':
          await dataStreamService.pauseStream(streamId);
          break;
        case 'stop':
          await dataStreamService.stopStream(streamId);
          break;
      }
      // Could trigger a refresh of the streams list here
    } catch (error) {
      console.error(`Failed to ${action} stream:`, error);
      // Could show error to user
    }
  };
  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatRecordsPerSecond = (rps: number) => {
    if (rps < 1000) return `${rps}/s`;
    if (rps < 1000000) return `${(rps / 1000).toFixed(1)}k/s`;
    return `${(rps / 1000000).toFixed(1)}M/s`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'PAUSED': return 'warning';
      case 'ERROR': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
        Real-time Data Streams
      </Typography>

      {streams.length === 0 ? (
        <Card sx={{ textAlign: 'center', py: 6 }}>
          <CardContent>
            <TimelineIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No active data streams
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Real-time data streams will appear here when configured
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {streams.map((stream) => (
            <Grid item xs={12} md={6} lg={4} key={stream.id}>
              <Card sx={{ borderRadius: 3 }}>
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
                        <TimelineIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                          {stream.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {stream.data_type.replace('_', ' ')}
                        </Typography>
                      </Box>
                    </Box>
                    <Chip
                      label={stream.status}
                      color={getStatusColor(stream.status) as any}
                      size="small"
                      sx={{ textTransform: 'capitalize' }}
                    />
                  </Box>

                  {/* Real-time Metrics */}
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Throughput
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                        {formatRecordsPerSecond(stream.records_per_second)}
                      </Typography>
                    </Box>
                    
                    {/* Visual throughput indicator */}
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((stream.records_per_second / 5000) * 100, 100)}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          bgcolor: stream.records_per_second > 1000 ? 'success.main' : 'primary.main'
                        }
                      }}
                    />
                  </Box>

                  {/* Stats Grid */}
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 2 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Latency
                      </Typography>
                      <Typography variant="body2" sx={{ 
                        fontWeight: 600,
                        color: stream.latency_ms < 100 ? 'success.main' : 
                               stream.latency_ms < 500 ? 'warning.main' : 'error.main'
                      }}>
                        {formatLatency(stream.latency_ms)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Buffer Size
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {stream.buffer_size.toLocaleString()}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Subscribers */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Subscribers ({stream.subscribers.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {stream.subscribers.slice(0, 2).map((subscriber) => (
                        <Chip
                          key={subscriber}
                          label={subscriber.replace('-', ' ')}
                          size="small"
                          variant="outlined"
                          sx={{ 
                            fontSize: '0.7rem',
                            height: 20,
                            textTransform: 'capitalize',
                            borderColor: 'info.main',
                            color: 'info.main'
                          }}
                        />
                      ))}
                      {stream.subscribers.length > 2 && (
                        <Chip
                          label={`+${stream.subscribers.length - 2}`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      )}
                    </Box>
                  </Box>

                  {/* Action Buttons */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      Last update: {new Date(stream.last_update).toLocaleTimeString()}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="View Details">
                        <IconButton size="small">
                          <VisibilityIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </Tooltip>
                      
                      {stream.status === 'ACTIVE' ? (
                        <Tooltip title="Pause Stream">
                          <IconButton 
                            size="small" 
                            color="warning"
                            onClick={() => handleStreamAction(stream.id, 'pause')}
                          >
                            <PauseIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                      ) : (
                        <Tooltip title="Start Stream">
                          <IconButton 
                            size="small" 
                            color="success"
                            onClick={() => handleStreamAction(stream.id, 'start')}
                          >
                            <PlayArrowIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      <Tooltip title="Stop Stream">
                        <IconButton 
                          size="small" 
                          color="error"
                          onClick={() => handleStreamAction(stream.id, 'stop')}
                        >
                          <StopIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default DataStreamMonitor;