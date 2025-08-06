#!/usr/bin/env python3
"""
Shared test utilities for Otomeshon test files.
This module provides common data creation functions and test runners
to eliminate code duplication across test files.
"""

import asyncio
import traceback
from datetime import datetime, date
from typing import Dict, Any, Callable, Awaitable


def create_sample_trade_data(
    trade_id: str = "TRADE_001",
    security_id: str = "AAPL",
    quantity: int = 1000,
    price: float = 150.50,
    trade_value: float = 150500.00,
    currency: str = "USD"
) -> Dict[str, Any]:
    """Create sample trade data for testing"""
    return {
        "tradeId": trade_id,
        "tradeType": "EQUITY",
        "counterpartyId": "CLIENT_001",
        "securityId": security_id,
        "quantity": quantity,
        "price": price,
        "tradeValue": trade_value,
        "currency": currency,
        "tradeDate": date.today().isoformat(),
        "settlementDate": date.today().isoformat(),
        "status": "PENDING",
        "portfolio": "PORTFOLIO_001",
        "custodyAccount": "CUSTODY_001"
    }


def create_sample_portfolio_data(
    portfolio_id: str = "PORTFOLIO_001",
    total_exposure: float = 5000000.00,
    exposure_limit: float = 10000000.00
) -> Dict[str, Any]:
    """Create sample portfolio data for testing"""
    return {
        "portfolioId": portfolio_id,
        "totalExposure": total_exposure,
        "exposureLimit": exposure_limit,
        "concentrationLimit": 1000000.00,
        "availableCash": 2000000.00,
        "securityExposures": {
            "AAPL": 500000.00,
            "MSFT": 300000.00,
            "GOOGL": 400000.00
        }
    }


def create_sample_client_data(
    client_id: str = "CLIENT_001",
    kyc_status: str = "APPROVED",
    aml_risk_rating: str = "LOW"
) -> Dict[str, Any]:
    """Create sample client data for testing"""
    return {
        "clientId": client_id,
        "kycStatus": kyc_status,
        "amlRiskRating": aml_risk_rating,
        "creditRating": "A",
        "lastReviewDate": "2024-01-15",
        "countryCode": "US",
        "approvedInstruments": ["EQUITY", "BOND", "FX"],
        "tradingLimits": {
            "dailyLimit": 1000000.00,
            "positionLimit": 5000000.00
        }
    }


def create_sample_settlement_data(
    settlement_id: str = "SETTLE_001",
    trade_id: str = "TRADE_001"
) -> Dict[str, Any]:
    """Create sample settlement data for testing"""
    return {
        "settlementId": settlement_id,
        "tradeId": trade_id,
        "cashRequired": 150500.00,
        "securitiesRequired": 1000,
        "settlementAgent": "DTC",
        "instructionStatus": "PENDING",
        "cutoffTime": "2024-07-20T16:00:00"
    }


def print_test_header(title: str, subtitle: str = "") -> None:
    """Print standardized test section header"""
    separator_length = max(len(title), len(subtitle), 50)
    print(f"\n{title}")
    print("=" * separator_length)
    if subtitle:
        print(subtitle)
        print()


def print_test_completion(system_name: str) -> None:
    """Print standardized test completion message"""
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print(f"🚀 {system_name} is ready for custodian banking operations")
    print("=" * 70)


async def run_test_with_error_handling(
    test_name: str,
    test_func: Callable[[], Awaitable[None]]
) -> None:
    """Run a test function with standardized error handling"""
    print_test_header(f"🧪 {test_name}")
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        await test_func()
        print_test_completion(test_name)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        traceback.print_exc()


def run_async_test_main(test_func: Callable[[], Awaitable[None]]) -> None:
    """Standard main function for async test scripts"""
    asyncio.run(test_func())