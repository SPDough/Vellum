# Workflow Configuration System

## Overview

The Workflow Configuration System provides a comprehensive interface for viewing and modifying LangGraph and LangChain workflow parameters, nodes, and execution settings within the Otomeshon platform.

## Features

### 🔧 Configuration Management
- **Parameter Configuration**: Add, edit, and delete workflow parameters with various data types (string, number, boolean, select, array, object)
- **Node Management**: View and configure workflow nodes with their inputs, outputs, and settings
- **Execution Settings**: Configure retry policies, timeouts, and concurrent execution limits
- **Performance Settings**: Enable caching, parallel processing, and optimization features
- **Security Settings**: Configure encryption, audit logging, and access restrictions

### 📊 Visual Interface
- **Tabbed Interface**: Organized sections for different configuration aspects
- **Real-time Preview**: View configuration changes before saving
- **Export Functionality**: Download configuration as JSON for backup or sharing
- **Parameter Validation**: Built-in validation for parameter types and values

### 🔄 Integration
- **LangChain Support**: Full configuration support for LangChain workflows
- **LangGraph Support**: Complete configuration management for LangGraph workflows
- **API Integration**: RESTful API endpoints for programmatic configuration management

## Architecture

### Frontend Components

#### `WorkflowConfiguration.tsx`
Main configuration component with the following tabs:
- **Nodes**: View and manage workflow nodes
- **Parameters**: Configure workflow parameters
- **Execution Settings**: Set execution policies and timeouts
- **Performance**: Configure caching and optimization
- **Security**: Set security and access controls
- **Preview**: View and export configuration

#### `WorkflowConfigurationPage.tsx`
Page wrapper that handles URL parameters for workflow ID and type.

### Backend Services

#### Enhanced LangChain Service
- `get_workflow_info()`: Returns detailed workflow configuration
- `update_workflow_configuration()`: Updates workflow settings
- Automatic parameter generation based on workflow type

#### Enhanced LangGraph Service
- `get_workflow_info()`: Returns detailed graph configuration
- `update_workflow_configuration()`: Updates graph settings
- Node-specific configuration based on node types

### API Endpoints

#### GET `/workflows/langchain/{workflow_id}/info`
Returns detailed LangChain workflow configuration including:
- Basic workflow information
- LLM configuration
- Default parameters
- Node definitions
- Execution settings

#### GET `/workflows/langgraph/{workflow_id}/info`
Returns detailed LangGraph workflow configuration including:
- Graph structure information
- Node details with inputs/outputs
- Default parameters
- Execution settings

#### PUT `/workflows/langchain/{workflow_id}/configuration`
Updates LangChain workflow configuration.

#### PUT `/workflows/langgraph/{workflow_id}/configuration`
Updates LangGraph workflow configuration.

## Usage

### Accessing Configuration

1. **From Workflow Management**: Click the settings icon on any workflow card
2. **Direct URL**: Navigate to `/workflow-configuration?id={workflow_id}&type={langchain|langgraph}`
3. **Test Page**: Use `/workflow-configuration-test` to create test workflows

### Configuration Workflow

1. **View Mode**: Initially displays current configuration in read-only mode
2. **Edit Mode**: Click "Edit Configuration" to enable editing
3. **Make Changes**: Modify parameters, settings, or add new items
4. **Save**: Click "Save" to persist changes
5. **Export**: Use the Preview tab to export configuration

### Parameter Types

- **String**: Text input with optional validation
- **Number**: Numeric input with min/max constraints
- **Boolean**: Toggle switch
- **Select**: Dropdown with predefined options
- **Array**: Comma-separated values
- **Object**: JSON object input

## Default Configurations

### LangChain Workflows

#### Position Analysis Workflow
```json
{
  "parameters": [
    {
      "name": "positions_data",
      "type": "array",
      "required": true,
      "description": "Array of position data to analyze"
    },
    {
      "name": "analysis_depth",
      "type": "select",
      "options": ["basic", "detailed", "comprehensive"],
      "default": "basic"
    }
  ],
  "execution_settings": {
    "maxConcurrentExecutions": 5,
    "executionTimeoutMinutes": 30
  }
}
```

#### Trade Validation Workflow
```json
{
  "parameters": [
    {
      "name": "trade_data",
      "type": "object",
      "required": true,
      "description": "Trade data to validate"
    },
    {
      "name": "strict_mode",
      "type": "boolean",
      "default": false
    }
  ]
}
```

### LangGraph Workflows

#### FIBO Mapping Workflow
```json
{
  "parameters": [
    {
      "name": "positions_data",
      "type": "array",
      "required": true
    },
    {
      "name": "fibo_version",
      "type": "select",
      "options": ["latest", "2023", "2022", "2021"],
      "default": "latest"
    }
  ],
  "execution_settings": {
    "maxConcurrentExecutions": 3,
    "executionTimeoutMinutes": 60
  }
}
```

## Security Features

- **Access Control**: Configurable user restrictions
- **Audit Logging**: Track configuration changes
- **Encryption**: Optional data encryption
- **Validation**: Parameter type and value validation

## Performance Features

- **Caching**: Configurable result caching
- **Parallel Processing**: Enable parallel node execution
- **Optimization**: Automatic workflow optimization
- **Timeout Management**: Configurable execution timeouts

## Testing

Use the test page at `/workflow-configuration-test` to:
1. Create test LangChain and LangGraph workflows
2. Access configuration screens
3. Test parameter modification
4. Verify save/load functionality

## Future Enhancements

- **Visual Workflow Builder**: Drag-and-drop node configuration
- **Template Library**: Pre-built configuration templates
- **Version Control**: Configuration versioning and rollback
- **Collaboration**: Multi-user configuration editing
- **Monitoring**: Real-time configuration impact monitoring
