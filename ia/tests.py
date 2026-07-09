from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase

from biens.models import Bien
from ia.services import search_biens_intelligente

User = get_user_model()


class IAServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123!",
        )
        Bien.objects.create(
            titre="Bel appartement",
            description="Appartement moderne proche du centre.",
            prix=150000.00,
            ville="Abidjan",
            localisation="Cocody",
            type="appartement",
            statut="disponible",
            nombre_chambres=3,
            nombre_salons=1,
            nombre_cuisines=1,
            nombre_salles_bain=2,
            superficie=85.00,
            etage=2,
            parking=True,
            proprietaire=self.user,
        )

    @patch("ia.services.call_ai")
    def test_search_biens_intelligente_returns_results_when_match(self, mocked_call_ai):
        mocked_call_ai.return_value = ("Résultats retrouvés.", None)
        response = search_biens_intelligente(
            {
                "texte": "", 
                "ville": "Abidjan", 
                "quartier": "", 
                "commune": "", 
                "type_bien": "appartement", 
                "budget_min": None, 
                "budget_max": 200000, 
                "nombre_chambres": None,
            }
        )

        self.assertEqual(response["type"], "resultats")
        self.assertTrue(response["resultats"])
        self.assertEqual(response["analyse_ia"], "Résultats retrouvés.")

    @patch("ia.services.call_ai")
    def test_search_biens_intelligente_returns_suggestions_when_no_match(self, mocked_call_ai):
        mocked_call_ai.return_value = ("Aucune offre exacte, voici des alternatives.", None)
        response = search_biens_intelligente(
            {
                "texte": "", 
                "ville": "Yamoussoukro", 
                "quartier": "", 
                "commune": "", 
                "type_bien": "villa", 
                "budget_min": None, 
                "budget_max": 1000, 
                "nombre_chambres": None,
            }
        )

        self.assertEqual(response["type"], "suggestions")
        self.assertFalse(response["resultats"])
        self.assertTrue(response["suggestions"])
        self.assertEqual(response["analyse_ia"], "Aucune offre exacte, voici des alternatives.")


class IAViewTests(APITestCase):
    @patch("ia.views._call_grok")
    def test_verifier_document_invalid_json_response_sets_valide_false(self, mocked_call_grok):
        mocked_call_grok.return_value = ("not json", None)
        response = self.client.post(
            "/api/ia/verifier-document/verifier/",
            {"document_url": "https://example.com/doc.pdf", "document_type": "cni"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["valide"])
        self.assertIn("Vérification manuelle recommandée", response.data["message"])
        self.assertEqual(response.data["details"]["type_detecte"], "CNI")
