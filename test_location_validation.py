from app import create_app, db, Location, haversine_distance

def test_location_validation():
    app = create_app()
    with app.app_context():
        # Create test client
        client = app.test_client()
        
        # Add test location if it doesn't exist
        if not Location.query.filter_by(name="Presidency University, Bengaluru").first():
            location = Location(
                name="Presidency University, Bengaluru",
                latitude=12.9338,
                longitude=77.6929,
                radius=500
            )
            db.session.add(location)
            db.session.commit()
            print("✅ Added test location: Presidency University, Bengaluru")
        
        # Test 1: Inside 500m radius (should pass)
        print("\n=== Test 1: Inside 500m radius (should pass) ===")
        test_coords_inside = (12.9338, 77.6929)  # Same as center
        test_validation(*test_coords_inside, True)
        
        # Test 2: Outside 500m radius (should fail)
        print("\n=== Test 2: Outside 500m radius (should fail) ===")
        test_coords_outside = (12.9420, 77.6929)  # ~900m away
        test_validation(*test_coords_outside, False)

def test_validation(lat, lng, expected_result):
    app = create_app()
    with app.app_context():
        # Find nearest location
        nearest = None
        min_dist = float('inf')
        for loc in Location.query.all():
            d = haversine_distance(lat, lng, loc.latitude, loc.longitude)
            if d < min_dist:
                min_dist = d
                nearest = loc
        
        if nearest:
            print(f"Nearest location: {nearest.name} (ID: {nearest.id})")
            print(f"Coordinates: {lat}, {lng}")
            print(f"Distance: {min_dist:.2f}m (Radius: {nearest.radius}m)")
            is_within_radius = min_dist <= nearest.radius
            print(f"Within radius: {'✅' if is_within_radius else '❌'}")
            test_passed = is_within_radius == expected_result
            print(f"Test {'PASSED' if test_passed else 'FAILED'}")
            if not test_passed:
                print(f"Expected: {'within' if expected_result else 'outside'} radius")
        else:
            print("❌ No locations found in the database")
        print("-" * 50)

if __name__ == '__main__':
    test_location_validation()
