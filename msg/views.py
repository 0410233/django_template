
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q
from django.db.models.query import QuerySet
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponseBadRequest

from rest_framework import mixins, generics, status, permissions, views
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ParseError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from server.utils import DEFAULT_RESPONSES
from user.models import User
from .serializers import MsgSerializer
from .models import Msg, MsgReaded


# Create your views here.


class MsgList(mixins.ListModelMixin, generics.GenericAPIView):

    queryset = Msg.objects.all()
    serializer_class = MsgSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Msg.objects.filter(
            create_time__gte=self.request.user.date_joined,
            type=self.type,
        ).filter(Q(user=self.request.user) | Q(user__isnull=True)).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='获取消息列表',
        responses=DEFAULT_RESPONSES,
        tags=['消息'],
    )
    def get(self, request: HttpRequest, *args, **kwargs):
        self.type = int(kwargs.get('type', 0))
        res = self.list(request, *args, **kwargs)

        for detail in res.data['results']:
            _, created = MsgReaded.objects.get_or_create(
                msg_id=detail['msg_id'],
                user=request.user,
            )
            if created:
                detail['is_read'] = 0
            else:
                detail['is_read'] = 1
        return res


class TipsInfo(views.APIView):
    """消息数"""

    permission_classes = (permissions.IsAuthenticated,)
    # serializer_class = MsgSerializer
    # pagination_class = None

    @swagger_auto_schema(
        operation_summary='获取用户新消息数',
        responses = {
            200: openapi.Response('用户新消息数统计', schema=openapi.Schema(
                type = openapi.TYPE_OBJECT,
                properties={
                    'msg_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='合计新消息数'),
                    'sys_msg_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='系统新消息数'),
                    'order_msg_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='咨询新消息数'),
                }
            ))
        } | DEFAULT_RESPONSES,
        tags=['消息'],
    )
    def get(self, request: HttpRequest, *args, **kwargs):
        user: User = request.user
        
        data = {
            'msg_count': 0,
            'sys_msg_count': 0,
            'order_msg_count': 0,
        }

        # 总消息数
        queryset = (
            Msg.objects
            .filter(Q(user=user)|Q(user__isnull=True))
            .filter(create_time__gte=user.date_joined)
            .values('type')
            .annotate(total=Count('*'))
        )
        # print(queryset.query)

        # 类型 0系统1咨询
        for rec in queryset:
            if rec['type'] == 0:
                data['sys_msg_count'] += rec['total']
            elif rec['type'] == 1:
                data['order_msg_count'] += rec['total']
            data['msg_count'] += rec['total']

        # 已读消息数
        queryset_read = (MsgReaded.objects
            .filter(user=user)
            .values('msg__type')
            .annotate(type=F('msg__type'), total=Count('*'))
        )
        # print(queryset_read.query)
        
        # 类型 0系统1咨询
        for rec in queryset_read:
            if rec['type'] == 0:
                data['sys_msg_count'] -= rec['total']
            elif rec['type'] == 1:
                data['order_msg_count'] -= rec['total']
            data['msg_count'] -= rec['total']

        return Response(data)
