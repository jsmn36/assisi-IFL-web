import requests
import json

base_url = "http://localhost:8000/cm/admin/mappings"

payload = {
    "channel": "booking_com",
    "property_id": "00000000-0000-0000-0000-000000000001",
    "room_type_id": 1,
    "channel_room_id": "EXT-5541",
}

print("Creating mapping...")
response = requests.post(base_url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

print("\nFetching mappings...")
response = requests.get(base_url)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Extract mapping string
if response.status_code == 200 and len(response.json()) > 0:
    mapping_id = response.json()[-1]["mapping_id"]

    print(f"\nDeleting mapping {mapping_id}...")
    del_res = requests.delete(f"{base_url}/{mapping_id}")
    print(f"Status: {del_res.status_code}")
    print(f"Response: {del_res.text}")
