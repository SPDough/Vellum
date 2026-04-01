# Custodian Data Chain Documentation

## Overview

The Custodian Data Chain is a LangChain-based service that provides a unified interface for retrieving and analyzing data from custodian MCP servers. This service integrates with the existing MCP infrastructure to provide intelligent data access and analysis capabilities.

## Features

- **Data Retrieval**: Pull data from custodian MCP servers with validation and transformation
- **Data Analysis**: Analyze custodian data using LangChain for insights and recommendations
- **Data Validation**: Automatic validation and quality assessment of retrieved data
- **Data Transformation**: Transform data into standardized formats
- **Integration**: Seamless integration with existing MCP service infrastructure
- **Mock Support**: Mock data support for testing and development

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Custodian Data Chain                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Data Retrieval│  │   Data Analysis │  │   Data       │ │
│  │      Chain      │  │      Chain      │  │ Validation   │ │
│  │                 │  │                 │  │   Chain      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│           │                     │                    │       │
│           ▼                     ▼                    ▼       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              MCP Service Integration                    │ │
│  │  • HTTP/WebSocket MCP Clients                          │ │
│  │  • Server Management                                   │ │
│  │  • Health Monitoring                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Custodian MCP Servers                      │ │
│  │  • State Street                                        │ │
│  │  • BNY Mellon                                          │ │
│  │  • Bloomberg                                           │ │
│  │  • Refinitiv                                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. CustodianDataChain

The main service class that orchestrates data retrieval and analysis.

**Key Methods:**
- `retrieve_custodian_data()`: Retrieve data from custodian MCP servers
- `analyze_custodian_data()`: Analyze custodian data using LangChain
- `_validate_custodian_data()`: Validate retrieved data
- `_extract_insights_from_analysis()`: Extract insights from analysis results

### 2. LangChain Integration

The service uses several LangChain chains:

- **Data Retrieval Chain**: Handles data retrieval from MCP servers
- **Data Analysis Chain**: Performs analysis on retrieved data
- **Data Validation Chain**: Validates data quality and completeness
- **Data Transformation Chain**: Transforms data into standardized formats

### 3. MCP Service Integration

Integrates with the existing MCP service infrastructure:

- **Server Management**: List, register, and manage custodian servers
- **Connection Testing**: Test connections to custodian servers
- **Tool Execution**: Execute tools on custodian servers
- **Health Monitoring**: Monitor server health and performance

## API Endpoints

### Data Retrieval

#### POST `/api/v1/custodian-data/retrieve`

Retrieve data from a custodian MCP server.

**Request Body:**
```json
{
  "custodian_id": "state_street",
  "data_type": "positions",
  "parameters": {
    "portfolio": "PORT_001",
    "as_of_date": "2024-01-15"
  },
  "filters": {
    "currency": "USD"
  },
  "limit": 1000,
  "include_metadata": true
}
```

**Response:**
```json
{
  "success": true,
  "custodian_id": "state_street",
  "data_type": "positions",
  "records_count": 150,
  "data": [
    {
      "position_id": "POS_001",
      "security_id": "AAPL",
      "quantity": 1000,
      "market_value": 185000.00,
      "currency": "USD",
      "custody_account": "ACC_001",
      "portfolio": "PORT_001",
      "as_of_date": "2024-01-15",
      "unrealized_pnl": 5000.00,
      "_validation_timestamp": "2024-01-15T10:30:00Z",
      "_data_type": "positions"
    }
  ],
  "metadata": {
    "custodian_id": "state_street",
    "data_type": "positions",
    "retrieval_time": "2024-01-15T10:30:00Z",
    "execution_time_seconds": 1.25,
    "records_count": 150,
    "available_tools": ["positions", "transactions", "cash_balances"],
    "parameters_used": {
      "portfolio": "PORT_001",
      "as_of_date": "2024-01-15",
      "limit": 1000
    }
  },
  "execution_time_seconds": 1.25
}
```

### Data Analysis

#### POST `/api/v1/custodian-data/analyze`

Analyze custodian data using LangChain.

**Request Body:**
```json
{
  "custodian_data": [
    {
      "position_id": "POS_001",
      "security_id": "AAPL",
      "quantity": 1000,
      "market_value": 185000.00,
      "currency": "USD"
    }
  ],
  "analysis_type": "risk_assessment",
  "analysis_parameters": {
    "risk_threshold": 0.1
  },
  "include_recommendations": true
}
```

