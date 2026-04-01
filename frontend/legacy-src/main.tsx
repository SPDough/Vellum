/**
 * @deprecated Legacy SPA bootstrap retained temporarily for migration reference.
 *
 * The canonical frontend runtime for Vellum is the Next.js App Router under
 * `frontend/app/*`, not this `src/main.tsx` entrypoint.
 *
 * Do not treat this file as the primary application bootstrap for new work.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
