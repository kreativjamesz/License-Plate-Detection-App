"""
Simple database connection test
Run this before launching the app to verify database connectivity
"""

from app.services.data_service import DataService, test_connection
from app.services.students_service import StudentsService
from app.services.attendance_service import AttendanceService

def main():
    print("🔍 Testing database connection...")
    print("=" * 50)
    
    # Test basic connection
    print("1. Testing basic database connection...")
    if test_connection():
        print("   ✅ Database connection successful!")
    else:
        print("   ❌ Database connection failed!")
        print("   💡 Make sure MySQL is running and database exists")
        return
    
    # Test students service
    print("\n2. Testing students service...")
    try:
        students_count = StudentsService.get_students_count()
        print(f"   ✅ Students count: {students_count}")
        
        # Get first few students
        students = StudentsService.get_all_students()
        print(f"   ✅ Found {len(students)} students")
        if students:
            print(f"   📋 First student: {students[0].get('student_number')} - {students[0].get('first_name')} {students[0].get('last_name')}")
    except Exception as e:
        print(f"   ❌ Students service error: {e}")
    
    # Test attendance service
    print("\n3. Testing attendance service...")
    try:
        attendance_stats = AttendanceService.get_attendance_stats()
        print(f"   ✅ Attendance stats: {attendance_stats}")
        
        # Get recent attendance
        attendance = AttendanceService.get_all_attendance(5)
        print(f"   ✅ Found {len(attendance)} recent attendance records")
        if attendance:
            print(f"   📋 Latest attendance: {attendance[0].get('student_number')} - {attendance[0].get('status')}")
    except Exception as e:
        print(f"   ❌ Attendance service error: {e}")
    
    print("\n🎉 Database test completed!")
    print("If all tests passed, your app should work properly.")
    print("If any test failed, fix the database connection first.")

if __name__ == "__main__":
    main()
