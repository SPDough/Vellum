import React, { lazy, Suspense, useState } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, CircularProgress } from '@mui/material';
import { theme } from '@/theme';
import Layout from '@/components/Layout';
import { ProtectedRoute } from '@/components/Auth/ProtectedRoute';

const Home = lazy(() => import('@/components/pages/Home'));
const Login = lazy(() => import('@/components/pages/Login'));
const NotFound = lazy(() => import('@/components/pages/NotFound'));
const Unauthorized = lazy(() => import('@/components/pages/Unauthorized'));
const CustodianLangGraph = lazy(() => import('@/components/pages/CustodianLangGraph'));
const Dashboard = lazy(() => import('@/components/pages/Dashboard'));
const Agents = lazy(() => import('@/components/pages/Agents'));
const Analytics = lazy(() => import('@/components/pages/Analytics'));
const DataIntegration = lazy(() => import('@/components/pages/DataIntegration'));
const DataSandbox = lazy(() => import('@/components/pages/DataSandbox'));
const DataSourceConfiguration = lazy(() => import('@/components/pages/DataSourceConfiguration'));
const KnowledgeGraph = lazy(() => import('@/components/pages/KnowledgeGraph'));
const Positions = lazy(() => import('@/components/pages/Positions'));
const Reconciliation = lazy(() => import('@/components/pages/Reconciliation'));
const RulesCatalog = lazy(() => import('@/components/pages/RulesCatalog'));
const Settings = lazy(() => import('@/components/pages/Settings'));
const SOPManager = lazy(() => import('@/components/pages/SOPManager'));
const Transactions = lazy(() => import('@/components/pages/Transactions'));
const WorkflowBuilder = lazy(() => import('@/components/pages/WorkflowBuilder'));
const WorkflowConfigurationPage = lazy(() => import('@/components/pages/WorkflowConfigurationPage'));
const WorkflowConfigurationTest = lazy(() => import('@/components/pages/WorkflowConfigurationTest'));
const WorkflowExecutor = lazy(() => import('@/components/pages/WorkflowExecutor'));
const WorkflowManagement = lazy(() => import('@/components/pages/WorkflowManagement'));

const RouteLoadingFallback = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
    <CircularProgress />
  </Box>
);

const App: React.FC = () => {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <HashRouter>
          <Suspense fallback={<RouteLoadingFallback />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/custodian-langgraph"
                element={
                  <ProtectedRoute>
                    <CustodianLangGraph />
                  </ProtectedRoute>
                }
              />

              <Route
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<Home />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/agents" element={<Agents />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/data" element={<DataIntegration />} />
                <Route path="/data-sandbox" element={<DataSandbox />} />
                <Route path="/data-sources" element={<DataSourceConfiguration />} />
                <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
                <Route path="/positions" element={<Positions />} />
                <Route path="/reconciliation" element={<Reconciliation />} />
                <Route path="/rules" element={<RulesCatalog />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/sop-manager" element={<SOPManager />} />
                <Route path="/transactions" element={<Transactions />} />
                <Route path="/workflow-builder" element={<WorkflowBuilder />} />
                <Route path="/workflow-configuration" element={<WorkflowConfigurationPage />} />
                <Route path="/workflow-configuration-test" element={<WorkflowConfigurationTest />} />
                <Route path="/workflow-executor" element={<WorkflowExecutor />} />
                <Route path="/workflows" element={<WorkflowManagement />} />
                <Route path="/unauthorized" element={<Unauthorized />} />
              </Route>

              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </HashRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
