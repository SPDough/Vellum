# Custodian LangGraph Workflows

## Overview

The Custodian LangGraph module provides intelligent data analysis workflows for custodian banking data. It combines LangGraph's workflow orchestration capabilities with LLM-powered analysis to extract insights from custodian APIs and answer natural language questions about the data.

## Features

- **Automated Data Extraction**: Pull data from custodian APIs using configurable endpoints
- **Intelligent Analysis**: Use LLMs to analyze custodian data and answer questions
- **Workflow Management**: Create, execute, and manage custodian analysis workflows
- **Multi-Custodian Support**: Support for multiple custodian providers (State Street, BNY Mellon, JPMorgan, etc.)
- **Real-time Processing**: Process data in real-time with pandas DataFrames
- **Natural Language Queries**: Ask questions about your custodian data in plain English

## Architecture

### Components

1. **CustodianLangGraphService**: Main service for managing workflows
2. **DataExtractionNode**: LangGraph node for extracting data from APIs
3. **DataAnalysisNode**: LangGraph node for LLM-powered data analysis
4. **API Endpoints**: RESTful API for workflow management
5. **Frontend Interface**: React-based UI for workflow management

### Workflow Flow

```
User Question → Data Extraction → DataFrame Creation → LLM Analysis → Results
```

## Backend Implementation

### Service Structure

```python
# Main service
CustodianLangGraphService
├── create_custodian_analysis_workflow()
├── execute_custodian_analysis()
├── list_available_custodians()
└── add_custodian_config()

# LangGraph Nodes
DataExtractionNode
├── __call__() - Extract data from custodian API
└── Convert to pandas DataFrame

DataAnalysisNode
├── __call__() - Analyze data using LLM
└── Generate insights and answers
```

### API Endpoints

- `POST /api/custodian-langgraph/workflows/create` - Create new workflow
- `POST /api/custodian-langgraph/workflows/{id}/execute` - Execute workflow
- `GET /api/custodian-langgraph/custodians` - List available custodians
- `POST /api/custodian-langgraph/custodians` - Add custodian configuration
- `GET /api/custodian-langgraph/workflows` - List workflows
- `DELETE /api/custodian-langgraph/workflows/{id}` - Delete workflow

## Frontend Implementation

### Components

- **CustodianLangGraph**: Main page component with tabs for workflows, custodians, and results
- **Workflow Management**: Create, execute, and delete workflows
- **Custodian Configuration**: Add and manage custodian API configurations
- **Analysis Results**: View and explore analysis results with expandable sections

### Features

- **Tabbed Interface**: Organized workflow management, custodian configuration, and results viewing
- **Real-time Updates**: Live status updates and execution progress
- **Data Visualization**: Sample data tables and analysis summaries
- **Error Handling**: Comprehensive error handling and user feedback

## Usage

### 1. Adding a Custodian Configuration

```typescript
// Frontend
const newCustodian = {
  name: "My Custodian",
  base_url: "https://api.mycustodian.com/v1",
  auth_type: "bearer",
  api_key: "your-api-key"
};

await custodianLangGraphService.addCustodianConfig(newCustodian);
```

### 2. Creating a Workflow

```typescript
// Frontend
const workflow = await custodianLangGraphService.createWorkflow(
  "My Custodian",
  "optional-api-key"
);
```

### 3. Executing Analysis

```typescript
// Frontend
const analysisRequest = {
  endpoint: "/positions",
  params: { account: "ACC123" },
  user_question: "What are the top holdings by market value?"
};

const result = await custodianLangGraphService.executeAnalysis(
  workflowId,
  analysisRequest
);
```

### 4. Backend API Usage

```python
# Python
from app.services.custodian_langgraph_service import get_custodian_langgraph_service

service = get_custodian_langgraph_service()

# Create workflow
workflow_id = await service.create_custodian_analysis_workflow(
    custodian_name="state_street",
    api_key="your-api-key"
)

# Execute analysis
result = await service.execute_custodian_analysis(
    workflow_id=workflow_id,
    endpoint="/positions",
    params={"account": "ACC123"},
    user_question="Analyze the portfolio risk exposure"
)
```

## Configuration

### Environment Variables

```bash
# Required for LLM analysis
OPENAI_API_KEY=your-openai-api-key

# Optional: LangSmith tracing
LANGSMITH_API_KEY=your-langsmith-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=otomeshon
```

### Default Custodian Configurations

