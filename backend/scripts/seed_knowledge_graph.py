#!/usr/bin/env python3
"""
Seed script for populating the Neo4j knowledge graph with sample data.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_settings
from app.models.knowledge_graph import EntityType, RelationshipType
from app.models.fibo_ontology import (
    FIBOLegalEntity,
    FIBOEquityInstrument,
    FIBOFinancialAccount,
    FIBOPositionHolding,
    FIBOTradeTransaction,
    FIBOHasHoldingRelationship,
    FIBOPlaysRoleRelationship,
)
from app.services.neo4j_service import neo4j_service


async def seed_accounts():
    """Create sample account entities."""
    accounts = [
        {
            "id": "acc_global_equity_fund",
            "name": "Global Equity Fund",
            "account_number": "GEF001",
            "account_type": "CUSTODY",
            "base_currency": "USD",
            "custodian_id": "state_street_001",
            "status": "ACTIVE",
        },
        {
            "id": "acc_fixed_income_fund",
            "name": "Fixed Income Fund",
            "account_number": "FIF001",
            "account_type": "CUSTODY",
            "base_currency": "USD",
            "custodian_id": "bny_mellon_001",
            "status": "ACTIVE",
        },
        {
            "id": "acc_emerging_markets",
            "name": "Emerging Markets Fund",
            "account_number": "EMF001",
            "account_type": "CUSTODY",
            "base_currency": "USD",
            "custodian_id": "state_street_001",
            "status": "ACTIVE",
        },
    ]

    for account in accounts:
        await neo4j_service.create_entity(EntityType.ACCOUNT.value, account)
        print(f"Created account: {account['name']}")


async def seed_securities():
    """Create sample security entities."""
    securities = [
        {
            "id": "sec_aapl",
            "name": "Apple Inc.",
            "symbol": "AAPL",
            "isin": "US0378331005",
            "cusip": "037833100",
            "security_type": "EQUITY",
            "currency": "USD",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "country": "US",
        },
        {
            "id": "sec_googl",
            "name": "Alphabet Inc. Class A",
            "symbol": "GOOGL",
            "isin": "US02079K3059",
            "cusip": "02079K305",
            "security_type": "EQUITY",
            "currency": "USD",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "country": "US",
        },
        {
            "id": "sec_msft",
            "name": "Microsoft Corporation",
            "symbol": "MSFT",
            "isin": "US5949181045",
            "cusip": "594918104",
            "security_type": "EQUITY",
            "currency": "USD",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "country": "US",
        },
        {
            "id": "sec_tsla",
            "name": "Tesla Inc.",
            "symbol": "TSLA",
            "isin": "US88160R1014",
            "cusip": "88160R101",
            "security_type": "EQUITY",
            "currency": "USD",
            "exchange": "NASDAQ",
            "sector": "Automotive",
            "country": "US",
        },
        {
            "id": "sec_us_treasury_10y",
            "name": "US Treasury 10 Year Note",
            "symbol": "UST10Y",
            "isin": "US912828XE41",
            "security_type": "BOND",
            "currency": "USD",
            "exchange": "OTC",
            "sector": "Government",
            "country": "US",
        },
    ]

    for security in securities:
        await neo4j_service.create_entity(EntityType.SECURITY.value, security)
        print(f"Created security: {security['name']}")


async def seed_custodians():
    """Create sample custodian entities."""
    custodians = [
        {
            "id": "state_street_001",
            "name": "State Street Global Services",
            "custodian_type": "GLOBAL",
            "primary_currency": "USD",
            "services": ["custody", "fund_accounting", "performance_measurement"],
            "aum_billions": 4300.0,
            "status": "ACTIVE",
        },
        {
            "id": "bny_mellon_001",
            "name": "BNY Mellon",
            "custodian_type": "GLOBAL",
            "primary_currency": "USD",
            "services": ["custody", "asset_servicing", "treasury_services"],
            "aum_billions": 2600.0,
            "status": "ACTIVE",
        },
    ]

    for custodian in custodians:
        await neo4j_service.create_entity(EntityType.CUSTODIAN.value, custodian)
        print(f"Created custodian: {custodian['name']}")


async def seed_positions():
    """Create sample position relationships."""
    positions = [
        {
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_aapl",
            "quantity": 10000,
            "market_value": 1500000.0,
            "book_cost": 1450000.0,
            "unrealized_pnl": 50000.0,
        },
        {
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_googl",
            "quantity": 3000,
            "market_value": 420000.0,
            "book_cost": 410000.0,
            "unrealized_pnl": 10000.0,
        },
        {
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_msft",
            "quantity": 5000,
            "market_value": 1750000.0,
            "book_cost": 1700000.0,
            "unrealized_pnl": 50000.0,
        },
        {
            "account_id": "acc_emerging_markets",
            "security_id": "sec_tsla",
            "quantity": 2000,
            "market_value": 480000.0,
            "book_cost": 500000.0,
            "unrealized_pnl": -20000.0,
        },
        {
            "account_id": "acc_fixed_income_fund",
            "security_id": "sec_us_treasury_10y",
            "quantity": 1000000,  # Par value
            "market_value": 980000.0,
            "book_cost": 1000000.0,
            "unrealized_pnl": -20000.0,
        },
    ]

    for position in positions:
        await neo4j_service.create_relationship(
            from_entity_type=EntityType.ACCOUNT.value,
            from_entity_id=position["account_id"],
            to_entity_type=EntityType.SECURITY.value,
            to_entity_id=position["security_id"],
            relationship_type=RelationshipType.HOLDS.value,
            properties={
                "quantity": position["quantity"],
                "market_value": position["market_value"],
                "book_cost": position["book_cost"],
                "unrealized_pnl": position["unrealized_pnl"],
                "as_of_date": datetime.utcnow().isoformat(),
                "percentage": round(
                    (position["market_value"] / 5000000.0) * 100, 2
                ),  # Assuming total portfolio value
            },
        )
        print(
            f"Created position: {position['account_id']} -> {position['security_id']}"
        )


async def seed_account_custodian_relationships():
    """Create relationships between accounts and custodians."""
    relationships = [
        ("acc_global_equity_fund", "state_street_001"),
        ("acc_emerging_markets", "state_street_001"),
        ("acc_fixed_income_fund", "bny_mellon_001"),
    ]

    for account_id, custodian_id in relationships:
        await neo4j_service.create_relationship(
            from_entity_type=EntityType.CUSTODIAN.value,
            from_entity_id=custodian_id,
            to_entity_type=EntityType.ACCOUNT.value,
            to_entity_id=account_id,
            relationship_type=RelationshipType.MANAGES.value,
            properties={
                "service_type": "custody",
                "start_date": "2020-01-01",
                "status": "active",
            },
        )
        print(f"Created custody relationship: {custodian_id} -> {account_id}")


async def seed_sample_trades():
    """Create sample trade entities."""
    trades = [
        {
            "id": "trade_001",
            "name": "AAPL Purchase Trade",
            "trade_id": "TRD20241201001",
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_aapl",
            "side": "BUY",
            "quantity": 1000,
            "price": 150.25,
            "gross_amount": 150250.0,
            "net_amount": 150000.0,
            "commission": 25.0,
            "fees": 225.0,
            "currency": "USD",
            "execution_venue": "NASDAQ",
            "status": "SETTLED",
        },
        {
            "id": "trade_002",
            "name": "GOOGL Purchase Trade",
            "trade_id": "TRD20241201002",
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_googl",
            "side": "BUY",
            "quantity": 500,
            "price": 140.50,
            "gross_amount": 70250.0,
            "net_amount": 70000.0,
            "commission": 15.0,
            "fees": 235.0,
            "currency": "USD",
            "execution_venue": "NASDAQ",
            "status": "SETTLED",
        },
    ]

    for trade in trades:
        # Add timestamps
        trade["trade_date"] = datetime.utcnow().isoformat()
        trade["settlement_date"] = datetime.utcnow().isoformat()

        await neo4j_service.create_entity(EntityType.TRADE.value, trade)

        # Create trade relationships
        await neo4j_service.create_relationship(
            from_entity_type=EntityType.ACCOUNT.value,
            from_entity_id=trade["account_id"],
            to_entity_type=EntityType.TRADE.value,
            to_entity_id=trade["id"],
            relationship_type=RelationshipType.EXECUTES.value,
            properties={"trade_type": "equity"},
        )

        await neo4j_service.create_relationship(
            from_entity_type=EntityType.TRADE.value,
            from_entity_id=trade["id"],
            to_entity_type=EntityType.SECURITY.value,
            to_entity_id=trade["security_id"],
            relationship_type=RelationshipType.TRADES.value,
            properties={
                "side": trade["side"],
                "quantity": trade["quantity"],
                "price": trade["price"],
            },
        )

        print(f"Created trade: {trade['name']}")


async def seed_fibo_entities():
    """Seed FIBO ontology entities."""
    print("Seeding FIBO entities...")

    fibo_custodians = [
        FIBOLegalEntity(
            id="fibo-state-street",
            name="State Street Corporation",
            fibo_type="LegalEntity",
            legal_name="State Street Corporation",
            jurisdiction="US-MA",
            lei_code="549300GKFG0RYRRQ1414",
            regulatory_status="ACTIVE",
            business_registry_identifier="042370443",
        ),
        FIBOLegalEntity(
            id="fibo-bny-mellon",
            name="The Bank of New York Mellon Corporation",
            fibo_type="LegalEntity",
            legal_name="The Bank of New York Mellon Corporation",
            jurisdiction="US-NY",
            lei_code="HPFHU0OQ28E4N0NFVK49",
            regulatory_status="ACTIVE",
            business_registry_identifier="042370443",
        ),
    ]

    for custodian in fibo_custodians:
        await neo4j_service.create_entity("FIBOLegalEntity", custodian.dict())
        print(f"Created FIBO custodian: {custodian.name}")

    fibo_accounts = [
        FIBOFinancialAccount(
            id="fibo-account-001",
            name="Institutional Custody Account 001",
            fibo_type="FinancialAccount",
            account_identifier="INST-001-SS",
            account_type="CUSTODY",
            currency="USD",
            account_status="ACTIVE",
            custodian_identifier="fibo-state-street",
        ),
        FIBOFinancialAccount(
            id="fibo-account-002",
            name="Institutional Custody Account 002",
            fibo_type="FinancialAccount",
            account_identifier="INST-002-BNY",
            account_type="CUSTODY",
            currency="USD",
            account_status="ACTIVE",
            custodian_identifier="fibo-bny-mellon",
        ),
    ]

    for account in fibo_accounts:
        await neo4j_service.create_entity("FIBOFinancialAccount", account.dict())
        print(f"Created FIBO account: {account.name}")

    fibo_securities = [
        FIBOEquityInstrument(
            id="fibo-aapl-equity",
            name="Apple Inc. Common Stock",
            fibo_type="EquityInstrument",
            isin="US0378331005",
            cusip="037833100",
            ticker="AAPL",
            exchange="NASDAQ",
            currency="USD",
            issuer_lei="HWUPKR0MPOU8FGXBT394",
            share_class="COMMON",
        ),
        FIBOEquityInstrument(
            id="fibo-msft-equity",
            name="Microsoft Corporation Common Stock",
            fibo_type="EquityInstrument",
            isin="US5949181045",
            cusip="594918104",
            ticker="MSFT",
            exchange="NASDAQ",
            currency="USD",
            issuer_lei="INR2EJN1ERAN0W5ZP974",
            share_class="COMMON",
        ),
    ]

    for security in fibo_securities:
        await neo4j_service.create_entity("FIBOEquityInstrument", security.dict())
        print(f"Created FIBO security: {security.name}")

    fibo_positions = [
        FIBOPositionHolding(
            id="fibo-position-001",
            name="AAPL Position in Account 001",
            fibo_type="PositionHolding",
            account_identifier="fibo-account-001",
            instrument_identifier="fibo-aapl-equity",
            quantity=1000.0,
            market_value=150000.0,
            currency="USD",
            valuation_date="2024-01-15",
            position_type="LONG",
        ),
        FIBOPositionHolding(
            id="fibo-position-002",
            name="MSFT Position in Account 002",
            fibo_type="PositionHolding",
            account_identifier="fibo-account-002",
            instrument_identifier="fibo-msft-equity",
            quantity=500.0,
            market_value=175000.0,
            currency="USD",
            valuation_date="2024-01-15",
            position_type="LONG",
        ),
    ]

    for position in fibo_positions:
        await neo4j_service.create_entity("FIBOPositionHolding", position.dict())
        print(f"Created FIBO position: {position.name}")


async def seed_fibo_relationships():
    """Seed FIBO ontology relationships."""
    print("Seeding FIBO relationships...")

    fibo_relationships = [
        {
            "from_type": "FIBOFinancialAccount",
            "from_id": "fibo-account-001",
            "to_type": "FIBOPositionHolding",
            "to_id": "fibo-position-001",
            "relationship_type": "FIBO_HAS_HOLDING",
            "properties": {
                "relationship_date": "2024-01-15",
                "relationship_status": "ACTIVE",
            },
        },
        {
            "from_type": "FIBOFinancialAccount",
            "from_id": "fibo-account-002",
            "to_type": "FIBOPositionHolding",
            "to_id": "fibo-position-002",
            "relationship_type": "FIBO_HAS_HOLDING",
            "properties": {
                "relationship_date": "2024-01-15",
                "relationship_status": "ACTIVE",
            },
        },
        {
            "from_type": "FIBOLegalEntity",
            "from_id": "fibo-state-street",
            "to_type": "FIBOFinancialAccount",
            "to_id": "fibo-account-001",
            "relationship_type": "FIBO_PLAYS_ROLE",
            "properties": {
                "role_type": "CUSTODIAN",
                "role_start_date": "2020-01-01",
                "role_status": "ACTIVE",
            },
        },
        {
            "from_type": "FIBOLegalEntity",
            "from_id": "fibo-bny-mellon",
            "to_type": "FIBOFinancialAccount",
            "to_id": "fibo-account-002",
            "relationship_type": "FIBO_PLAYS_ROLE",
            "properties": {
                "role_type": "CUSTODIAN",
                "role_start_date": "2020-01-01",
                "role_status": "ACTIVE",
            },
        },
    ]

    for rel in fibo_relationships:
        await neo4j_service.create_relationship(
            rel["from_type"],
            rel["from_id"],
            rel["to_type"],
            rel["to_id"],
            rel["relationship_type"],
            rel["properties"],
        )
        print(f"Created FIBO relationship: {rel['from_id']} -> {rel['to_id']}")


async def main():
    """Main seeding function."""
    print("Starting knowledge graph seeding...")

    try:
        # Initialize Neo4j connection
        await neo4j_service.connect()
        print("Connected to Neo4j")

        # Seed entities
        await seed_custodians()
        await seed_accounts()
        await seed_securities()
        await seed_sample_trades()

        # Seed relationships
        await seed_positions()
        await seed_account_custodian_relationships()
        
        await seed_fibo_entities()
        await seed_fibo_relationships()

        print("\nKnowledge graph seeding completed successfully!")

        # Print summary
        stats = await neo4j_service.get_graph_statistics()
        print(f"\nGraph Statistics:")
        print(f"Total Nodes: {stats.get('total_nodes', 0)}")
        print(f"Total Relationships: {stats.get('total_relationships', 0)}")

    except Exception as e:
        print(f"Error during seeding: {e}")
        raise
    finally:
        await neo4j_service.disconnect()
        print("Disconnected from Neo4j")


if __name__ == "__main__":
    asyncio.run(main())
