// Debug script to test React mounting
console.log('🔍 Debug script loaded');

// Test 1: Check if root element exists
const rootElement = document.getElementById('root');
console.log('Root element:', rootElement);

if (rootElement) {
  // Test 2: Try to mount something directly
  rootElement.innerHTML = '<div style="padding: 20px; background: lightgreen;"><h1>✅ Direct DOM Manipulation Works!</h1><p>This proves the root element exists and can be modified.</p></div>';
  
  // Test 3: Try React mounting
  try {
    console.log('🔍 Attempting React import...');
    import('react').then(React => {
      console.log('✅ React imported successfully:', React);
      
      import('react-dom/client').then(ReactDOM => {
        console.log('✅ ReactDOM imported successfully:', ReactDOM);
        
        const SimpleComponent = () => {
          console.log('🎯 SimpleComponent rendering');
          return React.createElement('div', { 
            style: { padding: '20px', background: 'lightblue' } 
          }, 
            React.createElement('h1', null, '🎉 React Mount Success!'),
            React.createElement('p', null, 'React is working properly now.')
          );
        };
        
        console.log('🔍 Creating React root...');
        const root = ReactDOM.createRoot(rootElement);
        
        console.log('🔍 Rendering React component...');
        root.render(React.createElement(SimpleComponent));
        
        console.log('✅ React rendering complete!');
      }).catch(err => {
        console.error('❌ ReactDOM import failed:', err);
      });
    }).catch(err => {
      console.error('❌ React import failed:', err);
    });
  } catch (err) {
    console.error('❌ React mounting failed:', err);
  }
} else {
  console.error('❌ Root element not found!');
}

export {};