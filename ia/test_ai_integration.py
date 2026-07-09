import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from biens.models import Bien
from .services import (
    call_ai,
    search_biens_intelligente,
    chat_immobilier,
    verify_document,
    recommande_villes_par_budget,
    extract_search_criteria,
    normalize_text,
)


class AIIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        Bien.objects.create(
            titre="Appartement Cocody",
            prix=500000,
            ville="Cocody",
            localisation="Riviera Palmeraie",
            type="appartement",
            transaction_type="location",
            statut="disponible",
            nombre_chambres=2,
            nombre_salles_bain=1,
            superficie=80,
            meuble=True,
            parking=True,
            securite=True,
        )

        Bien.objects.create(
            titre="Maison Bingerville",
            prix=250000,
            ville="Bingerville",
            localisation="Zone résidentielle",
            type="maison",
            transaction_type="location",
            statut="disponible",
            nombre_chambres=3,
            nombre_salles_bain=2,
            superficie=150,
            meuble=False,
            parking=True,
            securite=True,
        )

    def test_normalize_text(self):
        self.assertEqual(normalize_text("Cocody"), "cocody")
        self.assertEqual(normalize_text("RIVIERA PALMERAIE"), "riviera palmeraie")
        self.assertEqual(normalize_text(""), "")

    def test_extract_budget_from_text(self):
        criteria = extract_search_criteria({"texte": "Je cherche un appartement pour 500000 FCFA"})
        self.assertEqual(criteria.get("budget_max"), 500000)

    def test_search_criteria_extraction(self):
        data = {
            "ville": "Cocody",
            "type_bien": "appartement",
            "budget_max": 600000,
            "nombre_chambres": 2,
        }
        criteria = extract_search_criteria(data)
        self.assertEqual(criteria["ville"], "Cocody")
        self.assertEqual(criteria["type_bien"], "appartement")
        self.assertEqual(criteria["budget_max"], 600000)
        self.assertEqual(criteria["nombre_chambres"], 2)

    def test_search_biens_results(self):
        data = {
            "ville": "Cocody",
            "type_bien": "appartement",
            "budget_max": 600000,
        }
        result = search_biens_intelligente(data)
        self.assertIn("type", result)
        self.assertIn("resultats", result)
        self.assertIn("analyse_ia", result)

    def test_search_biens_suggestions(self):
        data = {
            "ville": "Yamoussoukro",
            "budget_max": 150000,
        }
        result = search_biens_intelligente(data)
        self.assertEqual(result["type"], "suggestions")
        self.assertGreater(len(result["suggestions"]), 0)

    def test_chat_immobilier(self):
        message = "Je cherche un appartement à Cocody avec 600000 FCFA"
        result = chat_immobilier(message)
        self.assertIn("message", result)
        self.assertIn("reponse", result)
        self.assertIn("criteres", result)

    def test_budget_advisory(self):
        recommendations = recommande_villes_par_budget(100000)
        self.assertIsInstance(recommendations, list)
        if recommendations:
            self.assertIn("ville", recommendations[0])
            self.assertIn("prix_range", recommendations[0])

    def test_document_verification_local(self):
        result = verify_document("cni", "https://example.com/cni.jpg")
        self.assertIn("verdict", result)
        self.assertIn("confidence", result)
        self.assertIn("message", result)
        self.assertIn("details", result)

    def test_recommendation_api_endpoint(self):
        data = {
            "ville": "Cocody",
            "type_bien": "appartement",
            "budget_max": 600000,
        }
        response = self.client.post("/api/ia/recommendation/", data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("type", result)

    def test_chat_api_endpoint(self):
        data = {"message": "Je cherche un appartement pas cher"}
        response = self.client.post("/api/ia/chat/", data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("reponse", result)

    def test_verify_document_api_endpoint(self):
        data = {
            "document_url": "https://example.com/cni.jpg",
            "document_type": "cni",
        }
        response = self.client.post("/api/ia/verify-document/", data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("verdict", result)

    def test_budget_advisory_api_endpoint(self):
        data = {"budget": 100000}
        response = self.client.post("/api/ia/budget-advisory/", data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("budget", result)
        self.assertIn("villes_recommandees", result)
