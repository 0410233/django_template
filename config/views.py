
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


class ConfigList(mixins.ListModelMixin, generics.GenericAPIView):
    """扩展配置列表"""

    # queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None

    def get_queryset(self):
        queryset = Config.objects.filter(scope=0)
        return queryset

    @swagger_auto_schema(
        operation_summary='获取扩展配置',
        operation_description='获取扩展配置',
        responses = DEFAULT_RESPONSES,
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


# def upload_file(request):
#     if request.method == 'POST' and request.FILES['file']:
#         filename = handle_upload_file(request.FILES['file'])
#         return JsonResponse({
#             'name': filename,
#             'path': settings.MEDIA_URL + filename,
#         })
#     return HttpResponseNotFound()


# def update_setting_value(request, key):
#     if request.method == 'POST':
#         try:
#             item = SettingInfo.objects.get(key=key)
#         except SettingInfo.DoesNotExist:
#             item = None

#         if item is not None:
#             item.value = request.POST['value']
#             item.save()
            
#             return JsonResponse(model_to_dict(item))

#         return JsonResponse({})
        
#     return HttpResponseNotFound()
