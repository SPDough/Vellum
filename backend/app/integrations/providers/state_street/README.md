# State Street Provider Scaffold

This is the first concrete provider built on Vellum's generalized integration architecture.

## Current state
- Provider scaffold exists
- Generic tool interfaces exist
- Initial custody-domain mappings are defined
- State Street mappings now align to Vellum's contract registry
- Spreadsheet-derived field aliases have been incorporated into the first mapping pass
- Live API connectivity is intentionally not enabled yet

## First planned live tools
- `get_positions`
- `get_cash_activity`
- `get_trade_status`

## Spreadsheet-derived source material used
- API Listing
- Consumption Mart Dictionary

## Still needed before live enablement
- auth flow confirmation
- required request parameter documentation
- pagination details
- sample responses
- rate limit handling details
