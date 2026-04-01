import React, { useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  Paper,
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ChartVisualizationProps {
  data: any[];
  height?: number;
}

const ChartVisualization: React.FC<ChartVisualizationProps> = ({ 
  data, 
  height = 400 
}) => {
  const [chartType, setChartType] = React.useState<string>('line');
  const [xAxis, setXAxis] = React.useState<string>('');
  const [yAxis, setYAxis] = React.useState<string>('');
  const [groupBy, setGroupBy] = React.useState<string>('');

  // Extract available fields from data
  const availableFields = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const firstRecord = data[0];
    return Object.keys(firstRecord).filter(key => 
      !key.startsWith('_') && // Exclude internal fields
      (typeof firstRecord[key] === 'string' || 
       typeof firstRecord[key] === 'number' ||
       firstRecord[key] instanceof Date)
    );
  }, [data]);

  // Get numeric fields for Y-axis
  const numericFields = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const firstRecord = data[0];
    return availableFields.filter(field => 
      typeof firstRecord[field] === 'number'
    );
  }, [data, availableFields]);

  // Get categorical fields for grouping
  const categoricalFields = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const firstRecord = data[0];
    return availableFields.filter(field => 
      typeof firstRecord[field] === 'string'
    );
  }, [data, availableFields]);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!data || !xAxis || !yAxis) return [];

    // If groupBy is specified, aggregate data
    if (groupBy) {
      const grouped = data.reduce((acc, item) => {
        const groupKey = item[groupBy];
        const xValue = item[xAxis];
        const yValue = parseFloat(item[yAxis]) || 0;
        
        const key = `${groupKey}-${xValue}`;
        if (!acc[key]) {
          acc[key] = {
            [xAxis]: xValue,
            [groupBy]: groupKey,
            [yAxis]: 0,
            count: 0
          };
        }
        
        acc[key][yAxis] += yValue;
        acc[key].count += 1;
        
        return acc;
      }, {} as any);

      return Object.values(grouped).map((item: any) => ({
        ...item,
        [yAxis]: item[yAxis] / item.count // Average
      }));
    }

    // Transform data for charts
    return data.map(item => ({
      [xAxis]: item[xAxis],
      [yAxis]: parseFloat(item[yAxis]) || 0,
      ...item
    }));
  }, [data, xAxis, yAxis, groupBy]);

  // Color palette
  const colors = [
    '#8b5cf6', '#a855f7', '#9333ea', '#7c3aed', '#6d28d9',
    '#10b981', '#059669', '#047857', '#065f46',
    '#06b6d4', '#0891b2', '#0e7490', '#155e75',
    '#f59e0b', '#d97706', '#b45309', '#92400e'
  ];

  const renderChart = () => {
    if (!chartData.length || !xAxis || !yAxis) {
      return (
        <Alert severity="info">
          Please select X-axis and Y-axis fields to display the chart.
        </Alert>
      );
    }

    const commonProps = {
      width: '100%',
      height: height,
      data: chartData,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer {...commonProps}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxis} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey={yAxis} 
                stroke={colors[0]} 
                strokeWidth={2}
                dot={{ fill: colors[0] }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxis} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey={yAxis} 
                stroke={colors[0]} 
                fill={colors[0]}
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer {...commonProps}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxis} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={yAxis} fill={colors[0]} />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'pie':
        const pieData = chartData.slice(0, 10).map((item, index) => ({
          name: item[xAxis],
          value: item[yAxis],
          fill: colors[index % colors.length]
        }));

        return (
          <ResponsiveContainer {...commonProps}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={Math.min(height * 0.35, 150)}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer {...commonProps}>
            <ScatterChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xAxis} />
              <YAxis dataKey={yAxis} />
              <Tooltip />
              <Legend />
              <Scatter 
                dataKey={yAxis} 
                fill={colors[0]}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        return <Alert severity="error">Unknown chart type: {chartType}</Alert>;
    }
  };

  if (!data || data.length === 0) {
    return (
      <Alert severity="info">
        No data available for visualization.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Chart Configuration */}
      <Card sx={{ mb: 3, borderRadius: 2 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Chart Configuration
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value)}
                  label="Chart Type"
                >
                  <MenuItem value="line">Line Chart</MenuItem>
                  <MenuItem value="area">Area Chart</MenuItem>
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                  <MenuItem value="scatter">Scatter Plot</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>X-Axis</InputLabel>
                <Select
                  value={xAxis}
                  onChange={(e) => setXAxis(e.target.value)}
                  label="X-Axis"
                >
                  {availableFields.map((field) => (
                    <MenuItem key={field} value={field}>
                      {field}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Y-Axis</InputLabel>
                <Select
                  value={yAxis}
                  onChange={(e) => setYAxis(e.target.value)}
                  label="Y-Axis"
                >
                  {numericFields.map((field) => (
                    <MenuItem key={field} value={field}>
                      {field}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Group By (Optional)</InputLabel>
                <Select
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value)}
                  label="Group By (Optional)"
                >
                  <MenuItem value="">None</MenuItem>
                  {categoricalFields.map((field) => (
                    <MenuItem key={field} value={field}>
                      {field}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Chart Display */}
      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart
            {xAxis && yAxis && (
              <Typography variant="body2" color="text.secondary" component="span">
                {' '}• {xAxis} vs {yAxis}
                {groupBy && ` (grouped by ${groupBy})`}
              </Typography>
            )}
          </Typography>
        </Box>
        
        <Box sx={{ height: height }}>
          {renderChart()}
        </Box>
      </Paper>

      {/* Chart Statistics */}
      {chartData.length > 0 && xAxis && yAxis && (
        <Card sx={{ mt: 3, borderRadius: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Data Summary
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  Data Points
                </Typography>
                <Typography variant="h6">
                  {chartData.length}
                </Typography>
              </Grid>
              
              {numericFields.includes(yAxis) && (
                <>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Max {yAxis}
                    </Typography>
                    <Typography variant="h6">
                      {Math.max(...chartData.map(d => d[yAxis])).toFixed(2)}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Min {yAxis}
                    </Typography>
                    <Typography variant="h6">
                      {Math.min(...chartData.map(d => d[yAxis])).toFixed(2)}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Avg {yAxis}
                    </Typography>
                    <Typography variant="h6">
                      {(chartData.reduce((sum, d) => sum + d[yAxis], 0) / chartData.length).toFixed(2)}
                    </Typography>
                  </Grid>
                </>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ChartVisualization;