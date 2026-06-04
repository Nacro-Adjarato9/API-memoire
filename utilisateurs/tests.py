from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from .serializers import RegisterSerializer

User = get_user_model()


class UserRegistrationTests(TestCase):
	def test_email_uniqueness_on_registration(self):
		data = {
			'email': 'unique@example.com',
			'password': 'StrongPass123!',
			'password2': 'StrongPass123!',
			'user_type': 'locataire'
		}

		serializer = RegisterSerializer(data=data)
		self.assertTrue(serializer.is_valid(), serializer.errors)
		user = serializer.save()
		self.assertEqual(User.objects.filter(email__iexact='unique@example.com').count(), 1)

		# Attempt to register again with same email
		serializer2 = RegisterSerializer(data=data)
		self.assertFalse(serializer2.is_valid())
		self.assertIn('email', serializer2.errors)

class UtilisateurViewSetTests(APITestCase):
    def test_utilisateur_list_returns_profile_for_authenticated_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='StrongPass123!'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/utilisateurs/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], user.id)