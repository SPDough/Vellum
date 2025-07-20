import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Divider,
  IconButton,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
} from '@mui/material';
import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { Node } from 'reactflow';
import { WorkflowNodeType } from '@/types/workflow';

interface NodePropertiesPanelProps {
  node: Node;
  onUpdateNode: (node: Node) => void;
  onClose: () => void;
}

const PANEL_WIDTH = 400;

// Mock MCP servers for selection
const mockMCPServers = [
  { id: 'state-street-001', name: 'State Street Global Services' },
  { id: 'bloomberg-mktdata', name: 'Bloomberg Market Data' },
  { id: 'bny-mellon-cust', name: 'BNY Mellon Custody' },
];

const NodePropertiesPanel: React.FC<NodePropertiesPanelProps> = ({
  node,
  onUpdateNode,
  onClose,
}) => {
  const [localNode, setLocalNode] = useState<Node>(node);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalNode(node);
    setHasChanges(false);
  }, [node]);

  const handlePropertyChange = (key: string, value: any) => {
    const updatedNode = {
      ...localNode,
      data: {
        ...localNode.data,
        config: {
          ...localNode.data.config,
          [key]: value,
        },
      },
    };
    setLocalNode(updatedNode);
    setHasChanges(true);
  };

  const handleBasicPropertyChange = (key: string, value: any) => {
    const updatedNode = {
      ...localNode,
      data: {
        ...localNode.data,
        [key]: value,
      },
    };
    setLocalNode(updatedNode);
    setHasChanges(true);
  };

  const handleSave = () => {
    onUpdateNode(localNode);
    setHasChanges(false);
  };

  const handleDelete = () => {
    // TODO: Implement node deletion
    console.log('Delete node:', localNode.id);
    onClose();
  };

  const renderMCPCallProperties = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControl fullWidth>
        <InputLabel>MCP Server</InputLabel>
        <Select
          value={localNode.data.config?.mcp_server_id || ''}
          onChange={(e) => handlePropertyChange('mcp_server_id', e.target.value)}
          label="MCP Server"
        >
          {mockMCPServers.map((server) => (
            <MenuItem key={server.id} value={server.id}>
              {server.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <TextField
        fullWidth
        label="Endpoint/Tool Name"
        value={localNode.data.config?.endpoint_id || ''}
        onChange={(e) => handlePropertyChange('endpoint_id', e.target.value)}
        helperText="The specific tool to call on the MCP server"
      />

      <TextField
        fullWidth
        multiline
        rows={3}
        label="Parameters (JSON)"
        value={localNode.data.config?.parameters ? JSON.stringify(localNode.data.config.parameters, null, 2) : '{}'}
        onChange={(e) => {
          try {
            const params = JSON.parse(e.target.value);
            handlePropertyChange('parameters', params);
          } catch (error) {
            // Invalid JSON, don't update
          }
        }}
        helperText="Parameters to pass to the MCP tool"
      />
    </Box>
  );

  const renderTransformProperties = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControl fullWidth>
        <InputLabel>Transform Type</InputLabel>
        <Select
          value={localNode.data.config?.transform_type || 'javascript'}
          onChange={(e) => handlePropertyChange('transform_type', e.target.value)}
          label="Transform Type"
        >
          <MenuItem value="javascript">JavaScript</MenuItem>
          <MenuItem value="python">Python</MenuItem>
          <MenuItem value="sql">SQL</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        multiline
        rows={6}
        label="Transformation Code"
        value={localNode.data.config?.transformation_code || ''}
        onChange={(e) => handlePropertyChange('transformation_code', e.target.value)}
        helperText="Code to transform the input data"
        placeholder="// Example: transform data here
return data.map(item => ({
  ...item,
  processed: true
}));"
      />
    </Box>
  );

  const renderFilterProperties = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        fullWidth
        label="Filter Expression"
        value={localNode.data.config?.filter_expression || ''}
        onChange={(e) => handlePropertyChange('filter_expression', e.target.value)}
        helperText="Boolean expression to filter data"
        placeholder="item.value > 100 && item.status === 'active'"
      />

      <FormControlLabel
        control={
          <Switch
            checked={localNode.data.config?.case_sensitive || false}
            onChange={(e) => handlePropertyChange('case_sensitive', e.target.checked)}
          />
        }
        label="Case Sensitive"
      />
    </Box>
  );

  const renderDataSinkProperties = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControl fullWidth>
        <InputLabel>Destination Type</InputLabel>
        <Select
          value={localNode.data.config?.destination_type || 'database'}
          onChange={(e) => handlePropertyChange('destination_type', e.target.value)}
          label="Destination Type"
        >
          <MenuItem value="database">Database</MenuItem>
          <MenuItem value="file">File</MenuItem>
          <MenuItem value="api">API Endpoint</MenuItem>
          <MenuItem value="message_queue">Message Queue</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        label="Connection String"
        value={localNode.data.config?.connection_string || ''}
        onChange={(e) => handlePropertyChange('connection_string', e.target.value)}
        helperText="Connection details for the destination"
      />

      <TextField
        fullWidth
        label="Table/Path"
        value={localNode.data.config?.table_name || ''}
        onChange={(e) => handlePropertyChange('table_name', e.target.value)}
        helperText="Target table name or file path"
      />
    </Box>
  );

  const renderConditionProperties = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        fullWidth
        label="Condition Expression"
        value={localNode.data.config?.condition_expression || ''}
        onChange={(e) => handlePropertyChange('condition_expression', e.target.value)}
        helperText="Boolean expression for the condition"
        placeholder="data.length > 0 && data.status === 'valid'"
      />

      <Alert severity="info" sx={{ mt: 1 }}>
        This node will route data to the "true" output if the condition is met, 
        otherwise to the "false" output.
      </Alert>
    </Box>
  );

  const renderNodeSpecificProperties = () => {
    switch (localNode.data.nodeType) {
      case WorkflowNodeType.MCP_CALL:
        return renderMCPCallProperties();
      case WorkflowNodeType.TRANSFORM:
        return renderTransformProperties();
      case WorkflowNodeType.FILTER:
        return renderFilterProperties();
      case WorkflowNodeType.DATA_SINK:
        return renderDataSinkProperties();
      case WorkflowNodeType.CONDITION:
        return renderConditionProperties();
      default:
        return (
          <Alert severity="info">
            No specific configuration options for this node type.
          </Alert>
        );
    }
  };

  return (
    <Drawer
      anchor="right"
      open={true}
      onClose={onClose}
      variant="persistent"
      sx={{
        '& .MuiDrawer-paper': {
          width: PANEL_WIDTH,
          position: 'relative',
          height: '100%',
          borderLeft: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        },
      }}
    >
      <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Node Properties
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Basic Properties */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
            Basic Settings
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Node Name"
              value={localNode.data.label || ''}
              onChange={(e) => handleBasicPropertyChange('label', e.target.value)}
            />

            <TextField
              fullWidth
              multiline
              rows={2}
              label="Description"
              value={localNode.data.description || ''}
              onChange={(e) => handleBasicPropertyChange('description', e.target.value)}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Type:
              </Typography>
              <Chip 
                label={localNode.data.nodeType?.replace('_', ' ')} 
                size="small" 
                color="primary"
                variant="outlined"
              />
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Node-specific Properties */}
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
            Node Configuration
          </Typography>
          {renderNodeSpecificProperties()}
        </Box>

        {/* Error Handling */}
        <Accordion sx={{ mt: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Error Handling
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                type="number"
                label="Retry Attempts"
                value={localNode.data.config?.retry_attempts || 3}
                onChange={(e) => handlePropertyChange('retry_attempts', parseInt(e.target.value))}
              />

              <TextField
                fullWidth
                type="number"
                label="Timeout (seconds)"
                value={localNode.data.config?.timeout_seconds || 30}
                onChange={(e) => handlePropertyChange('timeout_seconds', parseInt(e.target.value))}
              />

              <FormControl fullWidth>
                <InputLabel>On Error</InputLabel>
                <Select
                  value={localNode.data.config?.on_error || 'FAIL'}
                  onChange={(e) => handlePropertyChange('on_error', e.target.value)}
                  label="On Error"
                >
                  <MenuItem value="FAIL">Fail Workflow</MenuItem>
                  <MenuItem value="CONTINUE">Continue</MenuItem>
                  <MenuItem value="RETRY">Retry</MenuItem>
                  <MenuItem value="SKIP">Skip Node</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 1, mt: 3 }}>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={!hasChanges}
            sx={{ flex: 1 }}
          >
            Save Changes
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
          >
            Delete
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
};

export default NodePropertiesPanel;