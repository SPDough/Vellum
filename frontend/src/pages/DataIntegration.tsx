import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';

import { MCPServer, DataStream } from '@/types/data';
import { mcpServerService } from '@/services/mcpServerService';
import { dataStreamService } from '@/services/dataStreamService';
import NewConnectionDialog from '@/components/DataIntegration/NewConnectionDialog';

interface DataIntegrationProps {}

const DataIntegration: React.FC<DataIntegrationProps> = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [showNewConnectionDialog, setShowNewConnectionDialog] = useState(false);
  const queryClient = useQueryClient();

  // Fetch MCP servers from API
  const { data: mcpServers = [], error: serversError } = useQuery<MCPServer[]>(
    'mcp-servers',
    () => mcpServerService.listServers(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 10000, // Consider data stale after 10 seconds
    }
  );

  // Fetch data streams from API
  const { data: dataStreams = [], error: streamsError } = useQuery<DataStream[]>(
    'data-streams',
    () => dataStreamService.listStreams(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds for real-time data
      staleTime: 2000,
    }
  );


  const handleRefresh = () => {
    queryClient.invalidateQueries('mcp-servers');
    queryClient.invalidateQueries('data-streams');
  };

  const handleNewConnectionSuccess = () => {
    setShowNewConnectionDialog(false);
    queryClient.invalidateQueries('mcp-servers');
  };

  const renderTabContent = () => {
    return <div>Simple test content</div>;
  };



  const connectedServers = mcpServers.filter(s => s.status === 'CONNECTED').length;
  const totalDataVolume = mcpServers.reduce((acc, server) => acc + (server.metrics?.data_volume_mb || 0), 0);
  const avgUptime = mcpServers.length > 0 
    ? mcpServers.reduce((acc, server) => acc + (server.metrics?.uptime_percentage || 0), 0) / mcpServers.length 
    : 0;

  return (
    <>
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontWeight: 600, margin: 0, marginBottom: '8px' }}>
              Data Integration
            </h1>
            <p style={{ color: '#666', margin: 0 }}>
              Monitor and manage connections to custodians and market data providers
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={handleRefresh} style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #ccc', background: 'white', cursor: 'pointer' }}>
              Refresh
            </button>
            <button onClick={() => setShowNewConnectionDialog(true)} style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', background: '#1976d2', color: 'white', cursor: 'pointer' }}>
              New Connection
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '24px', marginBottom: '32px', flexWrap: 'wrap' }}>
          <div style={{ flex: '1', minWidth: '250px' }}>
            <div>Connected Servers: {connectedServers}</div>
          </div>
          <div style={{ flex: '1', minWidth: '250px' }}>
            <div>Data Volume: {totalDataVolume.toFixed(1)}GB</div>
          </div>
          <div style={{ flex: '1', minWidth: '250px' }}>
            <div>Uptime: {avgUptime.toFixed(1)}%</div>
          </div>
          <div style={{ flex: '1', minWidth: '250px' }}>
            <div>Streams: {dataStreams.length}</div>
          </div>
        </div>

        {Boolean(serversError || streamsError) ? (
          <div style={{ padding: '16px', backgroundColor: '#ffebee', border: '1px solid #f44336', borderRadius: '4px', marginBottom: '16px' }}>
            Failed to load data. Please check your connection and try again.
          </div>
        ) : null}
      </div>

      <div style={{ border: '1px solid #e0e0e0', borderRadius: '12px', marginBottom: '24px', margin: '24px' }}>
        <div style={{ borderBottom: '1px solid #e0e0e0', padding: '0' }}>
          <button 
            onClick={() => setActiveTab(0)}
            style={{ 
              padding: '12px 24px', 
              border: 'none', 
              background: activeTab === 0 ? '#f5f5f5' : 'transparent',
              cursor: 'pointer'
            }}
          >
            MCP Servers
          </button>
          <button 
            onClick={() => setActiveTab(1)}
            style={{ 
              padding: '12px 24px', 
              border: 'none', 
              background: activeTab === 1 ? '#f5f5f5' : 'transparent',
              cursor: 'pointer'
            }}
          >
            Data Flows
          </button>
          <button 
            onClick={() => setActiveTab(2)}
            style={{ 
              padding: '12px 24px', 
              border: 'none', 
              background: activeTab === 2 ? '#f5f5f5' : 'transparent',
              cursor: 'pointer'
            }}
          >
            Real-time Streams
          </button>
          <button 
            onClick={() => setActiveTab(3)}
            style={{ 
              padding: '12px 24px', 
              border: 'none', 
              background: activeTab === 3 ? '#f5f5f5' : 'transparent',
              cursor: 'pointer'
            }}
          >
            Data Quality
          </button>
        </div>
        <div style={{ padding: '24px' }}>
          {renderTabContent()}
        </div>
      </div>

      {/* New Connection Dialog */}
      <NewConnectionDialog
        open={showNewConnectionDialog}
        onClose={() => setShowNewConnectionDialog(false)}
        onSuccess={handleNewConnectionSuccess}
      />
    </>
  );
};

export default DataIntegration;
