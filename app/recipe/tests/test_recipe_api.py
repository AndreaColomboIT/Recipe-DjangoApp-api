"""
Tests for recipe apis
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
import tempfile
import os
from PIL import Image

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (Recipe, Tag, Ingredient)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args= [recipe_id])


def image_upload_url(recipe_id):
    """Create and upload image url"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

    
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


    def test_filter_by_tags(self):
        """Test filter recipe by tags"""
        recipe_1 = create_recipe(user= self.user, title = 'Spaghetti pomodoro')
        recipe_2 = create_recipe(user= self.user, title = 'Carbonara')
        tag_1 = Tag.objects.create(user = self.user, name = 'Primo piatto tipico')
        tag_2 = Tag.objects.create(user = self.user, name = 'Primo piatto romano')
        recipe_1.tags.add(tag_1)
        recipe_2.tags.add(tag_2)
        recipe_3 = create_recipe(user= self.user, title = 'Pesce')

        params = {'tags' : f'{tag_1.id},{tag_2.id}'}
        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(recipe_1)
        s2 = RecipeSerializer(recipe_2)
        s3 = RecipeSerializer(recipe_3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


    def test_filter_by_ingredients(self):
        """Test filter recipe by tags"""
        recipe_1 = create_recipe(user= self.user, title = 'Spaghetti pomodoro')
        recipe_2 = create_recipe(user= self.user, title = 'Carbonara')
        ing_1 = Ingredient.objects.create(user = self.user, name = 'Pasta')
        ing_2 = Ingredient.objects.create(user = self.user, name = 'Pomodoro')
        recipe_1.ingredients.add(ing_1)
        recipe_2.ingredients.add(ing_2)
        recipe_3 = create_recipe(user= self.user, title = 'Pesce')

        params = {'ingredients' : f'{ing_1.id},{ing_2.id}'}
        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(recipe_1)
        s2 = RecipeSerializer(recipe_2)
        s3 = RecipeSerializer(recipe_3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)
        
class ImageUploadTests(TestCase):
    """Tests for the Image Upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email = 'user@example.com', password = 'password123')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)


    # It runs after the test and delete the image created for recipe
    def tearDown(self):
        self.recipe.image.delete()


    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix= '.jpg') as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image' : image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))


    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image' : 'Bad format'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)