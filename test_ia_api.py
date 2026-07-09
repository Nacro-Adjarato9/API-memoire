#!/usr/bin/env python
"""
Script de test pour l'API IA LogeCiv
Teste tous les endpoints et la logique IA
"""

import os
import sys
import json
import requests
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("🧪 TEST API IA LOGECIV")
print("=" * 60)

def test_endpoint(method, endpoint, data, expected_status=200):
    url = f"{BASE_URL}{endpoint}"
    print(f"\n📌 Test: {method} {endpoint}")
    print(f"   Data: {json.dumps(data, ensure_ascii=False)[:100]}...")

    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)

        print(f"   Status: {response.status_code} {'✅' if response.status_code == expected_status else '❌'}")

        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {json.dumps(result, ensure_ascii=False)[:150]}...")
            return True, result
        else:
            print(f"   Error: {response.text[:150]}...")
            return False, None
    except Exception as e:
        print(f"   Error: {str(e)}")
        return False, None


print("\n" + "=" * 60)
print("1️⃣ TEST RECHERCHE INTELLIGENTE")
print("=" * 60)

search_data = {
    "ville": "Cocody",
    "type_bien": "appartement",
    "budget_max": 500000,
    "nombre_chambres": 2,
}
success, result = test_endpoint("POST", "/ia/recommendation/", search_data)


print("\n" + "=" * 60)
print("2️⃣ TEST CHAT IMMOBILIER")
print("=" * 60)

chat_data = {
    "message": "Je cherche un appartement pas cher à Cocody avec 300000 FCFA"
}
success, result = test_endpoint("POST", "/ia/chat/", chat_data)


print("\n" + "=" * 60)
print("3️⃣ TEST CONSEIL BUDGÉTAIRE")
print("=" * 60)

budget_data = {"budget": 150000}
success, result = test_endpoint("POST", "/ia/budget-advisory/", budget_data)


print("\n" + "=" * 60)
print("4️⃣ TEST VÉRIFICATION DE DOCUMENTS")
print("=" * 60)

verify_data = {
    "document_url": "https://example.com/cni.jpg",
    "document_type": "cni",
}
success, result = test_endpoint("POST", "/ia/verify-document/", verify_data)


print("\n" + "=" * 60)
print("5️⃣ TEST RECHERCHE AVEC TEXTE LIBRE")
print("=" * 60)

free_text_data = {
    "texte": "Je veux trouver une maison 3 chambres à Bingerville avec 400000 FCFA"
}
success, result = test_endpoint("POST", "/ia/recherche/rechercher/", free_text_data)


print("\n" + "=" * 60)
print("✅ TESTS TERMINÉS")
print("=" * 60)
print("\n💡 Assurez-vous que:")
print("   ✅ Le serveur Django tourne sur http://localhost:8000")
print("   ✅ La clé API Groq est configurée dans .env")
print("   ✅ Les données de test existent en base")
print("\n🚀 Pour démarrer le serveur:")
print("   python manage.py runserver")
