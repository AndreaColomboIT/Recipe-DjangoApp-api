"""
Serializer for recipe APIs
"""

from rest_framework import serializers
from core.models import (Recipe, Tag, Ingredient)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tags"""

    class Meta:
        model = Tag
        fields = ['id','name']
        read_only_fields = ['id']


class IngredientsSerializer(serializers.ModelSerializer):
    """Serializer for Ingredients"""

    class Meta:
        model = Ingredient
        fields = ['id','name']
        read_only_fields = ['id']   

      
class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe"""
    tags = TagSerializer(many = True, required = False)
    ingredients = IngredientsSerializer(many = True, required = False)
    class Meta:
        model = Recipe
        fields = ['id','title','time_minutes','price','link','tags','ingredients']
        read_only_fields = ['id']


    def _assigne_tags(self,tags,recipe):
        """Handle getting or creating tags as needed"""
        auth_user = self.context['request'].user
        for tag in tags:
            #method get_or_create return a tuple
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                # Use this sintaxt for future additional parameters
                #Now this takes only
                **tag
            )
            recipe.tags.add(tag_obj)

    def _assigne_ingredients(self,ingredients,recipe):
        """Handle getting or creating tags as needed"""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            #method get_or_create return a tuple
            ing_obj, created = Ingredient.objects.get_or_create(
                user = auth_user,
                # Use this sintaxt for future additional parameters
                #Now this takes only
                **ingredient
            )
            recipe.ingredients.add(ing_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._assigne_tags(tags,recipe)
        self._assigne_ingredients(ingredients,recipe)
        return recipe


    def update(self, instance, validated_data):
        """Update Recipe"""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._assigne_tags(tags,instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._assigne_tags(ingredients,instance)
            
        for attr,value in validated_data.items():
            setattr(instance,attr,value)

        instance.save()
        return instance
        
class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


