import requests, json, os
key = os.getenv('GOOGLE_PAGESPEED_API_KEY')
place_id = 'ChIJKyLjPxw25xIRfDH6wwFBHpA'
print(f"Using Key: {key[:5]}..." if key else "Key is None")
resp = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params={
    'place_id': place_id,
    'fields': 'name,rating,user_ratings_total,formatted_address,formatted_phone_number,website,opening_hours,reviews,photos,types,business_status,url',
    'language': 'it',
    'key': key
}, timeout=15)
data = resp.json()
print(f'Status: {data.get("status")}')
print(json.dumps(data.get('result',{}), indent=2, ensure_ascii=False))
