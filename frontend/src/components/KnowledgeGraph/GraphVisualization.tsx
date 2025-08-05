import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Toolbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';

import { knowledgeGraphService, GraphVisualizationData, GraphNode, GraphEdge } from '@/services/knowledgeGraphService';

interface GraphVisualizationProps {
  centerEntityId?: string;
  entityTypes?: string[];
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
}

interface D3Node extends GraphNode {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
}

interface D3Link extends Omit<GraphEdge, 'source' | 'target'> {
  source: string | D3Node;
  target: string | D3Node;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  centerEntityId,
  entityTypes,
  height = 600,
  onNodeClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<string[]>(entityTypes || []);
  const [searchEntity, setSearchEntity] = useState(centerEntityId || '');
  const [zoom, setZoom] = useState(1);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Fetch graph data
  const { data: graphData, isLoading, error, refetch } = useQuery<GraphVisualizationData>({
    queryKey: ['graph-visualization', centerEntityId, selectedEntityTypes],
    queryFn: () => knowledgeGraphService.getGraphVisualization({
      center_entity_id: centerEntityId,
      entity_types: selectedEntityTypes.length > 0 ? selectedEntityTypes : undefined,
      depth: 2,
      limit: 100
    }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const availableEntityTypes = [
    'Account', 'Security', 'Trade', 'Position', 'MCPServer', 
    'Workflow', 'DataStream', 'Custodian', 'Portfolio'
  ];

  // Simple force-directed layout simulation (basic implementation)
  useEffect(() => {
    if (!graphData || !svgRef.current) return;

    const svg = svgRef.current;
    const width = svg.clientWidth;
    const height = svg.clientHeight;

    // Clear previous content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }

    // Create SVG groups
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    svg.appendChild(g);

    // Convert data to D3-compatible format
    const nodes: D3Node[] = graphData.nodes.map(node => ({
      ...node,
      x: Math.random() * width,
      y: Math.random() * height,
    }));

    const links: D3Link[] = graphData.edges.map(edge => ({
      ...edge,
      source: edge.source,
      target: edge.target,
    }));

    // Node color mapping
    const getNodeColor = (type: string) => {
      const colors: Record<string, string> = {
        Account: '#8b5cf6',      // Purple
        Security: '#06b6d4',     // Cyan
        Trade: '#10b981',        // Green
        Position: '#f59e0b',     // Amber
        MCPServer: '#ef4444',    // Red
        Workflow: '#8b5a2b',     // Brown
        DataStream: '#6366f1',   // Indigo
        default: '#6b7280'       // Gray
      };
      return colors[type] || colors.default;
    };

    // Create links (edges)
    links.forEach(link => {
      const sourceNode = nodes.find(n => n.id === link.source);
      const targetNode = nodes.find(n => n.id === link.target);
      
      if (sourceNode && targetNode) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourceNode.x?.toString() || '0');
        line.setAttribute('y1', sourceNode.y?.toString() || '0');
        line.setAttribute('x2', targetNode.x?.toString() || '0');
        line.setAttribute('y2', targetNode.y?.toString() || '0');
        line.setAttribute('stroke', '#e5e7eb');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('opacity', '0.6');
        g.appendChild(line);
      }
    });

    // Create nodes
    nodes.forEach(node => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', node.x?.toString() || '0');
      circle.setAttribute('cy', node.y?.toString() || '0');
      circle.setAttribute('r', '12');
      circle.setAttribute('fill', getNodeColor(node.type));
      circle.setAttribute('stroke', '#ffffff');
      circle.setAttribute('stroke-width', '2');
      circle.style.cursor = 'pointer';
      
      circle.addEventListener('click', () => {
        setSelectedNode(node);
        onNodeClick?.(node);
      });

      // Add hover effect
      circle.addEventListener('mouseenter', () => {
        circle.setAttribute('r', '15');
        circle.setAttribute('opacity', '0.8');
      });
      
      circle.addEventListener('mouseleave', () => {
        circle.setAttribute('r', '12');
        circle.setAttribute('opacity', '1');
      });

      g.appendChild(circle);

      // Add node label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', (node.x! + 20).toString());
      text.setAttribute('y', (node.y! + 5).toString());
      text.setAttribute('font-size', '12');
      text.setAttribute('font-family', 'Arial, sans-serif');
      text.setAttribute('fill', '#374151');
      text.textContent = node.label.length > 20 ? `${node.label.substring(0, 20)}...` : node.label;
      g.appendChild(text);
    });

    // Apply zoom transform
    g.setAttribute('transform', `scale(${zoom})`);

  }, [graphData, zoom, onNodeClick]);

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.3));
  };

  const handleCenter = () => {
    setZoom(1);
  };

  const handleEntityTypeChange = (types: string[]) => {
    setSelectedEntityTypes(types);
  };

  const handleSearch = () => {
    if (searchEntity.trim()) {
      // Trigger a new query with the search entity as center
      refetch();
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load knowledge graph: {(error as any)?.message || 'Unknown error'}
      </Alert>
    );
  }

  return (
    <Paper sx={{ height: height + 100, borderRadius: 3, overflow: 'hidden' }}>
      {/* Toolbar */}
      <Toolbar sx={{ borderBottom: 1, borderColor: 'divider', gap: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Knowledge Graph
        </Typography>
        
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Entity Types</InputLabel>
          <Select
            multiple
            value={selectedEntityTypes}
            onChange={(e) => handleEntityTypeChange(e.target.value as string[])}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {availableEntityTypes.map((type) => (
              <MenuItem key={type} value={type}>
                {type}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          size="small"
          placeholder="Search entity ID..."
          value={searchEntity}
          onChange={(e) => setSearchEntity(e.target.value)}
          sx={{ minWidth: 200 }}
        />
        <Button
          variant="outlined"
          startIcon={<SearchIcon />}
          onClick={handleSearch}
          disabled={!searchEntity.trim()}
        >
          Search
        </Button>

        <Box sx={{ flexGrow: 1 }} />

        <IconButton onClick={handleZoomIn} title="Zoom In">
          <ZoomInIcon />
        </IconButton>
        <IconButton onClick={handleZoomOut} title="Zoom Out">
          <ZoomOutIcon />
        </IconButton>
        <IconButton onClick={handleCenter} title="Reset Zoom">
          <CenterIcon />
        </IconButton>
        <IconButton onClick={() => refetch()} title="Refresh">
          <RefreshIcon />
        </IconButton>
      </Toolbar>

      {/* Graph Container */}
      <Box sx={{ height, position: 'relative', overflow: 'hidden' }}>
        {isLoading ? (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%' 
          }}>
            <Typography>Loading knowledge graph...</Typography>
          </Box>
        ) : graphData ? (
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            style={{ backgroundColor: '#fafafa' }}
          />
        ) : (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%' 
          }}>
            <Typography color="text.secondary">
              No graph data available
            </Typography>
          </Box>
        )}

        {/* Selected Node Info */}
        {selectedNode && (
          <Card sx={{ 
            position: 'absolute', 
            top: 16, 
            right: 16, 
            width: 300,
            maxHeight: 400,
            overflow: 'auto'
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                {selectedNode.label}
              </Typography>
              <Chip 
                label={selectedNode.type} 
                size="small" 
                color="primary" 
                sx={{ mb: 2 }} 
              />
              
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Properties:
              </Typography>
              
              <Box sx={{ fontSize: '0.875rem' }}>
                {Object.entries(selectedNode.properties).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 0.5 }}>
                    <strong>{key}:</strong> {String(value)}
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* Graph Statistics */}
      {graphData && (
        <Box sx={{ 
          position: 'absolute', 
          bottom: 16, 
          left: 16, 
          bgcolor: 'rgba(255, 255, 255, 0.9)', 
          p: 1, 
          borderRadius: 2,
          boxShadow: 1
        }}>
          <Typography variant="caption">
            Nodes: {graphData.summary.node_count} | 
            Edges: {graphData.summary.edge_count} |
            Zoom: {(zoom * 100).toFixed(0)}%
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default GraphVisualization;
