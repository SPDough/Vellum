#!/usr/bin/env python3
"""
Seed script for populating the Neo4j knowledge graph with sample data.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.neo4j_service import neo4j_service
from app.models.knowledge_graph import EntityType, RelationshipType
from app.core.config import get_settings


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
            "status": "ACTIVE"
        },
        {
            "id": "acc_fixed_income_fund",
            "name": "Fixed Income Fund",
            "account_number": "FIF001",
            "account_type": "CUSTODY",
            "base_currency": "USD",
            "custodian_id": "bny_mellon_001",
            "status": "ACTIVE"
        },
        {
            "id": "acc_emerging_markets",
            "name": "Emerging Markets Fund",
            "account_number": "EMF001",
            "account_type": "CUSTODY",
            "base_currency": "USD",
            "custodian_id": "state_street_001",
            "status": "ACTIVE"
        }
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
            "country": "US"
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
            "country": "US"
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
            "country": "US"
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
            "country": "US"
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
            "country": "US"
        }
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
            "status": "ACTIVE"
        },
        {
            "id": "bny_mellon_001",
            "name": "BNY Mellon",
            "custodian_type": "GLOBAL",
            "primary_currency": "USD",
            "services": ["custody", "asset_servicing", "treasury_services"],
            "aum_billions": 2600.0,
            "status": "ACTIVE"
        }
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
            "unrealized_pnl": 50000.0
        },
        {
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_googl",
            "quantity": 3000,
            "market_value": 420000.0,
            "book_cost": 410000.0,
            "unrealized_pnl": 10000.0
        },
        {
            "account_id": "acc_global_equity_fund",
            "security_id": "sec_msft",
            "quantity": 5000,
            "market_value": 1750000.0,
            "book_cost": 1700000.0,
            "unrealized_pnl": 50000.0
        },
        {
            "account_id": "acc_emerging_markets",
            "security_id": "sec_tsla",
            "quantity": 2000,
            "market_value": 480000.0,
            "book_cost": 500000.0,
            "unrealized_pnl": -20000.0
        },
        {
            "account_id": "acc_fixed_income_fund",
            "security_id": "sec_us_treasury_10y",
            "quantity": 1000000,  # Par value
            "market_value": 980000.0,
            "book_cost": 1000000.0,
            "unrealized_pnl": -20000.0
        }
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
                "percentage": round((position["market_value"] / 5000000.0) * 100, 2)  # Assuming total portfolio value
            }
        )
        print(f"Created position: {position['account_id']} -> {position['security_id']}")


async def seed_account_custodian_relationships():
    """Create relationships between accounts and custodians."""
    relationships = [
        ("acc_global_equity_fund", "state_street_001"),
        ("acc_emerging_markets", "state_street_001"),
        ("acc_fixed_income_fund", "bny_mellon_001")
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
                "status": "active"
            }
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
            "status": "SETTLED"
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
            "status": "SETTLED"
        }
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
            properties={"trade_type": "equity"}
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
                "price": trade["price"]
            }
        )
        
        print(f"Created trade: {trade['name']}")


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