The service comes with pre-configured support for:

- **State Street**: `https://api.statestreet.com/v1`
- **BNY Mellon**: `https://api.bnymellon.com/v1`
- **JPMorgan**: `https://api.jpmorgan.com/v1`

### Custom Custodian Setup

```python
service = CustodianLangGraphService()

# Add custom custodian
service.add_custodian_config(
    name="custom_custodian",
    base_url="https://api.customcustodian.com/v1",
    auth_type="bearer",  # or "api_key", "oauth"
    api_key="your-api-key"
)
```

## Data Flow

### 1. Data Extraction

```python
# DataExtractionNode processes:
endpoint = "/positions"  # API endpoint
params = {"account": "ACC123"}  # Query parameters

# Makes HTTP request to custodian API
response = await client.get(f"{base_url}{endpoint}", params=params)

# Converts response to pandas DataFrame
df = pd.DataFrame(response.json())
```

### 2. Data Analysis

```python
# DataAnalysisNode processes:
data_summary = f"""
Data Summary:
- Shape: {df.shape}
- Columns: {df.columns.tolist()}
- Sample Data: {df.head().to_string()}
"""

# LLM analysis
messages = [
    SystemMessage(content="You are a financial data analyst..."),
    HumanMessage(content=f"Data: {data_summary}\nQuestion: {user_question}")
]

response = await llm.ainvoke(messages)
```

## Example Queries

### Portfolio Analysis

- "What are the top 5 holdings by market value?"
- "Calculate the total portfolio value by sector"
- "Which positions have the highest risk exposure?"
- "Show me the performance of technology stocks"

### Risk Analysis

- "Identify any concentration risks in the portfolio"
- "Calculate the portfolio's sector diversification"
- "Which positions have the highest volatility?"

### Compliance Analysis

- "Check for any regulatory compliance issues"
- "Identify any restricted securities"
- "Verify position limits are within guidelines"

## Error Handling

### Common Issues

1. **API Connection Errors**: Network timeouts, authentication failures
2. **Data Format Issues**: Unexpected API response formats
3. **LLM Errors**: OpenAI API rate limits, model availability
4. **Workflow Errors**: Invalid workflow configurations

### Error Recovery

- Automatic retry logic for transient failures
- Graceful degradation when LLM services are unavailable
- Detailed error logging and user feedback
- Fallback to basic data extraction without analysis

## Testing

### Running Tests

```bash
# Test the service
python test_custodian_langgraph.py

# Test API endpoints (requires running server)
curl http://localhost:8000/api/custodian-langgraph/custodians
```

### Test Coverage

- Service initialization and configuration
- Workflow creation and execution
- Data extraction and analysis nodes
- API endpoint functionality
- Error handling scenarios

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Process multiple accounts in a single workflow
2. **Caching**: Cache frequently accessed custodian data
3. **Parallel Execution**: Run multiple workflows concurrently
4. **Data Filtering**: Use API parameters to limit data size

### Monitoring

- Execution time tracking
- Success/failure rates
- API response times
- LLM token usage

## Security

### API Key Management

- Secure storage of custodian API keys
- Environment variable configuration
- Optional key rotation support

### Data Privacy

- No persistent storage of sensitive custodian data
- Secure transmission of API credentials
- Audit logging of data access

## Future Enhancements

### Planned Features

1. **Advanced Analytics**: Statistical analysis and trend detection
2. **Custom Models**: Fine-tuned models for specific custodian data
3. **Real-time Streaming**: WebSocket-based real-time data updates
4. **Multi-language Support**: Support for non-English queries
5. **Integration APIs**: Connect with other financial systems

### Extensibility

The modular design allows for easy extension:

- Custom analysis nodes
- Additional custodian providers
- Specialized data processing
- Integration with external analytics tools

## Troubleshooting

### Common Problems

1. **Workflow Creation Fails**
   - Check custodian configuration
   - Verify API credentials
   - Ensure network connectivity

2. **Analysis Returns Errors**
   - Verify OpenAI API key
   - Check data format compatibility
   - Review LLM model availability

3. **Frontend Issues**
   - Check API endpoint availability
   - Verify CORS configuration
   - Review browser console for errors

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.services.custodian_langgraph_service').setLevel(logging.DEBUG)
```

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review error logs
3. Test with the provided test script
4. Contact the development team

---

*This module provides powerful capabilities for custodian data analysis while maintaining security and performance standards required for financial applications.*
