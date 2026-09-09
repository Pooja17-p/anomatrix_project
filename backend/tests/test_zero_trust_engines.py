import sys
import os
import unittest
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geo_helper import calculate_distance, detect_impossible_travel, get_ip_geolocation
from service.anomaly_engine import detect_anomaly
from service.trust_engine import calculate_trust_score
from service.ai_model_service import calculate_ai_anomaly_score, extract_features_from_history

class TestZeroTrustEngines(unittest.TestCase):
    
    def test_haversine_distance(self):
        # Distance from London (51.5074, -0.1278) to Paris (48.8566, 2.3522) is roughly 344 km
        dist = calculate_distance(51.5074, -0.1278, 48.8566, 2.3522)
        self.assertAlmostEqual(dist, 344.0, delta=15.0) # Check within 15km delta
        
    def test_impossible_travel(self):
        # Case 1: Normal travel speed
        last_login = {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "timestamp": (datetime.now() - timedelta(hours=5)).isoformat()
        }
        # London to Paris in 5 hours (~68.8 km/h) -> Not impossible
        is_impossible, speed, distance = detect_impossible_travel(
            last_login, 48.8566, 2.3522, datetime.now()
        )
        self.assertFalse(is_impossible)
        self.assertLess(speed, 100.0)
        
        # Case 2: Impossible speed (London to New York in 10 minutes)
        # London (51.5074, -0.1278) to NY (40.7128, -74.0060) is ~5570 km
        last_login_london = {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()
        }
        is_impossible, speed, distance = detect_impossible_travel(
            last_login_london, 40.7128, -74.0060, datetime.now()
        )
        self.assertTrue(is_impossible)
        self.assertGreater(speed, 30000.0) # Speed should be around 33,000 km/h
        
    def test_get_ip_geolocation(self):
        # Test mock loop lookup
        geo = get_ip_geolocation("london")
        self.assertEqual(geo.get("city"), "London")
        self.assertEqual(geo.get("country"), "United Kingdom")
        self.assertEqual(geo.get("lat"), 51.5074)
        
        # Test default loopback / dynamic resolution
        geo_local = get_ip_geolocation("127.0.0.1")
        self.assertIsNotNone(geo_local.get("city"))
        
    def test_ai_model_scoring(self):
        # Mock historical records: 5 normal logins around 9 AM in Paris
        history = []
        base_time = datetime(2026, 7, 10, 9, 0)
        hours_offsets = [0, 1, -1, 0, 2]
        for i in range(5):
            history.append({
                "device_id": "trusted_device_123",
                "country": "France",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timestamp": (base_time + timedelta(days=i, hours=hours_offsets[i])).isoformat()
            })




            
        # Extract features check
        features = extract_features_from_history(history, "France", "trusted_device_123")
        self.assertEqual(features.shape, (5, 4))
        
        # Test case A: Normal login attempt (same device, same country, same time)
        # login_hour=9, known_device=1.0, country_match=1.0, travel_speed=0.0
        score_normal = calculate_ai_anomaly_score(
            "testuser",
            [9.0, 1.0, 1.0, 0.0],
            history,
            "France",
            "trusted_device_123"
        )
        # Should have low/0 anomaly score
        self.assertLess(score_normal, 35)

        
        # Test case B: Anomalous login attempt (unknown device, different country, high speed)
        # login_hour=2 (unusual hour), known_device=0.0, country_match=0.0, travel_speed=1500.0
        score_anomaly = calculate_ai_anomaly_score(
            "testuser",
            [2.0, 0.0, 0.0, 1500.0],
            history,
            "France",
            "trusted_device_123"
        )
        # Should have elevated anomaly score
        self.assertGreater(score_anomaly, 40)

if __name__ == "__main__":
    unittest.main()
