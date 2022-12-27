import json, random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Q, Avg
from django.db.models.query import QuerySet
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponseBadRequest

from rest_framework import mixins, generics, status, permissions, views
from rest_framework.exceptions import ParseError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from server.utils import DEFAULT_RESPONSES
from .models import *
from .serializers import *


# Create your views here.

class ArticleDetailView(generics.RetrieveAPIView):
    """文章详情"""

    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @swagger_auto_schema(
        operation_summary='获取文章详情',
        operation_description='获取文章详情',
        responses = DEFAULT_RESPONSES,
        tags=['H5'],
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
