import googlemaps
import requests
import json

# Google Maps setup
gmaps = googlemaps.Client(key="AIzaSyB2czIgnvUKOyx77SqK7N3gVN53lYyxGcY")

def get_coordinates(location):
    result = gmaps.geocode(location)
    if result:
        lat = result[0]['geometry']['location']['lat']
        lon = result[0]['geometry']['location']['lng']
        return lat, lon
    return None, None

def get_google_distance(origin_latlon, dest_latlon):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": "AIzaSyB2czIgnvUKOyx77SqK7N3gVN53lYyxGcY",
        "X-Goog-FieldMask": "routes.distanceMeters"
    }
    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": float(origin_latlon.split(",")[0]),
                    "longitude": float(origin_latlon.split(",")[1])
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": float(dest_latlon.split(",")[0]),
                    "longitude": float(dest_latlon.split(",")[1])
                }
            }
        },
        "travelMode": "DRIVE"
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body)).json()
        meters = res['routes'][0]['distanceMeters']
        km = meters / 1000
        return f"{km:.1f} km", km
    except Exception as e:
        print("Distance API error:", e)
        return "N/A", 10.0

def fetch_hospitals(lat, lon):
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": "AIzaSyB2czIgnvUKOyx77SqK7N3gVN53lYyxGcY",
        "X-Goog-FieldMask": "places.displayName,places.location,places.rating,places.userRatingCount,places.id"
    }
    body = {
        "includedTypes": ["hospital"],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": 5000.0
            }
        }
    }
    res = requests.post(url, json=body, headers=headers).json()
    hospitals = []

    for place in res.get("places", []):
        pid = place['id']
        details = requests.get(
            f"https://places.googleapis.com/v1/places/{pid}",
            headers={
                "X-Goog-Api-Key": "AIzaSyB2czIgnvUKOyx77SqK7N3gVN53lYyxGcY",
                "X-Goog-FieldMask": "displayName,location,rating,userRatingCount,reviews"
            }
        ).json()

        review_texts = []
        for r in details.get('reviews', []):
            text_obj = r.get('text', {})
            text = text_obj.get('text', "")
            if text:
                review_texts.append(text)
            if len(review_texts) >= 20:
                break

        dest = f"{details['location']['latitude']},{details['location']['longitude']}"
        dist_text, dist_km = get_google_distance(f"{lat},{lon}", dest)

        hospitals.append({
            "name": details.get('displayName', {}).get('text', 'Unknown'),
            "lat": details.get('location', {}).get('latitude'),
            "lon": details.get('location', {}).get('longitude'),
            "rating": details.get("rating", 0),
            "total_reviews": details.get("userRatingCount", 0),
            "reviews": review_texts,
            "distance_text": dist_text,
            "distance_km": dist_km
        })

    return hospitals