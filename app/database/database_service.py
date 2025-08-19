import mysql.connector
import os
from app.utils.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


class DatabaseService:
    @staticmethod
    def get_connection(use_db=True):
        """Get MySQL connection, optionally without selecting a database"""
        if use_db:
            return mysql.connector.connect(
                host=DB_HOST, 
                user=DB_USER, 
                password=DB_PASSWORD, 
                database=DB_NAME
            )
        else:
            return mysql.connector.connect(
                host=DB_HOST, 
                user=DB_USER, 
                password=DB_PASSWORD
            )
    
    @staticmethod
    def execute_sql_file(file_path):
        """Execute SQL commands from a file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        # Connect without database first
        conn = DatabaseService.get_connection(use_db=False)
        cursor = conn.cursor()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
                
                # Split by semicolon and execute each statement
                statements = sql_content.split(';')
                
                for statement in statements:
                    statement = statement.strip()
                    if statement:  # Skip empty statements
                        cursor.execute(statement)
                        conn.commit()
            
            print(f"✅ Successfully executed SQL file: {file_path}")
            
        except Exception as e:
            print(f"❌ Error executing SQL file: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def migrate():
        """Run database migrations"""
        sql_file = "db/license_plate_detection.sql"
        DatabaseService.execute_sql_file(sql_file)
        print("🚀 Database migration completed!")
    
    @staticmethod
    def seed():
        """Run database seeders"""
        # Import and run seeders here
        from app.database.seeders.user_seeder import UserSeeder
        
        try:
            UserSeeder.run()
            print("🌱 Database seeding completed!")
        except Exception as e:
            print(f"❌ Seeding error: {e}")
    
    @staticmethod
    def fresh():
        """Drop and recreate database with fresh data"""
        print("🔄 Running fresh migration...")
        DatabaseService.migrate()
        DatabaseService.seed()
        print("✨ Fresh database setup completed!")


# Legacy functions for backward compatibility
def get_connection():
    return DatabaseService.get_connection()

def create_tables():
    """Legacy function - now uses migration"""
    DatabaseService.migrate()
