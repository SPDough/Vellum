# Otomeshon Frontend Development Guide

This guide provides comprehensive information for developing and maintaining the Otomeshon frontend application built with React, TypeScript, and Material-UI.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Component Architecture](#component-architecture)
- [State Management](#state-management)
- [Routing](#routing)
- [Data Fetching](#data-fetching)
- [Styling Guidelines](#styling-guidelines)
- [Testing Strategy](#testing-strategy)
- [Performance Optimization](#performance-optimization)
- [Development Workflow](#development-workflow)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

The Otomeshon frontend follows a modern React architecture with TypeScript, emphasizing:

- **Component-based architecture** with reusable UI components
- **Centralized state management** using Zustand
- **Type-safe development** with comprehensive TypeScript coverage
- **Material Design** principles via Material-UI (MUI)
- **Real-time updates** through WebSocket connections
- **Responsive design** for desktop and mobile devices

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Environment                       │
├─────────────────────────────────────────────────────────────┤
│  React Application (Single Page Application)                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Pages       │  │   Components    │  │    Hooks     │ │
│  │                 │  │                 │  │              │ │
│  │ • Dashboard     │  │ • Layout        │  │ • useAuth    │ │
│  │ • DataSandbox   │  │ • DataGrid      │  │ • useApi     │ │
│  │ • Agents        │  │ • Charts        │  │ • useSocket  │ │
│  │ • Workflows     │  │ • Forms         │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ State Management│  │   Services      │  │   Utilities  │ │
│  │                 │  │                 │  │              │ │
│  │ • Zustand Store │  │ • API Client    │  │ • Formatters │ │
│  │ • React Query   │  │ • WebSocket     │  │ • Validators │ │
│  │ • Local State   │  │ • Auth Service  │  │ • Constants  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Backend API                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   REST APIs     │  │   WebSocket     │  │ Authentication│ │
│  │                 │  │                 │  │              │ │
│  │ • Data Sandbox  │  │ • Real-time     │  │ • JWT Tokens │ │
│  │ • Workflows     │  │   Updates       │  │ • Role-based │ │
│  │ • Knowledge     │  │ • Notifications │  │   Access     │ │
│  │   Graph         │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Technologies

- **React 18** - UI library with concurrent features
- **TypeScript 5.8** - Type-safe JavaScript development
- **Vite** - Fast build tool and development server
- **Material-UI (MUI) 6** - React component library

### State Management

- **Zustand** - Lightweight state management
- **React Query (TanStack Query)** - Server state management
- **React Hook Form** - Form state management

### Data Visualization

- **Recharts** - Composable charting library
- **TanStack Table** - Headless table library
- **D3.js** (selective imports) - Data manipulation utilities

### Development Tools

- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript ESLint** - TypeScript-specific linting
- **Vite DevTools** - Development debugging

## Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── favicon.ico
│   └── index.html
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Layout/        # Layout components
│   │   ├── DataGrid/      # Data table components
│   │   ├── Charts/        # Chart components
│   │   ├── Forms/         # Form components
│   │   └── Common/        # Shared components
│   ├── pages/             # Page components
│   │   ├── Dashboard.tsx
│   │   ├── DataSandbox.tsx
│   │   ├── Agents.tsx
│   │   ├── Workflows.tsx
│   │   └── KnowledgeGraph.tsx
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   ├── useSocket.ts
│   │   └── useLocalStorage.ts
│   ├── services/          # API and external services
│   │   ├── api.ts         # API client configuration
│   │   ├── authService.ts
│   │   ├── dataSandboxService.ts
│   │   └── websocketService.ts
│   ├── store/             # State management
│   │   ├── index.ts       # Main store configuration
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── dataStore.ts
│   ├── types/             # TypeScript type definitions
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── data.ts
│   │   └── ui.ts
│   ├── utils/             # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── styles/            # Global styles and themes
│   │   ├── theme.ts       # MUI theme configuration
│   │   ├── globals.css
│   │   └── components.css
│   ├── App.tsx            # Main application component
│   ├── main.tsx           # Application entry point
│   └── vite-env.d.ts      # Vite type definitions
├── tests/                 # Test files
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── utils/
├── package.json           # Dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite configuration
├── eslint.config.js       # ESLint configuration
└── README.md              # Frontend-specific documentation
```

## Component Architecture

### Component Hierarchy

The application follows a hierarchical component structure:

```
App
├── Layout
│   ├── Header
│   ├── Sidebar
│   └── Main Content
│       ├── Dashboard
│       ├── DataSandbox
│       │   ├── DataGrid
│       │   ├── FilterPanel
│       │   └── ExportDialog
│       ├── Agents
│       │   ├── AgentList
│       │   ├── AgentDetail
│       │   └── ChatInterface
│       ├── Workflows
│       │   ├── WorkflowBuilder
│       │   ├── NodePalette
│       │   └── PropertyPanel
│       └── KnowledgeGraph
│           ├── GraphVisualization
│           ├── NodeDetails
│           └── SearchPanel
```

### Component Design Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **Composition over Inheritance**: Use composition to build complex UIs
3. **Props Interface**: Well-defined TypeScript interfaces for all props
4. **Error Boundaries**: Graceful error handling at component boundaries
5. **Accessibility**: WCAG 2.1 AA compliance for all interactive elements

### Example Component Structure

```typescript
// components/DataGrid/DataGrid.tsx
import React, { useMemo } from 'react';
import { 
  useReactTable, 
  getCoreRowModel, 
  getSortedRowModel,
  getFilteredRowModel,
  ColumnDef 
} from '@tanstack/react-table';
import { Box, Paper, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { DataRecord } from '@/types/data';

interface DataGridProps {
  data: DataRecord[];
  columns: ColumnDef<DataRecord>[];
  loading?: boolean;
  onRowClick?: (row: DataRecord) => void;
  onSelectionChange?: (selectedRows: DataRecord[]) => void;
}

export const DataGrid: React.FC<DataGridProps> = ({
  data,
  columns,
  loading = false,
  onRowClick,
  onSelectionChange
}) => {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const handleRowClick = (row: DataRecord) => {
    onRowClick?.(row);
  };

  if (loading) {
    return <DataGridSkeleton />;
  }

  return (
    <Paper elevation={1}>
      <Table>
        <TableHead>
          {table.getHeaderGroups().map(headerGroup => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <TableCell key={header.id}>
                  {header.isPlaceholder ? null : (
                    <Box
                      sx={{ cursor: header.column.getCanSort() ? 'pointer' : 'default' }}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </Box>
                  )}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableHead>
        <TableBody>
          {table.getRowModel().rows.map(row => (
            <TableRow 
              key={row.id}
              hover
              onClick={() => handleRowClick(row.original)}
              sx={{ cursor: 'pointer' }}
            >
              {row.getVisibleCells().map(cell => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
};
```

## State Management

### Zustand Store Architecture

The application uses Zustand for client-side state management with a modular approach:

```typescript
// store/index.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { AuthSlice, createAuthSlice } from './authStore';
import { UISlice, createUISlice } from './uiStore';
import { DataSlice, createDataSlice } from './dataStore';

export interface AppState extends AuthSlice, UISlice, DataSlice {}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (...args) => ({
        ...createAuthSlice(...args),
        ...createUISlice(...args),
        ...createDataSlice(...args),
      }),
      {
        name: 'otomeshon-store',
        partialize: (state) => ({
          auth: state.auth,
          ui: {
            theme: state.theme,
            sidebarCollapsed: state.sidebarCollapsed,
          },
        }),
      }
    ),
    { name: 'otomeshon-store' }
  )
);
```

### Auth Store

```typescript
// store/authStore.ts
import { StateCreator } from 'zustand';
import { User } from '@/types/auth';

export interface AuthSlice {
  auth: {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
  };
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
}

export const createAuthSlice: StateCreator<AuthSlice> = (set, get) => ({
  auth: {
    user: null,
    token: null,
    isAuthenticated: false,
    loading: false,
  },
  
  login: async (email: string, password: string) => {
    set((state) => ({ auth: { ...state.auth, loading: true } }));
    
    try {
      const response = await authService.login(email, password);
      set((state) => ({
        auth: {
          ...state.auth,
          user: response.user,
          token: response.token,
          isAuthenticated: true,
          loading: false,
        },
      }));
    } catch (error) {
      set((state) => ({ auth: { ...state.auth, loading: false } }));
      throw error;
    }
  },
  
  logout: () => {
    authService.logout();
    set((state) => ({
      auth: {
        ...state.auth,
        user: null,
        token: null,
        isAuthenticated: false,
      },
    }));
  },
  
  refreshToken: async () => {
    try {
      const response = await authService.refreshToken();
      set((state) => ({
        auth: {
          ...state.auth,
          token: response.token,
        },
      }));
    } catch (error) {
      get().logout();
      throw error;
    }
  },
  
  updateUser: (userUpdate: Partial<User>) => {
    set((state) => ({
      auth: {
        ...state.auth,
        user: state.auth.user ? { ...state.auth.user, ...userUpdate } : null,
      },
    }));
  },
});
```

## Routing

The application uses React Router v6 for client-side routing:

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { ProtectedRoute } from '@/components/Auth/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route 
            path="dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="data-sandbox" 
            element={
              <ProtectedRoute>
                <DataSandbox />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="agents" 
            element={
              <ProtectedRoute>
                <Agents />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="workflows" 
            element={
              <ProtectedRoute>
                <Workflows />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="knowledge-graph" 
            element={
              <ProtectedRoute>
                <KnowledgeGraph />
              </ProtectedRoute>
            } 
          />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Data Fetching

### React Query Integration

The application uses TanStack Query (React Query) for server state management:

```typescript
// hooks/useDataSandbox.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataSandboxService } from '@/services/dataSandboxService';
import { DataQuery, DataRecord } from '@/types/data';

export const useDataSandboxRecords = (query: DataQuery) => {
  return useQuery({
    queryKey: ['dataSandbox', 'records', query],
    queryFn: () => dataSandboxService.getRecords(query),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useDataSandboxStats = () => {
  return useQuery({
    queryKey: ['dataSandbox', 'stats'],
    queryFn: () => dataSandboxService.getStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useExportData = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: dataSandboxService.exportData,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSandbox'] });
    },
  });
};
```

### WebSocket Integration

Real-time updates are handled through WebSocket connections:

```typescript
// hooks/useSocket.ts
import { useEffect, useRef } from 'react';
import { useAppStore } from '@/store';
import { websocketService } from '@/services/websocketService';

export const useSocket = () => {
  const { auth } = useAppStore();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (auth.isAuthenticated && auth.token) {
      socketRef.current = websocketService.connect(auth.token);
      
      socketRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleSocketMessage(data);
      };

      return () => {
        if (socketRef.current) {
          websocketService.disconnect();
          socketRef.current = null;
        }
      };
    }
  }, [auth.isAuthenticated, auth.token]);

  const handleSocketMessage = (data: any) => {
    switch (data.type) {
      case 'DATA_UPDATE':
        queryClient.invalidateQueries({ queryKey: ['dataSandbox'] });
        break;
      case 'NOTIFICATION':
        showNotification(data.message);
        break;
      default:
        console.log('Unknown socket message type:', data.type);
    }
  };

  return {
    isConnected: socketRef.current?.readyState === WebSocket.OPEN,
    send: (message: any) => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify(message));
      }
    },
  };
};
```

## Styling Guidelines

### Material-UI Theme Configuration

```typescript
// styles/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});
```

### Component Styling Best Practices

1. **Use MUI's sx prop** for component-specific styles
2. **Create reusable styled components** for common patterns
3. **Follow Material Design principles** for spacing and layout
4. **Use theme values** for colors, typography, and spacing
5. **Implement responsive design** using MUI's breakpoint system

```typescript
// Example of good styling practices
const StyledDataGrid = styled(Paper)(({ theme }) => ({
  borderRadius: theme.spacing(1.5),
  overflow: 'hidden',
  '& .MuiTable-root': {
    minWidth: 650,
  },
  '& .MuiTableHead-root': {
    backgroundColor: theme.palette.grey[50],
  },
  '& .MuiTableRow-root:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}));
```

## Testing Strategy

### Testing Framework Setup

The application uses Vitest and React Testing Library:

```typescript
// tests/setup.ts
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});
```

### Component Testing Example

```typescript
// tests/components/DataGrid.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DataGrid } from '@/components/DataGrid/DataGrid';
import { mockDataRecords } from '../mocks/data';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('DataGrid', () => {
  it('renders data correctly', () => {
    const columns = [
      { accessorKey: 'id', header: 'ID' },
      { accessorKey: 'name', header: 'Name' },
    ];

    render(
      <DataGrid data={mockDataRecords} columns={columns} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText(mockDataRecords[0].name)).toBeInTheDocument();
  });

  it('handles row click events', () => {
    const onRowClick = vi.fn();
    const columns = [{ accessorKey: 'name', header: 'Name' }];

    render(
      <DataGrid 
        data={mockDataRecords} 
        columns={columns} 
        onRowClick={onRowClick}
      />,
      { wrapper: createWrapper() }
    );

    fireEvent.click(screen.getByText(mockDataRecords[0].name));
    expect(onRowClick).toHaveBeenCalledWith(mockDataRecords[0]);
  });
});
```

## Performance Optimization

### Code Splitting

```typescript
// Lazy loading for route components
import { lazy, Suspense } from 'react';
import { CircularProgress, Box } from '@mui/material';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const DataSandbox = lazy(() => import('@/pages/DataSandbox'));
const Agents = lazy(() => import('@/pages/Agents'));

const LoadingFallback = () => (
  <Box display="flex" justifyContent="center" alignItems="center" height="200px">
    <CircularProgress />
  </Box>
);

// In routing configuration
<Route 
  path="dashboard" 
  element={
    <Suspense fallback={<LoadingFallback />}>
      <Dashboard />
    </Suspense>
  } 
/>
```

### Memoization Strategies

```typescript
// Use React.memo for expensive components
export const DataGrid = React.memo<DataGridProps>(({ data, columns, ...props }) => {
  // Component implementation
}, (prevProps, nextProps) => {
  return (
    prevProps.data.length === nextProps.data.length &&
    prevProps.columns.length === nextProps.columns.length
  );
});

// Use useMemo for expensive calculations
const processedData = useMemo(() => {
  return data.map(item => ({
    ...item,
    formattedValue: formatCurrency(item.value),
    calculatedField: performExpensiveCalculation(item),
  }));
}, [data]);

// Use useCallback for event handlers
const handleRowClick = useCallback((row: DataRecord) => {
  onRowClick?.(row);
}, [onRowClick]);
```

## Development Workflow

### Local Development Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Run type checking**:
   ```bash
   npm run type-check
   ```

4. **Run linting**:
   ```bash
   npm run lint
   npm run lint:fix  # Auto-fix issues
   ```

5. **Run tests**:
   ```bash
   npm run test
   npm run test:watch  # Watch mode
   npm run test:coverage  # With coverage
   ```

### Build and Deployment

1. **Production build**:
   ```bash
   npm run build
   ```

2. **Preview production build**:
   ```bash
   npm run preview
   ```

3. **Analyze bundle size**:
   ```bash
   npm run analyze
   ```

## Common Patterns

### Error Handling

```typescript
// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box textAlign="center" p={4}>
          <Typography variant="h6" color="error">
            Something went wrong. Please refresh the page.
          </Typography>
        </Box>
      );
    }

    return this.props.children;
  }
}
```

### Loading States

```typescript
// Consistent loading state handling
const useAsyncOperation = <T,>(
  operation: () => Promise<T>,
  dependencies: any[] = []
) => {
  const [state, setState] = useState<{
    data: T | null;
    loading: boolean;
    error: Error | null;
  }>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await operation();
      setState({ data: result, loading: false, error: null });
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error as Error 
      }));
    }
  }, dependencies);

  return { ...state, execute };
};
```

## Troubleshooting

### Common Issues

1. **TypeScript errors with TanStack Table**:
   - Ensure column definitions have proper type annotations
   - Use `ColumnDef<DataRecord>` for type safety

2. **WebSocket connection issues**:
   - Check authentication token validity
   - Verify WebSocket URL configuration
   - Handle connection state properly

3. **Performance issues with large datasets**:
   - Implement virtualization for large tables
   - Use pagination or infinite scrolling
   - Optimize re-renders with proper memoization

4. **Build failures**:
   - Clear node_modules and reinstall dependencies
   - Check for TypeScript errors
   - Verify environment variable configuration

### Debugging Tools

1. **React Developer Tools** - Component inspection and profiling
2. **Redux DevTools** - State management debugging (works with Zustand)
3. **Network tab** - API request monitoring
4. **Console logging** - Strategic logging for development

This comprehensive frontend guide provides the foundation for developing and maintaining the Otomeshon React application. For specific implementation details, refer to the individual component files and their documentation.
