import requests
import math
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

MOCK_GEO_DB = {
    "london": {"status": "success", "country": "United Kingdom", "city": "London", "lat": 51.5074, "lon": -0.1278, "region": "Greater London", "state": "Greater London", "isp": "Mock Telecom"},
    "tokyo": {"status": "success", "country": "Japan", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503, "region": "Kanto", "state": "Kanto", "isp": "Mock NTT"},
    "newyork": {"status": "success", "country": "United States", "city": "New York", "lat": 40.7128, "lon": -74.0060, "region": "New York", "state": "New York", "isp": "Mock Verizon"},
    "paris": {"status": "success", "country": "France", "city": "Paris", "lat": 48.8566, "lon": 2.3522, "region": "Ile-de-France", "state": "Ile-de-France", "isp": "Mock Orange"},
    "delhi": {"status": "success", "country": "India", "city": "Delhi", "lat": 28.6139, "lon": 77.2090, "region": "Delhi", "state": "Delhi", "isp": "Mock Airtel"},
    "sydney": {"status": "success", "country": "Australia", "city": "Sydney", "lat": -33.8688, "lon": 151.2093, "region": "New South Wales", "state": "New South Wales", "isp": "Mock Telstra"}
}

def is_private_ip(ip_str):
    """
    Checks if an IP address string is loopback or private/local RFC1918 address.
    """
    if not ip_str:
        return True
    ip_s = str(ip_str).strip().lower()
    if ip_s in ("127.0.0.1", "::1", "localhost", "0.0.0.0"):
        return True
    if ip_s.startswith("192.168.") or ip_s.startswith("10.") or ip_s.startswith("169.254."):
        return True
    if ip_s.startswith("172."):
        parts = ip_s.split(".")
        if len(parts) >= 2 and parts[1].isdigit():
            val = int(parts[1])
            if 16 <= val <= 31:
                return True
    return False

def get_client_ip(flask_req=None):
    """
    Extracts real client IP address from Flask request headers or remote_addr.
    Handles X-Forwarded-For safely by returning first non-private IP.
    """
    if not flask_req:
        return "127.0.0.1"

    xfwd = flask_req.headers.get("X-Forwarded-For")
    if xfwd:
        ips = [ip.strip() for ip in xfwd.split(",") if ip.strip()]
        for ip in ips:
            if not is_private_ip(ip):
                return ip
        if ips:
            return ips[0]

    xreal = flask_req.headers.get("X-Real-IP")
    if xreal and xreal.strip():
        return xreal.strip()

    return flask_req.remote_addr or "127.0.0.1"

def get_public_ip():
    """
    Attempts to discover public IP of local development environment via external IP lookup service.
    Used when client and server run on localhost (127.0.0.1).
    """
    endpoints = [
        "https://api.ipify.org?format=json",
        "http://ip-api.com/json/",
        "https://ifconfig.me/ip"
    ]
    for url in endpoints:
        try:
            res = requests.get(url, timeout=2.0)
            if res.status_code == 200:
                if "json" in url or res.headers.get("content-type", "").startswith("application/json"):
                    data = res.json()
                    ip = data.get("ip") or data.get("query")
                    if ip and not is_private_ip(ip):
                        return str(ip).strip()
                else:
                    ip = res.text.strip()
                    if ip and not is_private_ip(ip):
                        return ip
        except Exception:
            continue
    return None

