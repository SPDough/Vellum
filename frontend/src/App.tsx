/**
 * Otomeshon Frontend Application - Main Entry Point
 * 
 * This is the root component of the Otomeshon agentic trading system frontend.
 * It provides a comprehensive React-based user interface for financial data management,
 * workflow orchestration, and real-time trading operations.
 * 
 * Key Features:
 * - Material-UI theming and responsive design
 * - React Router for client-side navigation
 * - Modular component architecture for maintainability
 * - Real-time data updates and WebSocket integration
 * - Comprehensive form handling and validation
 * - Advanced data visualization and analytics
 * 
 * Architecture:
 * - Single Page Application (SPA) with client-side routing
 * - Component-based architecture with clear separation of concerns
 * - Material-UI design system for consistent user experience
 * - TypeScript for type safety and better developer experience
 * - Context API for global state management
 * 
 * Navigation Structure:
 * - Dashboard: Overview of system status and key metrics
 * - Positions: Portfolio position management and analysis
 * - Transactions: Trade execution and transaction history
 * - Reconciliation: Data reconciliation and validation
 * - Workflows: LangGraph workflow management and monitoring
 * - Rules: Business rules catalog and configuration
 * - Data Sources: External data source configuration and management
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Core layout component that provides the main application structure
import Layout from './components/Layout';

// Page components for different sections of the application
import Positions from './components/pages/Positions';                    // Portfolio positions and holdings management
import Transactions from './components/pages/Transactions';              // Trade execution and transaction processing
import Reconciliation from './components/pages/Reconciliation';          // Data reconciliation and validation workflows
import WorkflowManagement from './components/pages/WorkflowManagement';  // LangGraph workflow orchestration
import RulesCatalog from './components/pages/RulesCatalog';              // Business rules and compliance management
import DataSourceConfiguration from './components/pages/DataSourceConfiguration';  // External data source integration

/**
 * Material-UI Theme Configuration
 * 
 * Defines the visual design system for the entire application including colors,
 * typography, spacing, and component styling. This theme ensures consistent
 * visual appearance across all components and pages.
 * 
 * Design Principles:
 * - Professional financial application aesthetic
 * - High contrast for accessibility and readability
 * - Consistent color palette for different UI states
 * - Responsive typography for various screen sizes
 */
const theme = createTheme({
  palette: {
    mode: 'light',  // Light theme for better readability in professional environments
    primary: {
      main: '#1976d2',  // Professional blue for primary actions and branding
    },
    secondary: {
      main: '#dc004e',  // Accent red for alerts, warnings, and secondary actions
    },
    // Additional palette colors can be extended here for:
    // - Success states (green)
    // - Warning states (orange/yellow)
    // - Error states (red)
    // - Info states (blue)
  },
  // Typography, spacing, and component overrides can be added here
  // to further customize the design system
});

/**
 * Main Application Component
 * 
 * This is the root component that renders the entire application structure.
 * It sets up the global providers (theme, routing) and defines the main
 * navigation structure using React Router.
 * 
 * Component Hierarchy:
 * 1. ThemeProvider - Provides Material-UI theme to all child components
 * 2. CssBaseline - Normalizes CSS across different browsers
 * 3. Router - Enables client-side routing and navigation
 * 4. Layout - Main application layout with navigation and content areas
 * 5. Route Components - Individual page components for different sections
 * 
 * Routing Structure:
 * - All routes are nested under the Layout component for consistent navigation
 * - Each route corresponds to a major functional area of the application
 * - Nested routing allows for sub-pages within each main section
 */
const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      {/* Normalize CSS across browsers and apply base Material-UI styles */}
      <CssBaseline />
      
      {/* Client-side routing setup for SPA navigation */}
      <Router>
        <Routes>
          {/* Main application layout with nested routes */}
          <Route path="/" element={<Layout />}>
            {/* Dashboard - Main landing page with system overview */}
            <Route index element={<div>Dashboard Placeholder</div>} />
            
            {/* Portfolio Management Routes */}
            <Route path="positions" element={<Positions />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="reconciliation" element={<Reconciliation />} />
            
            {/* Workflow and Rules Management Routes */}
            <Route path="workflows" element={<WorkflowManagement />} />
            <Route path="rules" element={<RulesCatalog />} />
            
            {/* System Configuration Routes */}
            <Route path="data-sources" element={<DataSourceConfiguration />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;
