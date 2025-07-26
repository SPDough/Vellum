import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Toolbar,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fab,
  Chip,
  AppBar,
} from '@mui/material';
import {
  Save as SaveIcon,
  PlayArrow as PlayIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  Storage as StorageIcon,
  Transform as TransformIcon,
  Router as RouterIcon,
  Notifications as NotificationsIcon,
  AccountTree as AccountTreeIcon,
  Api as ApiIcon,
} from '@mui/icons-material';
import ReactFlow, {
  Node,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  ReactFlowProvider,
  Panel,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { WorkflowNodeType } from '@/types/workflow';
import { workflowService } from '@/services/workflowService';
import CustomWorkflowNode from '@/components/WorkflowBuilder/CustomWorkflowNode';
import NodePropertiesPanel from '@/components/WorkflowBuilder/NodePropertiesPanel';

const nodeTypes = {
  custom: CustomWorkflowNode,
};

const SIDEBAR_WIDTH = 300;

interface NodeTemplate {
  type: WorkflowNodeType;
  label: string;
  icon: React.ReactNode;
  description: string;
  category: string;
}

const nodeTemplates: NodeTemplate[] = [
  // Data Sources
  {
    type: WorkflowNodeType.MCP_CALL,
    label: 'MCP Server Call',
    icon: <ApiIcon />,
    description: 'Call a tool on an MCP server',
    category: 'Data Sources'
  },
  {
    type: WorkflowNodeType.DATA_SOURCE,
    label: 'Data Source',
    icon: <StorageIcon />,
    description: 'External data source',
    category: 'Data Sources'
  },
  // Processing
  {
    type: WorkflowNodeType.TRANSFORM,
    label: 'Transform',
    icon: <TransformIcon />,
    description: 'Transform data using custom logic',
    category: 'Processing'
  },
  {
    type: WorkflowNodeType.FILTER,
    label: 'Filter',
    icon: <RouterIcon />,
    description: 'Filter data based on conditions',
    category: 'Processing'
  },
  {
    type: WorkflowNodeType.AGGREGATE,
    label: 'Aggregate',
    icon: <AccountTreeIcon />,
    description: 'Aggregate data by grouping',
    category: 'Processing'
  },
  // Output
  {
    type: WorkflowNodeType.DATA_SINK,
    label: 'Data Sink',
    icon: <StorageIcon />,
    description: 'Store data to destination',
    category: 'Output'
  },
  {
    type: WorkflowNodeType.EMAIL,
    label: 'Email',
    icon: <NotificationsIcon />,
    description: 'Send email notification',
    category: 'Output'
  },
];

const WorkflowBuilder: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type || !reactFlowInstance || !reactFlowBounds) {
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const template = nodeTemplates.find(t => t.type === type);
      
      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type: 'custom',
        position,
        data: {
          label: template?.label || type,
          nodeType: type,
          icon: template?.icon,
          description: template?.description,
          config: {},
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleSaveWorkflow = async () => {
    try {
      const workflowData = {
        name: workflowName,
        description: workflowDescription,
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.data.nodeType,
          name: node.data.label,
          description: node.data.description,
          position: node.position,
          config: node.data.config || {},
          inputs: [],
          outputs: [],
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source_node_id: edge.source,
          source_port_id: edge.sourceHandle || 'default',
          target_node_id: edge.target,
          target_port_id: edge.targetHandle || 'default',
        })),
        triggers: [],
        execution_settings: {
          max_concurrent_executions: 1,
          execution_timeout_minutes: 60,
          retry_policy: {
            max_attempts: 3,
            backoff_strategy: 'EXPONENTIAL',
            delay_seconds: 30,
          },
          notification_settings: {
            on_success: false,
            on_failure: true,
            on_long_running: false,
            recipients: [],
            channels: [],
          }
        }
      };

      const savedWorkflow = await workflowService.createWorkflow(workflowData);
      console.log('Workflow saved successfully:', savedWorkflow);
      setCurrentWorkflowId(savedWorkflow.id);
      setWorkflowName(savedWorkflow.name);
      setSaveDialogOpen(false);
      
      // Could show success message
    } catch (error) {
      console.error('Failed to save workflow:', error);
      // Could show error message to user
    }
  };

  const handleTestRun = async () => {
    if (!currentWorkflowId) {
      // Need to save workflow first
      await handleSaveWorkflow();
      if (!currentWorkflowId) return;
    }

    setIsExecuting(true);
    
    try {
      const execution = await workflowService.executeWorkflow(currentWorkflowId, {
        input_data: { test: true },
        trigger_type: 'manual'
      });
      
      console.log('Workflow execution started:', execution);
      
      // Could poll for execution status or show execution details
      // For now, just log success
      
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      // Could show error message to user
    } finally {
      setIsExecuting(false);
    }
  };

  const nodeCategories = Array.from(new Set(nodeTemplates.map(t => t.category)));

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Toolbar */}
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
            {workflowName}
          </Typography>
          <Chip 
            label="Draft" 
            size="small" 
            color="warning" 
            sx={{ textTransform: 'uppercase', fontWeight: 600 }}
          />
          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            onClick={() => setSaveDialogOpen(true)}
            sx={{ borderRadius: 2 }}
          >
            Save
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={handleTestRun}
            disabled={isExecuting}
            sx={{ borderRadius: 2 }}
          >
            {isExecuting ? 'Running...' : 'Test Run'}
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', flex: 1 }}>
        {/* Node Palette Sidebar */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={sidebarOpen}
          sx={{
            width: sidebarOpen ? SIDEBAR_WIDTH : 0,
            '& .MuiDrawer-paper': {
              width: SIDEBAR_WIDTH,
              position: 'relative',
              borderRight: 1,
              borderColor: 'divider',
              bgcolor: 'background.sidebar',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Node Library
            </Typography>
            
            {nodeCategories.map((category) => (
              <Accordion key={category} defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {category}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ p: 0 }}>
                  <List dense>
                    {nodeTemplates
                      .filter(template => template.category === category)
                      .map((template) => (
                        <ListItem
                          key={template.type}
                          draggable
                          onDragStart={(event) => {
                            event.dataTransfer.setData('application/reactflow', template.type);
                            event.dataTransfer.effectAllowed = 'move';
                          }}
                          sx={{
                            cursor: 'grab',
                            border: 1,
                            borderColor: 'divider',
                            borderRadius: 2,
                            mb: 1,
                            bgcolor: 'background.paper',
                            '&:hover': {
                              bgcolor: 'action.hover',
                              borderColor: 'primary.main',
                            },
                            '&:active': {
                              cursor: 'grabbing',
                            }
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            {template.icon}
                          </ListItemIcon>
                          <ListItemText
                            primary={template.label}
                            secondary={template.description}
                            primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </Drawer>

        {/* Main Canvas */}
        <Box 
          ref={reactFlowWrapper}
          sx={{ 
            flex: 1, 
            position: 'relative',
            bgcolor: 'grey.50'
          }}
        >
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="#f0f0f0" gap={20} />
              <Controls />
              <MiniMap 
                nodeStrokeWidth={3}
                nodeColor={(node) => {
                  switch (node.data?.nodeType) {
                    case WorkflowNodeType.MCP_CALL: return '#8b5cf6';
                    case WorkflowNodeType.TRANSFORM: return '#06b6d4';
                    case WorkflowNodeType.DATA_SOURCE: return '#10b981';
                    default: return '#6b7280';
                  }
                }}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  border: '1px solid #e5e7eb',
                  borderRadius: 8,
                }}
              />
              
              {/* Custom Panel for Workflow Info */}
              <Panel position="top-right" style={{ margin: 16 }}>
                <Paper sx={{ p: 2, minWidth: 200 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                    Workflow Stats
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Nodes
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {nodes.length}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Connections
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {edges.length}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Panel>
            </ReactFlow>
          </ReactFlowProvider>

          {/* Floating Action Button to toggle sidebar */}
          <Fab
            size="small"
            color="primary"
            sx={{ position: 'absolute', top: 16, left: 16, zIndex: 1000 }}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <SettingsIcon />
          </Fab>
        </Box>

        {/* Properties Panel */}
        {selectedNode && (
          <NodePropertiesPanel
            node={selectedNode}
            onUpdateNode={(updatedNode) => {
              setNodes((nodes) =>
                nodes.map((node) =>
                  node.id === updatedNode.id ? updatedNode : node
                )
              );
            }}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </Box>

      {/* Save Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save Workflow</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Workflow Name"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Description"
            value={workflowDescription}
            onChange={(e) => setWorkflowDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveWorkflow}>
            Save Workflow
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorkflowBuilder;