def get_ip_geolocation(ip=None):
    """
    Looks up country, region/state, city, latitude, longitude, and ISP of an IP address.
    If ip is private/local or omitted, resolves external public IP for local dev environment.
    """
    target_ip = str(ip).strip() if ip else ""
    local_ip = target_ip if (target_ip and is_private_ip(target_ip)) else None

    # Check mock keyword DB for testing location anomalies
    if target_ip.lower() in MOCK_GEO_DB:
        geo = MOCK_GEO_DB[target_ip.lower()].copy()
        geo["ip_address"] = target_ip
        geo["state"] = geo.get("region") or geo.get("state") or ""
        geo["region"] = geo.get("region") or geo.get("state") or ""
        geo["isp"] = geo.get("isp") or "Mock ISP"
        geo["location_string"] = f"{geo.get('city', '')}, {geo.get('country', '')}".strip(", ")
        return geo

    # If target_ip is empty or private, resolve external public IP
    if not target_ip or is_private_ip(target_ip):
        pub_ip = get_public_ip()
        if pub_ip:
            target_ip = pub_ip
            if not local_ip:
                local_ip = ip or "127.0.0.1"
        else:
            display_ip = target_ip if target_ip else "127.0.0.1"
            return {
                "status": "fail",
                "ip_address": display_ip,
                "local_ip": local_ip or display_ip,
                "city": "Location unavailable",
                "region": "",
                "state": "",
                "country": "",
                "lat": None,
                "lon": None,
                "latitude": None,
                "longitude": None,
                "isp": "Local Network",
                "location_string": "Location unavailable"
            }

    api_key = os.getenv("GEOLOCATION_API_KEY")
    try:
        if api_key:
            url = f"https://pro.ip-api.com/json/{target_ip}?key={api_key}"
        else:
            url = f"http://ip-api.com/json/{target_ip}"

        res = requests.get(url, timeout=2.5)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                city = data.get("city", "Location unavailable")
                region = data.get("regionName") or data.get("region") or ""
                country = data.get("country", "")
                lat = float(data.get("lat", 0.0))
                lon = float(data.get("lon", 0.0))
                isp = data.get("isp") or data.get("org") or "Unknown ISP"

                parts = [p for p in [city, region, country] if p and p != "Location unavailable"]
                loc_str = ", ".join(parts) if parts else "Location unavailable"

                return {
                    "status": "success",
                    "ip_address": target_ip,
                    "local_ip": local_ip,
                    "city": city,
                    "region": region,
                    "state": region,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                    "latitude": lat,
                    "longitude": lon,
                    "isp": isp,
                    "location_string": loc_str
                }
    except Exception as e:
        logger.warning(f"Geolocation lookup failed for IP {target_ip}: {e}")

    return {
        "status": "fail",
        "ip_address": target_ip,
        "local_ip": local_ip,
        "city": "Location unavailable",
        "region": "",
        "state": "",
        "country": "",
        "lat": None,
        "lon": None,
        "latitude": None,
        "longitude": None,
        "isp": "Unknown ISP",
        "location_string": "Location unavailable"
    }

def get_request_client_geo(flask_req):
    """
    Utility function for Flask endpoints to extract real client IP and location details.
    Returns tuple: (ip_address, loc_details)
    """
    client_ip = get_client_ip(flask_req)
    geo = get_ip_geolocation(client_ip)

    ip_address = geo.get("ip_address") or client_ip
    loc_details = {
        "city": geo.get("city", "Location unavailable"),
        "state": geo.get("state") or geo.get("region") or "",
        "region": geo.get("region") or geo.get("state") or "",
        "country": geo.get("country", ""),
        "latitude": geo.get("latitude") or geo.get("lat"),
        "longitude": geo.get("longitude") or geo.get("lon"),
        "isp": geo.get("isp", "Unknown ISP"),
        "local_ip": geo.get("local_ip")
    }
    return ip_address, loc_details

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates geographic distance (in km) between two points using the Haversine formula.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0

    R = 6371.0  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def detect_impossible_travel(last_login_data, current_lat, current_lon, current_time):
    """
    Detects if the speed required to travel from the last login location 
    to the current login location exceeds typical flight velocity (1000 km/h).
    Returns (is_impossible, travel_speed, distance)
    """
    if not last_login_data:
        return False, 0.0, 0.0

    last_lat = last_login_data.get("latitude")
    last_lon = last_login_data.get("longitude")
    last_time = last_login_data.get("timestamp")

    if last_lat is None or last_lon is None or last_time is None:
        return False, 0.0, 0.0

    # Ensure last_time is datetime
    if isinstance(last_time, str):
        try:
            # Parse ISO format timestamp
            last_time = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
        except Exception:
            return False, 0.0, 0.0

    # Ensure both are offset-aware or both are offset-naive
    if current_time.tzinfo is not None and last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=current_time.tzinfo)
    elif current_time.tzinfo is None and last_time.tzinfo is not None:
        last_time = last_time.replace(tzinfo=None)

    distance = calculate_distance(last_lat, last_lon, current_lat, current_lon)
    time_diff_hours = (current_time - last_time).total_seconds() / 3600.0

    if time_diff_hours <= 0.0:
        # Same moment login but distance is greater than 1 km
        if distance > 1.0:
            return True, 9999.0, distance
        return False, 0.0, distance

    speed_kmh = distance / time_diff_hours

    # Flag speed above 1000 km/h (commercial flight speed limit)
    if speed_kmh > 1000.0:
        return True, speed_kmh, distance

    return False, speed_kmh, distance
