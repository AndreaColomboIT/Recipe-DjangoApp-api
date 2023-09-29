"""
Views for recipes API
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes
)

from rest_framework import (
    viewsets,
    status
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (Recipe, Tag, Ingredient)
from recipe import serializers


@extend_schema_view(
    list = extend_schema (
        parameters = [
            OpenApiParameter (
                'tags',
                OpenApiTypes.STR,
                description = 'Comma separated list of tag IDs to filter'
            ),
            OpenApiParameter (
                'ingredients',
                OpenApiTypes.STR,
                description = 'Comma separated list of ingredient IDs to filter'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self,qs):
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve recipes for authenticated user"""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tags_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_ids)
        if ingredients:
            ing_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ing_ids)
        # distinct() removes duplicate values 
        return queryset.filter(user = self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self,request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list = extend_schema (
        parameters = [
            OpenApiParameter (
                'assigned_only',
                OpenApiTypes.INT,
                enum = [0,1],
                description = 'Filter by items assigned to recipe'
            )
        ]
    )
)
class TagsViewSet(viewsets.ModelViewSet):
    """View for manage Tags APIs"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve Tags for authenticated user"""
        #use bool to convert integer 
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only',0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull = False)
            
        return queryset.filter(
            user = self.request.user
            ).order_by('-name').distinct()

    def perform_create(self, serializer):
        """Override method to create a new Tag."""
        serializer.save(user=self.request.user)


@extend_schema_view(
    list = extend_schema (
        parameters = [
            OpenApiParameter (
                'assigned_only',
                OpenApiTypes.INT,
                enum = [0,1],
                description = 'Filter by items assigned to recipe'
            )
        ]
    )
)
class IngredientsViewSet(viewsets.ModelViewSet):
    """View for manage Ingredients APIs"""
    serializer_class = serializers.IngredientsSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve Ingredients for authenticated user"""
        #use bool to convert integer 
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only',0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull = False)
        return queryset.filter(
            user = self.request.user
            ).order_by('-name').distinct()

    def perform_create(self, serializer):
        """Override method to create a new Tag."""
        serializer.save(user=self.request.user)