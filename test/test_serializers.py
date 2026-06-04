import base64
from types import SimpleNamespace
from unittest.mock import patch
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from biens.serializers import BienCreateSerializer, DocumentCreateSerializer
from tarifs.models import Abonnement, Tarif
from tarifs.serializers import (
    AbonnementCreateSerializer,
    AbonnementSerializer,
    TarifSerializer,
)
from utilisateurs.models import PasswordReset, ProfilAgence
from utilisateurs.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    ProfilAgenceSerializer,
    ProfilAgenceVerificationSerializer,
    ProfilProprietaireSerializer,
    ProfilProprietaireVerificationSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    ProfileUpdateSerializer,
)
from utilisateurs.token_generator import EmailVerificationTokenGenerator


User = get_user_model()


def make_request(user):
    return SimpleNamespace(user=user)


class RegisterSerializerTests(TestCase):
    def test_register_serializer_creates_locataire(self):
        serializer = RegisterSerializer(data={
            "email": "locataire@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "user_type": "locataire",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.profile.role, "locataire")

    def test_register_serializer_accepts_role_alias(self):
        serializer = RegisterSerializer()
        data = serializer.validate({
            "email": "alias@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "proprietaire",
        })
        self.assertEqual(data["user_type"], "proprietaire")

    def test_register_serializer_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="duplicate@example.com",
            password="StrongPass123!",
        )

        serializer = RegisterSerializer(data={
            "email": "duplicate@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "user_type": "locataire",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_register_serializer_rejects_invalid_user_type(self):
        serializer = RegisterSerializer(data={
            "email": "bad@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "user_type": "unknown",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("user_type", serializer.errors)

    def test_register_serializer_rejects_password_mismatch(self):
        serializer = RegisterSerializer(data={
            "email": "bad2@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass1234!",
            "user_type": "locataire",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class LoginSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123!",
        )

    def test_login_serializer_requires_identifier(self):
        serializer = LoginSerializer(data={"password": "StrongPass123!"})
        self.assertFalse(serializer.is_valid())

    def test_login_serializer_rejects_invalid_credentials(self):
        serializer = LoginSerializer(data={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "wrong",
        })
        self.assertFalse(serializer.is_valid())

    def test_login_serializer_rejects_unverified_user(self):
        serializer = LoginSerializer(data={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "StrongPass123!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)

    def test_login_serializer_accepts_verified_user(self):
        self.user.profile.is_verified = True
        self.user.profile.save()
        serializer = LoginSerializer(data={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "StrongPass123!",
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="StrongPass123!",
        )

    @patch("utilisateurs.serializers.send_password_reset_email")
    def test_password_reset_serializer_creates_reset_and_calls_email(
        self, mocked_send
    ):
        serializer = PasswordResetSerializer(data={"email": "reset@example.com"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        reset = serializer.save()

        self.assertIsInstance(reset, PasswordReset)
        self.assertTrue(PasswordReset.objects.filter(user=self.user).exists())
        mocked_send.assert_called_once()

    def test_password_reset_serializer_rejects_unknown_email(self):
        serializer = PasswordResetSerializer(data={"email": "unknown@example.com"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_reset_confirm_requires_matching_passwords(self):
        token = EmailVerificationTokenGenerator.generate_token(self.user)
        PasswordReset.objects.create(
            user=self.user,
            token=token,
            date_expiration=timezone.now() + timedelta(hours=1),
        )
        serializer = PasswordResetConfirmSerializer(data={
            "email": "reset@example.com",
            "token": token,
            "password": "StrongPass123!",
            "password2": "Different123!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("password2", serializer.errors)

    def test_password_reset_confirm_succeeds_and_deletes_reset(self):
        token = EmailVerificationTokenGenerator.generate_token(self.user)
        PasswordReset.objects.create(
            user=self.user,
            token=token,
            date_expiration=timezone.now() + timedelta(hours=1),
        )
        serializer = PasswordResetConfirmSerializer(data={
            "email": "reset@example.com",
            "token": token,
            "password": "NewStrongPass123!",
            "password2": "NewStrongPass123!",
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertFalse(PasswordReset.objects.filter(user=self.user).exists())

    def test_password_reset_confirm_rejects_invalid_token(self):
        serializer = PasswordResetConfirmSerializer(data={
            "email": "reset@example.com",
            "token": "wrong",
            "password": "NewStrongPass123!",
            "password2": "NewStrongPass123!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_password_reset_confirm_rejects_unknown_email(self):
        serializer = PasswordResetConfirmSerializer(data={
            "email": "missing@example.com",
            "token": "wrong",
            "password": "NewStrongPass123!",
            "password2": "NewStrongPass123!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_reset_confirm_rejects_expired_token(self):
        token = EmailVerificationTokenGenerator.generate_token(self.user)
        PasswordReset.objects.create(
            user=self.user,
            token=token,
            date_expiration=timezone.now() - timedelta(hours=1),
        )
        serializer = PasswordResetConfirmSerializer(data={
            "email": "reset@example.com",
            "token": token,
            "password": "NewStrongPass123!",
            "password2": "NewStrongPass123!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_change_password_serializer_rejects_mismatch(self):
        serializer = ChangePasswordSerializer(data={
            "old_password": "StrongPass123!",
            "new_password": "NewStrongPass123!",
            "new_password2": "Different123!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password2", serializer.errors)


class VerificationAndProfileSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123!",
            first_name="Awa",
            last_name="Diallo",
        )

    def test_verify_email_serializer_accepts_valid_token(self):
        token = EmailVerificationTokenGenerator.generate_token(self.user)
        serializer = VerifyEmailSerializer(data={
            "email": "profile@example.com",
            "token": token,
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_verify_email_serializer_rejects_invalid_token(self):
        serializer = VerifyEmailSerializer(data={
            "email": "profile@example.com",
            "token": "bad-token",
        })
        self.assertFalse(serializer.is_valid())

    def test_verify_email_serializer_rejects_unknown_email(self):
        serializer = VerifyEmailSerializer(data={
            "email": "missing@example.com",
            "token": "bad-token",
        })
        self.assertFalse(serializer.is_valid())

    def test_resend_verification_serializer_is_valid(self):
        serializer = ResendVerificationSerializer(
            data={"email": "profile@example.com"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_serializer_reports_verification_status(self):
        self.user.profile.is_verified = True
        self.user.profile.save()
        serializer = UserSerializer(self.user)
        self.assertTrue(serializer.data["is_verified"])

    def test_user_serializer_defaults_to_false_without_profile(self):
        other = User.objects.create_user(
            username="noprof",
            email="noprof@example.com",
            password="StrongPass123!",
        )
        other.profile.delete()
        serializer = UserSerializer(other)
        self.assertFalse(serializer.data["is_verified"])

    def test_profile_update_serializer_has_expected_fields(self):
        serializer = ProfileUpdateSerializer()
        self.assertEqual(
            tuple(serializer.fields.keys()),
            ("username", "email", "first_name", "last_name"),
        )

    def test_profil_proprietaire_serializer_sets_defaults(self):
        request = make_request(self.user)
        serializer = ProfilProprietaireSerializer(
            instance=None,
            context={"request": request},
        )
        data = serializer.validate({})
        self.assertEqual(data["nom"], "Awa")
        self.assertEqual(data["prenom"], "Diallo")

    def test_profil_agence_serializer_create_with_logo_preview(self):
        request = make_request(self.user)
        logo = "data:image/png;base64," + base64.b64encode(b"logo").decode()
        serializer = ProfilAgenceSerializer(
            data={
                "nom_agence": "Agence X",
                "ville": "Abidjan",
                "logoPreview": logo,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_profil_agence_serializer_create_method_decodes_logo(self):
        request = make_request(self.user)
        logo = "data:image/png;base64," + base64.b64encode(b"logo").decode()
        serializer = ProfilAgenceSerializer(context={"request": request})
        created = serializer.create(
            {
                "user": self.user,
                "nom_agence": "Agence Y",
                "ville": "Abidjan",
                "logoPreview": logo,
            }
        )
        self.assertEqual(created.nom_agence, "Agence Y")
        self.assertTrue(created.logo.name.endswith(".png"))

    def test_profil_agence_serializer_update_method_decodes_logo(self):
        request = make_request(self.user)
        agence = ProfilAgence.objects.create(
            user=self.user,
            nom_agence="Agence Z",
            ville="Abidjan",
        )
        serializer = ProfilAgenceSerializer(context={"request": request})
        logo = "data:image/png;base64," + base64.b64encode(b"logo").decode()
        updated = serializer.update(
            agence,
            {
                "logoPreview": logo,
                "nom_agence": "Agence Z2",
            },
        )
        self.assertEqual(updated.nom_agence, "Agence Z2")

    def test_profil_proprietaire_verification_serializer_validate(self):
        serializer = ProfilProprietaireVerificationSerializer()
        data = {
            "type_piece": "cni",
            "numero_piece": "AB123",
            "photo_piece_recto": SimpleUploadedFile("recto.jpg", b"1"),
            "photo_piece_verso": SimpleUploadedFile("verso.jpg", b"1"),
            "selfie_verification": SimpleUploadedFile("selfie.jpg", b"1"),
        }
        self.assertEqual(serializer.validate(data), data)

    def test_profil_proprietaire_verification_serializer_rejects_missing(self):
        serializer = ProfilProprietaireVerificationSerializer()
        with self.assertRaises(Exception):
            serializer.validate({})

    def test_profil_agence_verification_serializer_validate(self):
        serializer = ProfilAgenceVerificationSerializer()
        data = {
            "numero_registre_commerce": "RCCM123",
            "numero_contribuable": "NCC123",
            "document_legal": SimpleUploadedFile("doc.pdf", b"1"),
        }
        self.assertEqual(serializer.validate(data), data)

    def test_profil_agence_verification_serializer_rejects_missing(self):
        serializer = ProfilAgenceVerificationSerializer()
        with self.assertRaises(Exception):
            serializer.validate({})


class BienAndDocumentSerializerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="bienowner",
            email="bienowner@example.com",
            password="StrongPass123!",
        )
        self.agent = User.objects.create_user(
            username="bienagent",
            email="bienagent@example.com",
            password="StrongPass123!",
        )
        self.agent.profile.role = "agence"
        self.agent.profile.save()

    def test_bien_create_serializer_assigns_proprietaire(self):
        request = make_request(self.owner)
        serializer = BienCreateSerializer(
            data={
                "titre": "Villa",
                "description": "Test",
                "prix": 500000,
                "ville": "Abidjan",
                "localisation": "Cocody",
                "type": "maison",
                "statut": "disponible",
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        bien = serializer.save()
        self.assertEqual(bien.proprietaire, self.owner)

    def test_bien_create_serializer_assigns_agence_for_agency_role(self):
        request = make_request(self.agent)
        serializer = BienCreateSerializer(
            data={
                "titre": "Villa agence",
                "description": "Test",
                "prix": 600000,
                "ville": "Abidjan",
                "localisation": "Marcory",
                "type": "maison",
                "statut": "disponible",
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        bien = serializer.save()
        self.assertEqual(bien.agence, self.agent)

    def test_document_create_serializer_generates_title_from_type(self):
        request = make_request(self.owner)
        pdf = base64.b64encode(b"%PDF-1.4 fake").decode()
        serializer = DocumentCreateSerializer(
            data={
                "type_document": "registre_commerce",
                "fichier_base64": pdf,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        document = serializer.save()
        self.assertEqual(document.titre, "Registre Commerce")

    def test_document_create_serializer_assigns_file_from_base64(self):
        request = make_request(self.owner)
        pdf = base64.b64encode(b"%PDF-1.4 fake").decode()
        serializer = DocumentCreateSerializer(
            data={
                "type_document": "cni",
                "fichier_base64": pdf,
                "fichier_name": "identity",
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        document = serializer.save()
        self.assertTrue(document.fichier.name.endswith(".pdf"))


class TarifsSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tarifuser",
            email="tarifuser@example.com",
            password="StrongPass123!",
        )
        self.request = make_request(self.user)

    def test_tarif_serializer_serializes_fields(self):
        tarif = Tarif.objects.create(
            nom="Pack A",
            description="Desc",
            prix=9000,
            duree="mensuel",
            features=["a", "b"],
        )
        self.assertTrue(tarif.pk)
        self.assertEqual(TarifSerializer(tarif).data["nom"], "Pack A")

    def test_abonnement_serializer_assigns_user(self):
        tarif = Tarif.objects.create(
            nom="Pack B",
            description="Desc",
            prix=9000,
            duree="mensuel",
        )
        serializer = AbonnementSerializer(
            data={
                "tarif": tarif.id,
                "date_fin": timezone.now() + timedelta(days=30),
                "statut": "actif",
                "auto_renew": True,
            },
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        abonnement = serializer.save()
        self.assertIsInstance(abonnement, Abonnement)
        self.assertEqual(abonnement.utilisateur, self.user)

    def test_abonnement_create_serializer_monthly_branch(self):
        tarif = Tarif.objects.create(
            nom="Pack C",
            description="Desc",
            prix=9000,
            duree="mensuel",
        )
        serializer = AbonnementCreateSerializer(
            data={"tarif": tarif.id, "duree_mois": 2, "auto_renew": True},
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        abonnement = serializer.save()
        self.assertIsInstance(abonnement, Abonnement)
        self.assertEqual(abonnement.utilisateur, self.user)

    def test_abonnement_create_serializer_trimestriel_branch(self):
        tarif = Tarif.objects.create(
            nom="Pack D",
            description="Desc",
            prix=9000,
            duree="trimestriel",
        )
        serializer = AbonnementCreateSerializer(
            data={"tarif": tarif.id, "duree_mois": 1, "auto_renew": True},
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        abonnement = serializer.save()
        self.assertIsInstance(abonnement, Abonnement)
        self.assertEqual(abonnement.utilisateur, self.user)

    def test_abonnement_create_serializer_semestriel_branch(self):
        tarif = Tarif.objects.create(
            nom="Pack E",
            description="Desc",
            prix=9000,
            duree="semestriel",
        )
        serializer = AbonnementCreateSerializer(
            data={"tarif": tarif.id, "duree_mois": 1, "auto_renew": True},
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        abonnement = serializer.save()
        self.assertIsInstance(abonnement, Abonnement)
        self.assertEqual(abonnement.utilisateur, self.user)

    def test_abonnement_create_serializer_annuel_branch(self):
        tarif = Tarif.objects.create(
            nom="Pack F",
            description="Desc",
            prix=9000,
            duree="annuel",
        )
        serializer = AbonnementCreateSerializer(
            data={"tarif": tarif.id, "duree_mois": 1, "auto_renew": True},
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        abonnement = serializer.save()
        self.assertIsInstance(abonnement, Abonnement)
        self.assertEqual(abonnement.utilisateur, self.user)