**Response:**
```json
{
  "success": true,
  "analysis_type": "risk_assessment",
  "insights": [
    {
      "type": "data_overview",
      "title": "Data Overview",
      "description": "Analyzed 150 records with 8 columns",
      "value": 150,
      "severity": "info"
    },
    {
      "type": "risk_assessment",
      "title": "Concentration Risk",
      "description": "AAPL represents 45% of portfolio value",
      "value": 0.45,
      "severity": "warning"
    }
  ],
  "recommendations": [
    {
      "type": "risk_management",
      "title": "Diversification",
      "description": "Consider reducing concentration in AAPL",
      "priority": "high",
      "action": "rebalance_portfolio"
    }
  ],
  "summary": {
    "total_records": 150,
    "total_columns": 8,
    "insights_count": 2,
    "recommendations_count": 1,
    "analysis_timestamp": "2024-01-15T10:30:00Z",
    "data_quality_score": 0.95
  },
  "execution_time_seconds": 2.15
}
```

### Combined Operations

#### POST `/api/v1/custodian-data/retrieve-and-analyze`

Retrieve and analyze custodian data in a single operation.

**Request Body:**
```json
{
  "custodian_id": "state_street",
  "data_type": "positions",
  "parameters": {
    "portfolio": "PORT_001"
  },
  "limit": 1000,
  "include_metadata": true
}
```

**Query Parameters:**
- `analysis_type`: Type of analysis to perform (default: "general")
- `analysis_parameters`: Parameters for the analysis (default: {})
- `include_recommendations`: Whether to include recommendations (default: true)

### Server Management

#### GET `/api/v1/custodian-data/custodians`

List available custodian MCP servers.

**Response:**
```json
[
  {
    "id": "state_street",
    "name": "State Street Global Services",
    "type": "custodian",
    "status": "connected",
    "capabilities": ["positions", "transactions", "cash_balances"],
    "enabled": true,
    "last_health_check": "2024-01-15T10:25:00Z"
  }
]
```

#### GET `/api/v1/custodian-data/custodians/{custodian_id}/capabilities`

Get capabilities of a specific custodian MCP server.

#### GET `/api/v1/custodian-data/custodians/{custodian_id}/health`

Get health status of a specific custodian MCP server.

### Reference Data

#### GET `/api/v1/custodian-data/data-types`

Get list of available data types.

#### GET `/api/v1/custodian-data/analysis-types`

Get list of available analysis types.

## Usage Examples

### Python Usage

```python
import asyncio
from app.services.custodian_data_chain import (
    CustodianDataChain,
    CustodianDataRequest,
    CustodianAnalysisRequest,
    get_custodian_data_chain,
)

async def example_usage():
    # Get the custodian data chain
    custodian_chain = await get_custodian_data_chain()
    
    # Retrieve data
    retrieval_request = CustodianDataRequest(
        custodian_id="state_street",
        data_type="positions",
        parameters={"portfolio": "PORT_001"},
        limit=100,
        include_metadata=True,
    )
    
    retrieval_response = await custodian_chain.retrieve_custodian_data(retrieval_request)
    
    if retrieval_response.success:
        print(f"Retrieved {retrieval_response.records_count} records")
        
        # Analyze the data
        analysis_request = CustodianAnalysisRequest(
            custodian_data=retrieval_response.data,
            analysis_type="risk_assessment",
            analysis_parameters={"risk_threshold": 0.1},
            include_recommendations=True,
        )
        
        analysis_response = await custodian_chain.analyze_custodian_data(analysis_request)
        
        if analysis_response.success:
            print(f"Found {len(analysis_response.insights)} insights")
            print(f"Generated {len(analysis_response.recommendations)} recommendations")

# Run the example
asyncio.run(example_usage())
```

### API Usage

```bash
# Retrieve positions from State Street
curl -X POST "http://localhost:8000/api/v1/custodian-data/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "custodian_id": "state_street",
    "data_type": "positions",
    "parameters": {"portfolio": "PORT_001"},
    "limit": 100
  }'

# Analyze the retrieved data
curl -X POST "http://localhost:8000/api/v1/custodian-data/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "custodian_data": [...],
    "analysis_type": "risk_assessment",
    "include_recommendations": true
  }'

# Combined retrieve and analyze
curl -X POST "http://localhost:8000/api/v1/custodian-data/retrieve-and-analyze?analysis_type=risk_assessment" \
  -H "Content-Type: application/json" \
  -d '{
    "custodian_id": "state_street",
    "data_type": "positions",
    "parameters": {"portfolio": "PORT_001"},
    "limit": 100
  }'
```

