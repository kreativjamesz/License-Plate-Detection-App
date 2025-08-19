#!/usr/bin/env python3
"""
Add test license plate to database
Usage: python add_test_plate.py
"""

from app.services.license_plate_service import LicensePlateService

def main():
    print("🚗 Adding test license plate...")
    
    try:
        service = LicensePlateService()
        
        # Add your license plate
        plate_id = service.add_detection(
            plate_text="518UOZ",
            confidence=0.98,
            location="Test Camera",
            coordinates=(145, 190, 125, 42)  # (x, y, width, height)
        )
        
        if plate_id > 0:
            print(f"✅ Successfully added license plate 518UOZ with ID: {plate_id}")
            
            # Show current stats
            stats = service.get_plates_count()
            print(f"📊 Current database stats: {stats}")
            
            # Show recent plates
            plates = service.get_plates_for_table()[:5]
            print("\n📋 Recent plates:")
            for plate in plates:
                print(f"   • {plate[1]} - {plate[5]} ({plate[2]} {plate[3]})")
                
        else:
            print("❌ Failed to add license plate")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        print("\n💡 Make sure MySQL is running and database is set up!")
        print("   Run: python migrate.py fresh")

if __name__ == "__main__":
    main()
