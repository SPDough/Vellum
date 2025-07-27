import React from 'react';

const TestApp: React.FC = () => {
  console.log('TestApp rendering...');
  
  React.useEffect(() => {
    console.log('TestApp mounted!');
    document.title = 'TestApp Mounted Successfully';
  }, []);

  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f8ff', fontFamily: 'Arial' }}>
      <h1 style={{ color: 'green' }}>✅ React is Working!</h1>
      <p>This is a minimal test component to verify React mounting.</p>
      <div style={{ marginTop: '20px', padding: '10px', background: 'white', border: '1px solid #ccc' }}>
        <strong>Test Info:</strong>
        <ul>
          <li>React Version: {React.version}</li>
          <li>Current Time: {new Date().toLocaleTimeString()}</li>
          <li>Test Status: ✅ SUCCESS</li>
        </ul>
      </div>
    </div>
  );
};

export default TestApp;