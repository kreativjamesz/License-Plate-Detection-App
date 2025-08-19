import bcrypt
from app.database.database_service import DatabaseService


class UserSeeder:
    @staticmethod
    def run():
        """Seed default users"""
        conn = DatabaseService.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if users already exist
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count > 0:
                print("👥 Users already exist, skipping seeding...")
                return
            
            # Default users data
            users = [
                {
                    'username': 'admin',
                    'password': 'admin123',
                    'role': 'admin'
                },
                {
                    'username': 'teacher1',
                    'password': 'teacher123',
                    'role': 'teacher'
                },
                {
                    'username': 'staff1',
                    'password': 'staff123',
                    'role': 'staff'
                }
            ]
            
            # Insert users
            for user in users:
                # Hash password
                password_hash = bcrypt.hashpw(
                    user['password'].encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    (user['username'], password_hash, user['role'])
                )
                print(f"👤 Created user: {user['username']} ({user['role']})")
            
            conn.commit()
            print("✅ User seeding completed!")
            
        except Exception as e:
            print(f"❌ User seeding error: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
