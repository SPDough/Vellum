"""
Database seeding utilities for Otomeshon Banking Platform
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import asyncio
import json

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from app.models.user import User
from app.models.sop import SOPDocument, SOPStep, SOPExecution
from app.models.trade import Trade
from app.core.security import get_password_hash


class BankingSeedData:
    """Banking-specific seed data for development and testing"""
    
    @staticmethod
    def get_sample_users() -> List[Dict[str, Any]]:
        """Generate sample banking users with realistic roles"""
        return [
            {
                "email": "admin@otomeshon.com",
                "username": "admin",
                "full_name": "System Administrator",
                "password": "SecureAdmin123!",
                "role": "admin",
                "department": "IT",
                "position": "System Administrator",
                "is_active": True,
                "is_verified": True,
            },
            {
                "email": "trader1@otomeshon.com", 
                "username": "trader1",
                "full_name": "Alice Johnson",
                "password": "TraderPass123!",
                "role": "trader",
                "department": "Trading",
                "position": "Senior Trader",
                "is_active": True,
                "is_verified": True,
            },
            {
                "email": "compliance@otomeshon.com",
                "username": "compliance",
                "full_name": "Robert Chen",
                "password": "CompliancePass123!",
                "role": "compliance_officer",
                "department": "Compliance",
                "position": "Chief Compliance Officer",
                "is_active": True,
                "is_verified": True,
            },
            {
                "email": "operations@otomeshon.com",
                "username": "operations",
                "full_name": "Maria Rodriguez",
                "password": "OpsPass123!",
                "role": "operations",
                "department": "Operations",
                "position": "Operations Manager",
                "is_active": True,
                "is_verified": True,
            },
            {
                "email": "risk@otomeshon.com",
                "username": "riskmanager",
                "full_name": "David Kim",
                "password": "RiskPass123!",
                "role": "risk_manager",
                "department": "Risk Management",
                "position": "Senior Risk Manager",
                "is_active": True,
                "is_verified": True,
            }
        ]
    
    @staticmethod
    def get_sample_sop_documents() -> List[Dict[str, Any]]:
        """Generate sample SOP documents for banking operations"""
        return [
            {
                "id": str(uuid.uuid4()),
                "title": "Trade Settlement Process",
                "document_number": "SOP-001",
                "version": "1.0",
                "content": """
                # Trade Settlement Standard Operating Procedure
                
                ## Purpose
                This SOP defines the standard process for settling trades in the Otomeshon trading system.
                
                ## Scope
                Applies to all equity trades executed through the platform.
                
                ## Process Steps
                1. Trade Validation
                2. Risk Assessment
                3. Compliance Check
                4. Settlement Instruction Generation
                5. Confirmation and Reporting
                """,
                "summary": "Standard process for trade settlement including validation, risk assessment, and compliance checks.",
                "category": "Trading",
                "subcategory": "Settlement",
                "process_type": "operational",
                "business_area": "Trading",
                "created_by": "admin@otomeshon.com",
                "review_frequency_days": 90,
                "status": "ACTIVE",
                "is_automated": True,
                "automation_percentage": 75.0,
            },
            {
                "id": str(uuid.uuid4()),
                "title": "KYC Customer Onboarding",
                "document_number": "SOP-002", 
                "version": "2.1",
                "content": """
                # Know Your Customer (KYC) Onboarding Procedure
                
                ## Purpose
                Establishes requirements for customer identity verification and due diligence.
                
                ## Regulatory Framework
                - BSA/AML Requirements
                - Patriot Act Compliance
                - FINRA Rules
                
                ## Process Steps
                1. Customer Information Collection
                2. Identity Verification
                3. Risk Assessment
                4. Documentation Review
                5. Approval/Rejection Decision
                6. Ongoing Monitoring Setup
                """,
                "summary": "Customer onboarding process with KYC/AML compliance requirements.",
                "category": "Compliance",
                "subcategory": "KYC/AML",
                "process_type": "regulatory",
                "business_area": "Compliance",
                "created_by": "compliance@otomeshon.com",
                "review_frequency_days": 365,
                "status": "ACTIVE",
                "is_automated": False,
                "automation_percentage": 35.0,
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Daily Risk Monitoring",
                "document_number": "SOP-003",
                "version": "1.5",
                "content": """
                # Daily Risk Monitoring Procedure
                
                ## Purpose
                Defines daily risk monitoring activities and escalation procedures.
                
                ## Key Risk Metrics
                - Portfolio VaR (Value at Risk)
                - Position Concentration
                - Credit Exposure
                - Market Risk Limits
                
                ## Monitoring Schedule
                - Pre-market: 07:00 EST
                - Intraday: Every 30 minutes during trading hours
                - Post-market: 17:00 EST
                """,
                "summary": "Daily risk monitoring procedures and limit management.",
                "category": "Risk Management",
                "subcategory": "Market Risk",
                "process_type": "monitoring",
                "business_area": "Risk Management",
                "created_by": "risk@otomeshon.com",
                "review_frequency_days": 180,
                "status": "ACTIVE",
                "is_automated": True,
                "automation_percentage": 90.0,
            }
        ]
    
    @staticmethod
    def get_sample_sop_steps() -> List[Dict[str, Any]]:
        """Generate sample SOP steps for the documents"""
        sop_docs = BankingSeedData.get_sample_sop_documents()
        trade_settlement_id = sop_docs[0]["id"]
        kyc_onboarding_id = sop_docs[1]["id"]
        
        return [
            # Trade Settlement Steps
            {
                "id": str(uuid.uuid4()),
                "sop_document_id": trade_settlement_id,
                "step_number": 1,
                "step_title": "Trade Validation",
                "step_description": "Validate trade details including symbol, quantity, price, and counterparty information.",
                "is_manual": False,
                "is_automated": True,
                "is_decision_point": False,
                "estimated_duration_minutes": 2,
                "automation_tool": "TradeValidator",
                "automation_confidence": 95.0,
            },
            {
                "id": str(uuid.uuid4()),
                "sop_document_id": trade_settlement_id,
                "step_number": 2,
                "step_title": "Risk Assessment",
                "step_description": "Calculate position risk, check limits, and assess portfolio impact.",
                "is_manual": False,
                "is_automated": True,
                "is_decision_point": True,
                "estimated_duration_minutes": 5,
                "automation_tool": "RiskEngine",
                "automation_confidence": 88.0,
            },
            {
                "id": str(uuid.uuid4()),
                "sop_document_id": trade_settlement_id,
                "step_number": 3,
                "step_title": "Compliance Check",
                "step_description": "Verify compliance with trading rules, regulations, and internal policies.",
                "is_manual": True,
                "is_automated": False,
                "is_decision_point": True,
                "estimated_duration_minutes": 10,
                "automation_confidence": 60.0,
            },
            # KYC Steps
            {
                "id": str(uuid.uuid4()),
                "sop_document_id": kyc_onboarding_id,
                "step_number": 1,
                "step_title": "Customer Information Collection",
                "step_description": "Collect customer personal information, financial details, and identification documents.",
                "is_manual": True,
                "is_automated": False,
                "is_decision_point": False,
                "estimated_duration_minutes": 30,
                "automation_confidence": 20.0,
            },
            {
                "id": str(uuid.uuid4()),
                "sop_document_id": kyc_onboarding_id,
                "step_number": 2,
                "step_title": "Identity Verification",
                "step_description": "Verify customer identity through document verification and database checks.",
                "is_manual": False,
                "is_automated": True,
                "is_decision_point": False,
                "estimated_duration_minutes": 15,
                "automation_tool": "IDVerifyPro",
                "automation_confidence": 85.0,
            }
        ]
    
    @staticmethod
    def get_sample_trades() -> List[Dict[str, Any]]:
        """Generate sample trades for testing"""
        base_date = date.today()
        settlement_date = base_date + timedelta(days=2)  # T+2 settlement
        
        return [
            {
                "id": str(uuid.uuid4()),
                "trade_id": "TRD-001-20241127",
                "external_trade_id": "EXT-12345",
                "symbol": "AAPL",
                "instrument_type": "EQUITY",
                "quantity": 1000,
                "price": Decimal("150.25"),
                "side": "BUY",
                "trade_date": base_date,
                "settlement_date": settlement_date,
                "currency": "USD",
                "counterparty": "Goldman Sachs",
                "account": "ACC-001",
                "portfolio": "GROWTH-01",
                "trader_id": "trader1",
                "status": "SETTLED",
                "settlement_instructions": {
                    "delivery_method": "DTC",
                    "custodian": "State Street",
                    "account_number": "123456789"
                },
                "compliance_checks": {
                    "aml_status": "PASSED",
                    "position_limit_check": "PASSED",
                    "trading_halt_check": "PASSED"
                },
                "risk_metrics": {
                    "var_impact": 2500.00,
                    "concentration_risk": "LOW",
                    "credit_exposure": 150250.00
                }
            },
            {
                "id": str(uuid.uuid4()),
                "trade_id": "TRD-002-20241127",
                "external_trade_id": "EXT-12346",
                "symbol": "MSFT",
                "instrument_type": "EQUITY",
                "quantity": 500,
                "price": Decimal("280.75"),
                "side": "SELL",
                "trade_date": base_date,
                "settlement_date": settlement_date,
                "currency": "USD",
                "counterparty": "Morgan Stanley",
                "account": "ACC-002",
                "portfolio": "VALUE-01",
                "trader_id": "trader1",
                "status": "PENDING",
                "settlement_instructions": {
                    "delivery_method": "DTC",
                    "custodian": "BNY Mellon",
                    "account_number": "987654321"
                },
                "risk_metrics": {
                    "var_impact": -1500.00,
                    "concentration_risk": "MEDIUM",
                    "credit_exposure": -140375.00
                }
            }
        ]


class DatabaseSeeder:
    """Main seeder class for populating the database"""
    
    def __init__(self):
        self.seed_data = BankingSeedData()
    
    async def seed_users(self, session: AsyncSession) -> None:
        """Seed user data"""
        users_data = self.seed_data.get_sample_users()
        
        for user_data in users_data:
            # Hash the password
            hashed_password = get_password_hash(user_data.pop("password"))
            
            user = User(
                **user_data,
                hashed_password=hashed_password
            )
            session.add(user)
        
        await session.commit()
        print(f"✓ Seeded {len(users_data)} users")
    
    async def seed_sop_documents(self, session: AsyncSession) -> None:
        """Seed SOP documents and steps"""
        sop_docs_data = self.seed_data.get_sample_sop_documents()
        sop_steps_data = self.seed_data.get_sample_sop_steps()
        
        # Create SOP documents
        for doc_data in sop_docs_data:
            sop_doc = SOPDocument(**doc_data)
            session.add(sop_doc)
        
        await session.commit()
        
        # Create SOP steps
        for step_data in sop_steps_data:
            sop_step = SOPStep(**step_data)
            session.add(sop_step)
        
        await session.commit()
        print(f"✓ Seeded {len(sop_docs_data)} SOP documents with {len(sop_steps_data)} steps")
    
    async def seed_trades(self, session: AsyncSession) -> None:
        """Seed sample trades"""
        trades_data = self.seed_data.get_sample_trades()
        
        for trade_data in trades_data:
            trade = Trade(**trade_data)
            session.add(trade)
        
        await session.commit()
        print(f"✓ Seeded {len(trades_data)} trades")
    
    async def seed_all(self, session: AsyncSession) -> None:
        """Seed all data"""
        print("🌱 Starting database seeding...")
        
        try:
            await self.seed_users(session)
            await self.seed_sop_documents(session)
            await self.seed_trades(session)
            
            print("✅ Database seeding completed successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during seeding: {e}")
            raise
    
    async def clear_all_data(self, session: AsyncSession) -> None:
        """Clear all seeded data (for testing)"""
        print("🧹 Clearing all seeded data...")
        
        try:
            # Clear in reverse order of dependencies
            await session.execute("DELETE FROM trades")
            await session.execute("DELETE FROM sop_steps")
            await session.execute("DELETE FROM sop_executions") 
            await session.execute("DELETE FROM sop_documents")
            await session.execute("DELETE FROM users")
            await session.execute("DELETE FROM audit.audit_log")
            
            await session.commit()
            print("✅ All data cleared successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during data clearing: {e}")
            raise


async def main():
    """Main seeding function"""
    seeder = DatabaseSeeder()
    
    async for session in get_async_session():
        await seeder.seed_all(session)
        break


if __name__ == "__main__":
    asyncio.run(main())