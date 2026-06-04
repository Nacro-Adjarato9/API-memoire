import json
import os
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient

from biens.models import Bien
from tarifs.models import Tarif
from utilisateurs.token_generator import EmailVerificationTokenGenerator
from django.conf import settings


User = get_user_model()


def as_data(response):
    content_type = response.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            return response.json()
        except Exception:
            return response.content.decode(errors="ignore")
    return response.content.decode(errors="ignore")


def call(client, name, method, path, data=None, format="json"):
    func = getattr(client, method.lower())
    kwargs = {"format": format}
    if data is not None:
        kwargs["data"] = data
    response = func(path, **kwargs)
    return {
        "name": name,
        "method": method.upper(),
        "path": path,
        "status": response.status_code,
        "data": as_data(response),
    }


def main():
    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

    suffix = get_random_string(6).lower()
    email = f"test{suffix}@example.com"
    password = "Testpass123!"
    client = APIClient()
    results = []

    results.append(
        call(
            client,
            "register",
            "POST",
            "/api/auth/register/",
            {
                "email": email,
                "password": password,
                "password2": password,
                "first_name": "Test",
                "last_name": "User",
                "phone": "01020304",
                "user_type": "locataire",
            },
        )
    )

    user = User.objects.get(email=email)
    token = EmailVerificationTokenGenerator.generate_token(user)
    results.append(
        call(
            client,
            "verify_email",
            "POST",
            "/api/auth/verify-email/",
            {"email": email, "token": token},
        )
    )

    login = call(
        client,
        "login",
        "POST",
        "/api/auth/login/",
        {"email": email, "password": password},
    )
    results.append(login)
    access = None
    if isinstance(login["data"], dict):
        access = login["data"].get("access")

    if not access:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        return

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    second_email = f"receiver{suffix}@example.com"
    second_user = User.objects.create_user(
        username=f"receiver{suffix}",
        email=second_email,
        password=password,
    )
    EmailVerificationTokenGenerator.mark_as_verified(second_user)

    results.append(call(client, "me", "GET", "/api/utilisateurs/me/"))
    results.append(call(client, "profile", "GET", "/api/utilisateurs/profile/"))
    results.append(call(client, "list_biens", "GET", "/api/biens/"))
    results.append(call(client, "mes_biens", "GET", "/api/biens/mes_biens/"))
    results.append(call(client, "villes", "GET", "/api/villes/"))
    results.append(call(client, "types_bien", "GET", "/api/types-bien/"))
    results.append(call(client, "search", "GET", "/api/search/?q=Abidjan"))
    results.append(call(client, "stats", "GET", "/api/stats/"))

    bien_payload = {
        "titre": f"Bien test {suffix}",
        "description": "Bien créé pour tester l'API",
        "prix": "150000.00",
        "ville": "Abidjan",
        "localisation": "Cocody",
        "type": "appartement",
        "statut": "disponible",
        "nombre_chambres": 2,
        "nombre_salons": 1,
        "nombre_cuisines": 1,
        "nombre_salles_bain": 1,
        "superficie": "80.00",
        "etage": 2,
        "ascenseur": False,
        "balcon": True,
        "parking": True,
    }
    bien_create = call(client, "create_bien", "POST", "/api/biens/", bien_payload)
    results.append(bien_create)
    bien_id = None
    if isinstance(bien_create["data"], dict):
        bien_id = bien_create["data"].get("id")

    if bien_id:
        results.append(call(client, "detail_bien", "GET", f"/api/biens/{bien_id}/"))
        results.append(call(client, "disponibilites", "GET", f"/api/biens/{bien_id}/disponibilites/"))

        doc_file = SimpleUploadedFile("test.txt", b"document de test", content_type="text/plain")
        results.append(
            call(
                client,
                "create_document",
                "POST",
                "/api/documents/",
                {
                    "titre": f"Doc test {suffix}",
                    "type_document": "autre",
                    "fichier": doc_file,
                    "bien": bien_id,
                },
                format="multipart",
            )
        )

        results.append(
            call(
                client,
                "create_image",
                "POST",
                "/api/images/",
                {
                    "bien": bien_id,
                    "url": "https://example.com/image.jpg",
                },
            )
        )

        results.append(
            call(
                client,
                "create_reservation",
                "POST",
                "/api/reservations/",
                {
                    "bien": bien_id,
                    "date": str(date.today() + timedelta(days=7)),
                    "message": "Je souhaite réserver ce bien.",
                },
            )
        )

        results.append(
            call(
                client,
                "create_avis",
                "POST",
                "/api/avis/",
                {
                    "bien": bien_id,
                    "note": 5,
                    "commentaire": "Très bon bien.",
                },
            )
        )

        results.append(
            call(
                client,
                "create_favori",
                "POST",
                "/api/favoris/",
                {"bien": bien_id},
            )
        )

        results.append(call(client, "favoris_count", "GET", "/api/favoris/count/"))
        results.append(
            call(
                client,
                "favori_toggle",
                "POST",
                "/api/favoris/toggle/",
                {"bien_id": bien_id},
            )
        )

        results.append(
            call(
                client,
                "notification_create",
                "POST",
                "/api/notifications/",
                {"message": "Notification de test"},
            )
        )
        results.append(call(client, "notifications_list", "GET", "/api/notifications/"))
        results.append(call(client, "unread_count", "GET", "/api/notifications/unread_count/"))

    results.append(call(client, "agences_list", "GET", "/api/agences/"))
    results.append(
        call(
            client,
            "agence_create",
            "POST",
            "/api/agences/",
            {"nom": f"Agence test {suffix}", "adresse": "Cocody", "telephone": "01010101"},
        )
    )

    Tarif.objects.get_or_create(
        nom=f"Tarif test {suffix}",
        defaults={
            "description": "Plan de test",
            "prix": "10000.00",
            "duree": "mensuel",
            "features": ["test"],
            "actif": True,
        },
    )
    tarif = Tarif.objects.get(nom=f"Tarif test {suffix}")
    results.append(call(client, "tarifs_list", "GET", "/api/tarifs/"))
    results.append(call(client, "abonnements_list", "GET", "/api/abonnements/"))
    results.append(
        call(
            client,
            "abonnement_create",
            "POST",
            "/api/abonnements/",
            {"tarif": tarif.id, "duree_mois": 1, "auto_renew": False},
        )
    )

    results.append(call(client, "recommendations_list", "GET", "/api/ia/recommendations/"))
    results.append(
        call(
            client,
            "recommendations_create",
            "POST",
            "/api/ia/recommendations/",
            {
                "budget_min": "50000.00",
                "budget_max": "200000.00",
                "ville": "Abidjan",
                "type_bien": "appartement",
                "nombre_chambres_min": 1,
                "localisation": "Cocody",
            },
        )
    )
    results.append(
        call(
            client,
            "ia_search",
            "POST",
            "/api/ia/recherche/rechercher/",
            {"texte": "appartement Abidjan Cocody budget 150000"},
        )
    )
    results.append(
        call(
            client,
            "ia_verify_document",
            "POST",
            "/api/ia/verifier-document/verifier/",
            {"document_url": "https://example.com/doc.jpg", "document_type": "cni"},
        )
    )

    if bien_id:
        results.append(
            call(
                client,
                "message_create",
                "POST",
                "/api/messages/",
                {
                    "conversation_id": f"conv-{suffix}",
                    "receiver": second_user.id,
                    "texte": "Bonjour, test message.",
                },
            )
        )
        results.append(call(client, "messages_list", "GET", "/api/messages/"))
        results.append(call(client, "mes_messages", "GET", "/api/messages/mes_messages/"))
        results.append(call(client, "conversations", "GET", "/api/messages/conversations/"))
        results.append(call(client, "conversation_detail", "GET", f"/api/messages/conversation/conv-{suffix}/"))

    results.append(call(client, "api_root", "GET", "/api/"))

    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
