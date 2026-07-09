#!/usr/bin/env python
"""Test API IA LogeCiv sans authentification"""

import sys
import requests
import json

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("TEST API PUBLIC IA LOGECIV")
print("=" * 60)

# Test 1: Chat (public)
print("\n1. Chat IA (PUBLIC)")
try:
    response = requests.post(
        f"{BASE_URL}/ia/chat/",
        json={"message": "Je cherche un appartement a Cocody"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Reponse: {data.get('reponse', 'N/A')[:100]}...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 2: Recherche (public)
print("\n2. Recherche IA (PUBLIC)")
try:
    response = requests.post(
        f"{BASE_URL}/ia/recommendation/",
        json={"ville": "Cocody", "budget_max": 500000}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Type: {data.get('type')}")
        print(f"Resultats: {len(data.get('resultats', []))} biens")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 3: Budget advisory (public)
print("\n3. Conseil Budget (PUBLIC)")
try:
    response = requests.post(
        f"{BASE_URL}/ia/budget-advisory/",
        json={"budget": 150000}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        villes = data.get('villes_recommandees', [])
        if villes:
            print(f"Villes recommandees: {', '.join([v['ville'] for v in villes[:3]])}")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 4: Recommandations list (public)
print("\n4. Liste Recommandations (PUBLIC)")
try:
    response = requests.get(f"{BASE_URL}/ia/recommendations/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Recommendations count: {len(data)}")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "=" * 60)
print("✅ Tests complets!")
print("=" * 60)
