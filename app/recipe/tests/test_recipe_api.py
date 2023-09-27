"""
Tests for recipe apis
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (Recipe, Tag)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args= [recipe_id])

    
def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title' : 'Sample recipe test title',
        'time_minutes' : 22,
        'price' : Decimal('5.25'),
        'description' : 'Sample recipe test description'
    }
    # Add additional params passed to function
    defaults.update(params)
    recipe = Recipe.objects.create(
        user = user, 
        **defaults
    )
    return recipe


def create_user(**params):
    """Create users"""
    return get_user_model().objects.create_user(**params)
    
class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email = 'test@example.com', password = 'testPass')
        self.other_user = create_user(email = 'other@example.com', password = 'testPass')
        # Authenticate user 
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieve list of recipes"""
        #Create two recipes in Database
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        
        recipes = Recipe.objects.all().order_by('-id')
        #many = True means that is a list of items
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test retrieve list of recipes of authenticated user"""
        #Create two recipes in Database
        create_recipe(user=self.other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        
        recipes = Recipe.objects.filter(user = self.user)
        
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user = self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)


    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
            'description' : 'Sample description'
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)


    def test_partial_update(self):
        """Test partial update of recipe"""
        original_link = 'https://RandomLink.com'
        recipe = create_recipe(
            user = self.user,
            title = 'Random sample title',
            link = original_link
        )

        payload = {'title' : 'New Recipe Title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)


    def test_full_update(self):
        """Test full update of recipe"""
        recipe = create_recipe(
            user = self.user,
            title = 'Random sample title',
            link = 'https://RandomLink.com',
            description = 'Sample description'
        )
        payload = {
            'title': 'New Sample recipe',
            'time_minutes': 30,
            'price': Decimal('10.99'),
            'description' : 'New Sample description',
            'link' : 'https://NewRandomLink.com'
        }
        
        url = detail_url(recipe.id)
        #put is used for full update of Object
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k ), v)
        self.assertEqual(recipe.user, self.user)    


    def test_update_user_returns_error(self):
        new_user = create_user(email = 'other2@example.com', password = 'testPass123456')
        recipe = create_recipe(user = self.user)

        payload = {'user' : new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test to Delete a recipe"""
        recipe = create_recipe(user = self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id = recipe.id).exists()) 

    def test_create_recipe_with_new_tags(self):
        """Test creating recipe with new tags"""
        payload = {
            'title': 'New Sample recipe',
            'time_minutes': 30,
            'price': Decimal('10.99'),
            'description' : 'Sample description',
            'tags' : [{'name':'Thai'}, {'name':'Dinner'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)


    def test_create_tag_on_update(self):
        """Test create tag when updating a recipe"""
        recipe = create_recipe(user = self.user)
        payload = {
            'tags' : [{'name':'Lunch'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user = self.user, name = 'Lunch')
        self.assertIn(new_tag, recipe.tags.all())