#!/usr/bin/env python3
"""
Database migration utilities for Otomeshon Banking Platform
"""

import asyncio
import sys
import os
from pathlib import Path
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from sqlalchemy import create_engine, text

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings


class MigrationManager:
    """Manage database migrations for banking compliance"""
    
    def __init__(self):
        self.settings = get_settings()
        self.alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        
        # Override the database URL in alembic config
        self.alembic_cfg.set_main_option("sqlalchemy.url", str(self.settings.database_url))
    
    def create_migration(self, message: str, autogenerate: bool = True):
        """Create a new migration"""
        print(f"📝 Creating migration: {message}")
        
        try:
            if autogenerate:
                command.revision(
                    self.alembic_cfg, 
                    message=message, 
                    autogenerate=True
                )
            else:
                command.revision(self.alembic_cfg, message=message)
                
            print("✅ Migration created successfully!")
            
        except Exception as e:
            print(f"❌ Failed to create migration: {e}")
            sys.exit(1)
    
    def upgrade_database(self, revision: str = "head"):
        """Upgrade database to specified revision"""
        print(f"⬆️  Upgrading database to: {revision}")
        
        try:
            command.upgrade(self.alembic_cfg, revision)
            print("✅ Database upgraded successfully!")
            
        except Exception as e:
            print(f"❌ Failed to upgrade database: {e}")
            sys.exit(1)
    
    def downgrade_database(self, revision: str):
        """Downgrade database to specified revision"""
        print(f"⬇️  Downgrading database to: {revision}")
        
        # Banking compliance warning
        print("⚠️  WARNING: Downgrading in production environments may violate")
        print("   banking regulations regarding data retention and audit trails.")
        
        confirm = input("Continue? (yes/no): ").lower().strip()
        if confirm != "yes":
            print("Operation cancelled.")
            return
        
        try:
            command.downgrade(self.alembic_cfg, revision)
            print("✅ Database downgraded successfully!")
            
        except Exception as e:
            print(f"❌ Failed to downgrade database: {e}")
            sys.exit(1)
    
    def show_current_revision(self):
        """Show current database revision"""
        try:
            current = command.current(self.alembic_cfg)
            print(f"📍 Current revision: {current}")
            
        except Exception as e:
            print(f"❌ Failed to get current revision: {e}")
    
    def show_migration_history(self):
        """Show migration history"""
        try:
            command.history(self.alembic_cfg, verbose=True)
            
        except Exception as e:
            print(f"❌ Failed to get migration history: {e}")
    
    def validate_database_schema(self):
        """Validate current database schema against models"""
        print("🔍 Validating database schema...")
        
        try:
            # Check if database is up to date
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            head_revision = script_dir.get_current_head()
            
            engine = create_engine(str(self.settings.database_url))
            
            with engine.connect() as conn:
                context = EnvironmentContext(
                    self.alembic_cfg,
                    script_dir,
                    fn=lambda rev, context: None
                )
                
                context.configure(connection=conn)
                current_rev = context.get_current_revision()
                
                if current_rev == head_revision:
                    print("✅ Database schema is up to date!")
                else:
                    print(f"⚠️  Database schema is out of date.")
                    print(f"   Current: {current_rev}")
                    print(f"   Latest:  {head_revision}")
                    print("   Run 'upgrade' to update the schema.")
        
        except Exception as e:
            print(f"❌ Failed to validate schema: {e}")
    
    def backup_database(self):
        """Create a database backup before migration"""
        print("💾 Creating database backup...")
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_otomeshon_{timestamp}.sql"
            
            # This is a simplified backup - in production, use proper backup tools
            engine = create_engine(str(self.settings.database_url))
            
            with engine.connect() as conn:
                # Get all table names
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname IN ('public', 'audit')
                """))
                
                tables = [row[0] for row in result]
                
                print(f"📊 Found {len(tables)} tables to backup")
                print(f"💾 Backup file: {backup_file}")
                print("⚠️  Note: Use pg_dump for production backups")
                
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
    
    def check_migration_safety(self):
        """Check if pending migrations are safe for production"""
        print("🛡️  Checking migration safety...")
        
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            head_revision = script_dir.get_current_head()
            
            engine = create_engine(str(self.settings.database_url))
            
            with engine.connect() as conn:
                context = EnvironmentContext(
                    self.alembic_cfg,
                    script_dir,
                    fn=lambda rev, context: None
                )
                
                context.configure(connection=conn)
                current_rev = context.get_current_revision()
                
                if current_rev == head_revision:
                    print("✅ No pending migrations")
                    return
                
                # Get pending migrations
                revisions = list(script_dir.walk_revisions(current_rev, head_revision))
                
                print(f"📋 Found {len(revisions)} pending migrations:")
                
                for rev in revisions:
                    print(f"   - {rev.revision}: {rev.doc}")
                    
                    # Check for potentially dangerous operations
                    if rev.module and hasattr(rev.module, 'upgrade'):
                        upgrade_source = str(rev.module.upgrade.__code__.co_consts)
                        
                        if any(dangerous in upgrade_source.lower() for dangerous in 
                               ['drop table', 'drop column', 'alter column']):
                            print(f"     ⚠️  WARNING: Potentially destructive operations detected!")
                
                print("\n🏦 Banking Compliance Notes:")
                print("   - All migrations should be reviewed by compliance team")
                print("   - Audit trail must be maintained during schema changes")
                print("   - Consider maintenance window for large table modifications")
                
        except Exception as e:
            print(f"❌ Failed to check migration safety: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Otomeshon Banking Platform - Migration Utilities")
        print("=" * 50)
        print("Usage: python migration_utils.py <command> [args]")
        print()
        print("Commands:")
        print("  create <message>     Create new migration")
        print("  upgrade [revision]   Upgrade database (default: head)")
        print("  downgrade <revision> Downgrade database")
        print("  current             Show current revision")
        print("  history             Show migration history")
        print("  validate            Validate database schema")
        print("  backup              Create database backup")
        print("  safety-check        Check migration safety")
        sys.exit(1)
    
    manager = MigrationManager()
    command_name = sys.argv[1].lower()
    
    if command_name == "create":
        if len(sys.argv) < 3:
            print("Error: Migration message required")
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        manager.create_migration(message)
        
    elif command_name == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        manager.upgrade_database(revision)
        
    elif command_name == "downgrade":
        if len(sys.argv) < 3:
            print("Error: Target revision required")
            sys.exit(1)
        manager.downgrade_database(sys.argv[2])
        
    elif command_name == "current":
        manager.show_current_revision()
        
    elif command_name == "history":
        manager.show_migration_history()
        
    elif command_name == "validate":
        manager.validate_database_schema()
        
    elif command_name == "backup":
        manager.backup_database()
        
    elif command_name == "safety-check":
        manager.check_migration_safety()
        
    else:
        print(f"Unknown command: {command_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()