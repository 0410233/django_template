import json, random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Q, Avg
from django.db.models.query import QuerySet
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponseBadRequest

from rest_framework import mixins, generics, status, permissions, views
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ParseError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.pagination import PageNumberPagination

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from server.utils import DEFAULT_RESPONSES, generate_order_sn
from user.models import MoneyLog, User, Expert
from user.serializers import ExpertSerializer
from coupon.models import Coupon, UserCoupon

from .models import *
from .serializers import *


# Create your views here.


class HomeCarouselView(views.APIView):
    """首页轮播图"""

    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(
        operation_summary='获取首页轮播图',
        operation_description='获取首页轮播图',
        query_serializer=None,
        responses = {
            200: CarouselSerializer(many=True)
        } | DEFAULT_RESPONSES,
        tags=['首页'],
    )
    def get(self, request, *args, **kwargs):

        prefix = request.scheme + '://' + request.get_host() + settings.MEDIA_URL

        # 轮播图
        carousel = []

        from article.models import Article
        articles = Article.objects.filter(is_carousel=1, status=1).exclude(carousel_image=None)[:5]
        for article in articles:
            carousel.append({
                'id': article.pk,
                'type': 0,
                'title': article.title,
                'image': prefix + article.carousel_image.name,
                'time': article.modify_time,
            })

        from user.models import Expert
        experts = Expert.objects.filter(is_carousel=1).exclude(carousel_image=None)[:5]
        for expert in experts:
            carousel.append({
                'id': expert.pk,
                'type': 1,
                'title': expert.name,
                'image': prefix + expert.carousel_image.name,
                'time': expert.modify_time,
            })

        from knowledge.models import Knowledge
        knowledges = Knowledge.objects.filter(is_carousel=1).exclude(carousel_image=None)[:5]
        for knowledge in knowledges:
            carousel.append({
                'id': knowledge.pk,
                'type': 2,
                'title': knowledge.name,
                'image': prefix + knowledge.carousel_image.name,
                'time': knowledge.modify_time,
            })

        if len(carousel):
            carousel = sorted(carousel, key=lambda focus: focus['time'], reverse=True)[:5]

        return Response(carousel)


class HotExpertList(generics.ListAPIView):
    """首页热门专家"""
    
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_serializer_class(self):
        from user.serializers import ExpertSerializer
        return ExpertSerializer

    def get_queryset(self):
        from user.models import Expert
        queryset = Expert.objects.filter(is_hot=1).order_by('-create_time')[:5]
        return queryset

    @swagger_auto_schema(
        operation_summary='首页热门专家',
        operation_description='首页热门专家',
        responses = DEFAULT_RESPONSES,
        tags=['首页'],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)



class RecommendKnowledgeList(generics.ListAPIView):
    """首页推荐视频"""
    
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_serializer_class(self):
        from knowledge.serializers import KnowledgeSerializer
        return KnowledgeSerializer

    def get_queryset(self):
        from knowledge.models import Knowledge
        queryset = Knowledge.objects.filter(is_recommend=1).order_by('-create_time')[:6]
        return queryset

    @swagger_auto_schema(
        operation_summary='首页推荐视频',
        operation_description='首页推荐视频',
        responses = DEFAULT_RESPONSES,
        tags=['首页'],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)



class SearchView(views.APIView):
    """搜索"""
    
    permission_classes = (permissions.AllowAny,)
    pagination_class = PageNumberPagination
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_expert_results(self):
        """专家搜索"""
        from user.models import Expert
        from user.serializers import ExpertSerializer

        queryset = Expert.objects.filter(name__contains=self.keywords).order_by('-create_time')
        page = self.paginate_queryset(queryset)
        serializer = ExpertSerializer(page, many=True, context=self.get_serializer_context())
        paginated_response = self.paginator.get_paginated_response(serializer.data)
        return paginated_response.data

    def get_topic_results(self):
        """问答搜索"""
        from topic.models import Topic
        from topic.serializers import TopicSerializer
        
        queryset = Topic.objects.filter(status=Topic.Status.PASSED).filter(Q(title__contains=self.keywords)|Q(content__contains=self.keywords)).order_by('-create_time')
        page = self.paginate_queryset(queryset)
        serializer = TopicSerializer(page, many=True, context=self.get_serializer_context())
        paginated_response = self.paginator.get_paginated_response(serializer.data)
        return paginated_response.data

    def get_knowledge_results(self):
        """视频搜索"""
        from knowledge.models import Knowledge
        from knowledge.serializers import KnowledgeSerializer
        
        queryset = Knowledge.objects.filter(Q(name__contains=self.keywords)|Q(content__contains=self.keywords)).order_by('-create_time')
        page = self.paginate_queryset(queryset)
        serializer = KnowledgeSerializer(page, many=True, context=self.get_serializer_context())
        paginated_response = self.paginator.get_paginated_response(serializer.data)
        return paginated_response.data

    @swagger_auto_schema(
        operation_summary='搜索结果',
        query_serializer=SearchSerializer,
        responses = {
            status.HTTP_200_OK: SearchResponseSerializer,
        } | DEFAULT_RESPONSES,
        tags=['首页'],
    )
    def get(self, request: Request, *args, **kwargs):
        self.keywords = request.query_params.get('keywords', '')

        results = {}

        type = request.query_params.get('type', None)
        if type is None or int(type) == 0:
            results['expert'] = self.get_expert_results()
        if type is None or int(type) == 1:
            results['topic'] = self.get_topic_results()
        if type is None or int(type) == 2:
            results['knowledge'] = self.get_knowledge_results()

        return Response(results)
