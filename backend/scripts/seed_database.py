#!/usr/bin/env python3
"""
Database seeding script for Otomeshon Banking Platform
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.seeds import DatabaseSeeder
from app.core.database import get_async_session


async def seed_database():
    """Seed the database with initial data"""
    print("🚀 Otomeshon Banking Platform - Database Seeding")
    print("=" * 50)
    
    seeder = DatabaseSeeder()
    
    try:
        async for session in get_async_session():
            await seeder.seed_all(session)
            break
            
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        sys.exit(1)


async def clear_database():
    """Clear all seeded data"""
    print("🧹 Clearing database...")
    
    seeder = DatabaseSeeder()
    
    try:
        async for session in get_async_session():
            await seeder.clear_all_data(session)
            break
            
    except Exception as e:
        print(f"❌ Clearing failed: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clear":
            asyncio.run(clear_database())
        elif command == "seed":
            asyncio.run(seed_database())
        else:
            print("Usage: python seed_database.py [seed|clear]")
            sys.exit(1)
    else:
        # Default to seeding
        asyncio.run(seed_database())


if __name__ == "__main__":
    main()