## Configuration

### Environment Variables

The service uses the following environment variables:

```bash
# LLM Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# MCP Service Configuration
MCP_SERVICE_URL=http://localhost:8080
MCP_SERVICE_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

### Service Configuration

The service can be configured through the `CustodianDataChain` constructor:

```python
from app.services.custodian_data_chain import CustodianDataChain
from app.services.mcp_service import get_mcp_service

# Get MCP service
mcp_service = await get_mcp_service()

# Create custodian data chain with custom configuration
custodian_chain = CustodianDataChain(
    mcp_service=mcp_service,
    llm=your_custom_llm  # Optional custom LLM
)
```

## Testing

### Running Tests

```bash
# Run the test script
cd backend
python test_custodian_data_chain.py
```

### Test Coverage

The test script covers:

1. **Custodian Listing**: List available custodian servers
2. **Data Retrieval**: Mock data retrieval with validation
3. **Data Analysis**: Analysis of retrieved data
4. **Combined Operations**: Retrieve and analyze in one operation

### Mock Data

The service includes mock data for testing:

- **Positions**: Sample position data with AAPL, MSFT, GOOGL
- **Transactions**: Sample transaction data
- **Cash Balances**: Sample cash balance data

## Error Handling

### Common Errors

1. **Custodian Not Found**: `Custodian server {custodian_id} not found`
2. **Custodian Not Enabled**: `Custodian server {custodian_id} is not enabled`
3. **Connection Failed**: `Cannot connect to custodian server {custodian_id}`
4. **Data Type Not Available**: `Data type {data_type} not available for custodian {custodian_id}`
5. **LLM Not Available**: `No LLM providers available`

### Error Response Format

```json
{
  "success": false,
  "custodian_id": "state_street",
  "data_type": "positions",
  "records_count": 0,
  "data": [],
  "metadata": {},
  "execution_time_seconds": 0.5,
  "error_message": "Custodian server state_street not found"
}
```

## Performance

### Optimization Tips

1. **Use Limits**: Always specify limits for data retrieval
2. **Filter Data**: Use filters to reduce data volume
3. **Batch Operations**: Use combined retrieve-and-analyze for efficiency
4. **Caching**: Implement caching for frequently accessed data
5. **Connection Pooling**: Reuse MCP connections when possible

### Performance Metrics

- **Data Retrieval**: ~1-2 seconds for 1000 records
- **Data Analysis**: ~2-3 seconds for 1000 records
- **Combined Operations**: ~3-5 seconds for 1000 records
- **Connection Testing**: ~0.5 seconds per server

## Security

### Authentication

All API endpoints require authentication:

```bash
# Include authentication header
curl -H "Authorization: Bearer your-token" \
  -X POST "http://localhost:8000/api/v1/custodian-data/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"custodian_id": "state_street", "data_type": "positions"}'
```

### Data Validation

- All input data is validated using Pydantic models
- Data is sanitized before processing
- Sensitive data is not logged
- Error messages don't expose internal details

## Monitoring

### Health Checks

```bash
# Check custodian health
curl "http://localhost:8000/api/v1/custodian-data/custodians/state_street/health"
```

### Metrics

The service provides the following metrics:

- **Execution Time**: Time taken for data retrieval and analysis
- **Success Rate**: Percentage of successful operations
- **Data Quality Score**: Quality assessment of retrieved data
- **Error Rate**: Percentage of failed operations

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Connection Issues**: Check MCP service availability
3. **LLM Issues**: Verify API keys are configured
4. **Data Format Issues**: Check data format compatibility

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python test_custodian_data_chain.py
```

## Future Enhancements

1. **Real-time Data Streaming**: Support for real-time data updates
2. **Advanced Analytics**: More sophisticated analysis algorithms
3. **Data Caching**: Implement caching for improved performance
4. **Batch Processing**: Support for batch operations
5. **Custom Analysis**: Allow custom analysis workflows
6. **Data Export**: Export capabilities for analysis results
7. **Integration**: Integration with other data sources
8. **Machine Learning**: ML-based insights and predictions

## Support

For questions and support:

1. Check the API documentation at `/docs`
2. Review the test script for usage examples
3. Check the logs for error details
4. Contact the development team

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Submit a pull request
