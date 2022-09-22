
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Q, Avg
from django.db.models.query import QuerySet
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponseBadRequest, QueryDict

from rest_framework import mixins, generics, status, permissions, views
from rest_framework.authtoken.models import Token
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


class UserSettingList(mixins.ListModelMixin, generics.GenericAPIView):
    """用户配置列表"""

    serializer_class = UserSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None

    def get_queryset(self):
        queryset = UserSetting.objects.filter(scope=0)
        return queryset

    @swagger_auto_schema(
        operation_summary='获取用户配置',
        operation_description='获取用户配置',
        responses = DEFAULT_RESPONSES,
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
