# Required Dependencies for Otomeshon Frontend

## TanStack Table (Data Sandbox)
The Data Sandbox feature requires TanStack Table for advanced data grid functionality.

```bash
npm install @tanstack/react-table
```

## Optional Dependencies for Enhanced Features

### Chart Visualization (for Data Sandbox Chart View)
```bash
npm install recharts
# or
npm install @nivo/core @nivo/line @nivo/bar @nivo/pie
```

### Data Export (Excel support)
```bash
npm install xlsx
```

### CSV Parsing/Export
```bash
npm install papaparse
npm install @types/papaparse --save-dev
```

### Date Handling
```bash
npm install date-fns
```

### Advanced Data Filtering
```bash
npm install fuse.js  # For fuzzy search
```

## Already Included Dependencies
- Material-UI (@mui/material, @mui/icons-material)
- React Query (react-query)
- React Router (react-router-dom)
- Zustand (state management)

## Installation Command
To install all required dependencies at once:

```bash
npm install @tanstack/react-table recharts xlsx papaparse date-fns fuse.js
npm install @types/papaparse --save-dev
```

## Usage Notes

### TanStack Table
- Provides powerful data grid features
- Headless design works perfectly with Material-UI
- Supports sorting, filtering, pagination, column visibility
- Integrates well with React Query for data fetching

### Workflow Integration
- Data from workflows is automatically displayed in the sandbox
- Supports JSON, CSV, and structured data formats
- Real-time updates when workflows complete

### MCP Integration
- MCP server data streams appear in the sandbox
- Supports various content types and encodings
- Live data updates from connected servers

### Export Features
- CSV export (built-in)
- JSON export (built-in)
- Excel export (requires xlsx dependency)
- Scheduled exports (future feature)