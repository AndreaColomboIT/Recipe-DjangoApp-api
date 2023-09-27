from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag
from recipe.serializers import (TagSerializer)


TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    """Create and return a tag detail url"""
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email = 'user@example.com', password = 'testpass123'):
    return get_user_model().objects.create_user(email = email, password = password)

    
class PublicTagsAPITests(TestCase):
    """Test unauthenticated API"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test authenticated API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.other_user = create_user(email = 'Other@example.com')
        # Authenticate user 
        self.client.force_authenticate(self.user)


    def test_retrieve_tags(self):
        """Test retrieve list of tags"""
        Tag.objects.create(user = self.user, name = 'Vegan')
        Tag.objects.create(user = self.user, name = 'Dessert')

        res = self.client.get(TAGS_URL)
        
        tags = Tag.objects.all().order_by('-name')
        #many = True means that is a list of items
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_tag_list_limited_to_user(self):
        """Test retrieve list of tags of authenticated user"""
        Tag.objects.create(user = self.other_user, name = 'Casual')
        tag = Tag.objects.create(user = self.user, name = 'Fruity')

        res = self.client.get(TAGS_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_update_tag(self):
        tag = Tag.objects.create(user = self.user, name = 'Fruity')
        payload = {'name' : 'Dessert'}

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test to Delete a recipe"""
        tag = Tag.objects.create(user = self.user, name = 'Fruity')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id = tag.id).exists()) 