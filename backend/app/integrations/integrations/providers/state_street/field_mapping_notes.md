# State Street Field Mapping Notes

Seeded from spreadsheet analysis:
- API Listing
- Consumption Mart Dictionary
- additional spreadsheet extracts provided in chat

## Confirmed/strong signals from spreadsheet set

### API families observed
- custody-position / quantity positions
- custody-cash / activities
- custody-trade / status
- custody-penalty / daily penalties
- custody-penalty / monthly penalties
- custody tax reclaim
- fund accounting NAV
- entity-level positions
- lot-level positions
- security-level positions
- transactions

## Current mapping priorities
1. Position
2. Cash Activity
3. Trade Status
4. Cash Balance
5. Penalty / Tax Reclaim

## Cash Activity dictionary signals
Examples observed from dictionary materials:
- `createDatetime`
- `debitCreditCode`
- `currencyCodeLocal`
- `ddaId`
- `entityId`
- `iban`
- `cashNetAmount`
- `transactionType`
- `transactionId`
- `transactionIdClient`
- `transactionStatusCode`
- `transactionStatusDescription`

### Current Vellum contract mapping intent
- `transactionId` -> `CashActivity.payload.transaction_id`
- `transactionType` -> `CashActivity.payload.transaction_type`
- `transactionStatusCode` -> `CashActivity.payload.transaction_status`
- `cashNetAmount` -> `CashActivity.payload.amount`
- `currencyCodeLocal` -> `CashActivity.payload.currency`
- `createDatetime` -> `CashActivity.payload.effective_date`
- `debitCreditCode` -> `CashActivity.payload.debit_credit_indicator`
- `ddaId` -> `CashActivity.payload.account_id`
- `entityId` -> `CashActivity.payload.entity_id`

## Position signals
Spreadsheet/API listing confirms a custody position API and fund accounting position APIs.
Likely/expected source fields include:
- `entityId`
- `accountId`
- `securityId`
- `instrumentId`
- `quantity`
- `currencyCode` / `currency`
- `positionDate`

### Current Vellum contract mapping intent
- `entityId` -> `Position.payload.entity_id`
- `accountId` -> `Position.payload.account_id`
- `securityId` -> `Position.payload.security_id`
- `instrumentId` -> `Position.payload.instrument_id`
- `quantity` -> `Position.payload.quantity`
- `currencyCode` -> `Position.payload.currency`
- `positionDate` -> `Position.payload.position_date`

## Trade Status signals
Spreadsheet/API listing confirms a custody trade status API.
Likely/expected source fields include:
- `tradeId` or `transactionId`
- `clientTradeId` or `transactionIdClient`
- `settlementStatus`
- `settlementDate`
- `tradeDate`
- `securityId` / `instrumentId`
- `quantity`
- `price`
- `currencyCode`
- `counterpartyId`
- `statusReason` / `transactionStatusDescription`

### Current Vellum contract mapping intent
- `tradeId` / `transactionId` -> `TradeStatus.payload.trade_id`
- `clientTradeId` / `transactionIdClient` -> `TradeStatus.payload.client_trade_id`
- `settlementStatus` -> `TradeStatus.payload.settlement_status`
- `tradeDate` -> `TradeStatus.payload.trade_date`
- `settlementDate` -> `TradeStatus.payload.settlement_date`
- `securityId` -> `TradeStatus.payload.security_id`
- `quantity` -> `TradeStatus.payload.quantity`
- `price` -> `TradeStatus.payload.price`
- `currencyCode` -> `TradeStatus.payload.currency`

## Penalty / tax reclaim notes
APIs exist and should likely become later contract candidates after the first custody oversight wave.
These are especially relevant to the product wedge around finding custodian errors and reducing reimbursement exposure.

## Next enrichment steps
- inspect more spreadsheet rows per API family when needed
- capture field aliases and required filters/params
- add `cash-balance`, `penalty`, and `tax-reclaim` contract candidates
- introduce source alias dictionaries per contract
