import React from 'react';
import { Box, IconButton, Tooltip } from '@mui/material';
import { Add, ZoomIn, ZoomOut, FitScreen } from '@mui/icons-material';

interface WorkflowToolbarProps {
  onAddNode?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onFitScreen?: () => void;
}

const WorkflowToolbar: React.FC<WorkflowToolbarProps> = ({
  onAddNode,
  onZoomIn,
  onZoomOut,
  onFitScreen
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        gap: 1,
        p: 1,
        backgroundColor: 'background.paper',
        borderRadius: 1,
        boxShadow: 1
      }}
    >
      <Tooltip title="Add Node">
        <IconButton onClick={onAddNode} size="small">
          <Add />
        </IconButton>
      </Tooltip>
      
      <Tooltip title="Zoom In">
        <IconButton onClick={onZoomIn} size="small">
          <ZoomIn />
        </IconButton>
      </Tooltip>
      
      <Tooltip title="Zoom Out">
        <IconButton onClick={onZoomOut} size="small">
          <ZoomOut />
        </IconButton>
      </Tooltip>
      
      <Tooltip title="Fit Screen">
        <IconButton onClick={onFitScreen} size="small">
          <FitScreen />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default WorkflowToolbar;
