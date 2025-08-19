# Legacy database.py - now redirects to new database service
from app.database.database_service import DatabaseService


# For backward compatibility
def get_connection():
    return DatabaseService.get_connection()


def create_tables():
    """Now uses the SQL file migration"""
    DatabaseService.fresh()
