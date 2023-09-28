from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient
from recipe.serializers import (IngredientsSerializer)

def create_user(email = 'user@example.com', password = 'Testpass123'):
    return get_user_model().objects.create_user(email = email,password = password)


INGREDIENTS_URL = reverse('recipe:ingredient-list')
class PublicIngredientAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        
    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        # Authenticate user 
        self.client.force_authenticate(self.user)

    
    def test_retrieve_ingredients(self):
        """Test retrieve list of tags"""
        Ingredient.objects.create(user = self.user, name = 'Vegan')
        Ingredient.objects.create(user = self.user, name = 'Dessert')

        res = self.client.get(INGREDIENTS_URL)
        
        tags = Ingredient.objects.all().order_by('-name')
        #many = True means that is a list of items
        serializer = IngredientsSerializer(tags, many=True)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
