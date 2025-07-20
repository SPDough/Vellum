import React from 'react';

const SimpleDataSandbox: React.FC = () => {
  const [data, setData] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    // Fetch data from our API
    fetch('/api/v1/data-sandbox/records?page=1&page_size=10')
      .then(response => response.json())
      .then(result => {
        setData(result.data || []);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading data...</div>;
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🎉 Otomeshon Data Sandbox</h1>
      <p>Simple data table showing banking transaction data from the API.</p>
      
      <div style={{ marginTop: '20px' }}>
        <h2>Sample Data ({data.length} records)</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Source</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Type</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Amount</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Currency</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Status</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Customer</th>
            </tr>
          </thead>
          <tbody>
            {data.map((record, index) => (
              <tr key={record.id || index}>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{record.source}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{record.data?.type}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>${record.data?.amount}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{record.data?.currency}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                  <span style={{ 
                    padding: '2px 6px', 
                    borderRadius: '4px',
                    backgroundColor: record.data?.status === 'completed' ? '#d4edda' : 
                                   record.data?.status === 'pending' ? '#fff3cd' : '#f8d7da',
                    color: record.data?.status === 'completed' ? '#155724' : 
                           record.data?.status === 'pending' ? '#856404' : '#721c24'
                  }}>
                    {record.data?.status}
                  </span>
                </td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{record.data?.customer_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
        <h3>API Status</h3>
        <p>✅ Backend API: <a href="http://localhost:8000/health" target="_blank">http://localhost:8000/health</a></p>
        <p>✅ Data API: <a href="http://localhost:8000/api/v1/data-sandbox/stats" target="_blank">http://localhost:8000/api/v1/data-sandbox/stats</a></p>
      </div>
    </div>
  );
};

export default SimpleDataSandbox;