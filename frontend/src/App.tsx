import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Layout from './components/Layout';
import Positions from './pages/Positions';
import Transactions from './pages/Transactions';
import Reconciliation from './pages/Reconciliation';
import WorkflowManagement from './pages/WorkflowManagement';
import RulesCatalog from './pages/RulesCatalog';
import DataSourceConfiguration from './pages/DataSourceConfiguration';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<div>Dashboard Placeholder</div>} />
            <Route path="positions" element={<Positions />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="reconciliation" element={<Reconciliation />} />
            <Route path="workflows" element={<WorkflowManagement />} />
            <Route path="rules" element={<RulesCatalog />} />
            <Route path="data-sources" element={<DataSourceConfiguration />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;
