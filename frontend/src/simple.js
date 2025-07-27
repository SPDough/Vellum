// Simple JavaScript test - no TypeScript, no React
console.log('🔍 Simple JS file loaded');

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔍 DOM loaded');
  
  const root = document.getElementById('root');
  if (root) {
    console.log('✅ Root element found');
    root.innerHTML = `
      <div style="padding: 20px; background: lightgreen; font-family: Arial;">
        <h1>✅ JavaScript is Working!</h1>
        <p>This is plain JavaScript - no React, no TypeScript.</p>
        <p>Time: ${new Date().toLocaleString()}</p>
      </div>
    `;
    console.log('✅ Content injected');
  } else {
    console.error('❌ Root element not found');
  }
});