import React from 'react';

const App: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🎉 Otomeshon is Working!</h1>
      <p>This is a simple test to verify React is mounting correctly.</p>
      <div style={{ background: '#f0f0f0', padding: '10px', borderRadius: '5px', marginTop: '20px' }}>
        <h3>Backend Status:</h3>
        <p>Backend API: <a href="http://localhost:8000/health" target="_blank">http://localhost:8000/health</a></p>
        <p>Data Sandbox API: <a href="http://localhost:8000/api/v1/data-sandbox/stats" target="_blank">http://localhost:8000/api/v1/data-sandbox/stats</a></p>
      </div>
    </div>
  );
};

export default App;