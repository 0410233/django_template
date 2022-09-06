import os
import requests
import json, random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.query import QuerySet
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponseBadRequest, QueryDict

from rest_framework import mixins, generics, status, permissions, views
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ParseError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from server.WXBizDataCrypt import WXBizDataCrypt

import urllib.request
from user.models import get_file_path

from .serializers import *
from server.utils import DEFAULT_RESPONSES, generate_order_sn


# Create your views here.


class UserLogin(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserLoginSerializer

    @swagger_auto_schema(
        operation_summary='用户登录',
        responses={
            status.HTTP_201_CREATED: openapi.Response('response description', UserSerializer),
        } | DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appid = settings.WX_APPID
        secret = settings.WX_SECRET

        code = request.data['code']

        resp = requests.get('https://api.weixin.qq.com/sns/jscode2session',
                            {"appid": appid, 'secret': secret,
                             'js_code': code, 'grant_type': 'authorization_code'})
        data = json.loads(resp.text)

        if 'errcode' in dict(data).keys():
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            user = None
            if 'unionid' in dict(data).keys():
                try:
                    user = User.objects.get(unionid=data['unionid'])
                except User.DoesNotExist:
                    user = None
            if user is None:
                try:
                    user = User.objects.get(openid=data['openid'])
                except User.DoesNotExist:
                    user = None

            if user:
                if user.openid is None:
                    user.openid = data['openid']

                if user.unionid is None and 'unionid' in dict(data).keys():
                    user.unionid = data['unionid']

                user.session_key = data['session_key']

                serializer = UserSerializer(user, context={'request': request})
                token, _ = Token.objects.get_or_create(user=user)
                result = dict(serializer.data)
                result['token'] = token.key
                result['username'] = user.username

                user.session_key = data['session_key']

                now = timezone.now()
                # if timezone.is_aware(now):
                #     now = timezone.localtime(now)
                user.last_login = now

                user.save()

            else:
                seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"
                sa = []
                for i in range(8):
                    sa.append(random.choice(seed))
                salt = ''.join(sa)
                data['username'] = salt

                dic = {'openid': data['openid'], 'session_key': data['session_key']}

                serializer = UserSerializer(data=data, context={'request': request})

                if 'unionid' in dict(data).keys():
                    dic['unionid'] = data['unionid']
                if 'username' in dict(data).keys():
                    dic['username'] = data['username']

                result = {}

                if serializer.is_valid(raise_exception=True):
                    user = serializer.save(**dic)

                    token, _ = Token.objects.get_or_create(user=user)
                    result = dict(serializer.data)
                    result['token'] = token.key
                    result['username'] = user.username
                    user.save()

            return Response(result, status=status.HTTP_201_CREATED)



class UserWxMobileModify(mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserMobileModifySerializer

    @swagger_auto_schema(
        operation_summary='小程序用户修改手机号',
        responses={
            status.HTTP_201_CREATED: openapi.Response('response description', UserSerializer),
        } | DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        iv = request.data['iv']
        encryptedData = request.data['encryptedData']
        # try:
        appId = settings.WX_APPID

        sessionKey = self.request.user.session_key

        pc = WXBizDataCrypt(appId, sessionKey)

        data = pc.decrypt(encryptedData, iv)
        mobile = data['purePhoneNumber']

        try:
            user = User.objects.get(username=mobile)
            if user != self.request.user:
                raise ParseError('手机号已经存在')

        except User.DoesNotExist:
            user = request.user
            user.username = mobile
            user.save()

        # except:
        #     raise ParseError('未知错误')

        return Response(UserSerializer(request.user,context={"request":request}).data)



class UserDetail(mixins.RetrieveModelMixin, mixins.CreateModelMixin, generics.ListAPIView):

    # queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    parser_classes =  (MultiPartParser, )
    pagination_class = None

    def get_queryset(self):
        queryset = User.objects.all()

        if self.request.method == 'POST':
            queryset = queryset.filter(pk=self.request.user.id)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserPutSerializer

        return UserSerializer

    @swagger_auto_schema(
        operation_summary='获取用户信息',
        manual_parameters= [
            openapi.Parameter('id', openapi.IN_PATH, description="", type=openapi.TYPE_INTEGER),
        ],
        responses=DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def get(self, request: HttpRequest, *args, **kwargs):
        res = self.retrieve(request, *args, **kwargs)
        user_info = res.data
        if request.user.is_authenticated:
            user_id = int(user_info[User._meta.pk.name])
            if request.user.pk != user_id:
                count = Fans.objects.filter(user=request.user, to_user=user_id).count()
                user_info['is_followed'] = count > 0
        return res

    @swagger_auto_schema(
        operation_summary='修改用户信息',
        responses=DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        username = request.data.get('username')
        if username:
            user_list = User.objects.filter(username=username).exclude(id=pk)
            if len(user_list):
                raise ParseError('手机号已经存在')

        res = self.update(request, *args, **kwargs, partial=True)

        return res

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        user = serializer.save()

        if 'wx_user_info' in dict(self.request.data).keys():
            user.wx_user_info = self.request.data['wx_user_info']
            user.save()

        # if (user.avatar is None or len(user.avatar.name) < 1) and user.name is None:
        if 'wx_user_info' in dict(self.request.data).keys() and (
                user.wx_user_info is None or (user.wx_user_info and len(user.wx_user_info))):
            wx_user_info = user.wx_user_info
            try:
                user_info = json.loads(wx_user_info)

                # 下载图片到本地
                avatar = user_info['avatarUrl']
                filename = get_file_path(None, avatar)

                user.name = user_info['nickName']
                # user.sex = user_info['gender']
                user.save()

                if os.path.exists(settings.MEDIA_ROOT + '/'.join((filename.split('/')[:-1]))) is False:
                    os.makedirs(settings.MEDIA_ROOT + '/'.join((filename.split('/')[:-1])))

                urllib.request.urlretrieve(avatar, filename=settings.MEDIA_ROOT + filename)
                user.avatar = filename

                user.save()

            except json.decoder.JSONDecodeError:
                pass


class UserCurrentDetail(mixins.ListModelMixin, generics.GenericAPIView):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None

    @swagger_auto_schema(
        operation_summary='获取当前用户信息',
        operation_description="""
            credit 积分
            is_active false时被冻结 
        """,
        responses=DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset, pk=request.user.id)

        serializer = UserSerializer(user, context={'request': request})

        user_info = serializer.data
        
        user_info['credit'] = get_user_credit(self.request.user)

        return Response(user_info)


class FeedbackPost(mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):

    queryset = Feedback.objects.all()
    serializer_class = FeedbackPostSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='添加用户反馈',
        responses=DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def post(self, request, *args, **kwargs):
        res = self.create(request, *args, **kwargs)

        return res

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QAList(mixins.ListModelMixin,generics.GenericAPIView):

    queryset = QA.objects.all()
    serializer_class = QAListSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None

    def get_queryset(self):
        queryset = QA.objects.order_by('-display', '-modify_time')

        return queryset

    @swagger_auto_schema(
        operation_summary='常见问题/使用帮助',
        responses=DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def get(self,request):
        res =  self.list(request)
        return res

def getUserAvailableBalance(user):
    balance = 0  # 余额

    return balance


def get_user_credit(user):
    """获取用户积分余额"""
    result = CreditLog.objects.filter(user=user).aggregate(total_credit=Sum('credit'))
    return result['total_credit'] or 0


def get_user_balance(user):
    """获取用户余额"""
    result = MoneyLog.objects.filter(user=user).aggregate(total_money=Sum('money'))
    return result['total_money'] or 0


class UserSearchView(generics.ListAPIView):
    """搜索用户"""
    
    # queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = User.objects.all()
        if self.keywords:
            queryset = queryset.filter(name__contains=self.keywords)
        queryset = queryset.order_by('-date_joined')
        return queryset

    @swagger_auto_schema(
        operation_summary='搜索用户',
        operation_description='搜索用户',
        manual_parameters=[
            openapi.Parameter('keywords', openapi.IN_QUERY, description='用户昵称', type=openapi.TYPE_STRING),
        ],
        responses = DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def get(self, request, *args, **kwargs):
        self.keywords = request.query_params.get('keywords')
        # return Response({'keywords': self.keywords})
        return super().get(request, *args, **kwargs)


class FollowListView(generics.ListAPIView):
    """关注列表"""

    queryset = Fans.objects.all()
    serializer_class = FansSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def filter_queryset(self, queryset: QuerySet):
        queryset = queryset.filter(user=self.request.user)
        return queryset

    @swagger_auto_schema(
        operation_summary='关注列表',
        responses = DEFAULT_RESPONSES,
        tags=['我的'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class FansListView(generics.ListAPIView):
    """粉丝列表"""

    queryset = Fans.objects.all()
    serializer_class = FansSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def filter_queryset(self, queryset: QuerySet):
        queryset = queryset.filter(to_user=self.request.user)
        return queryset

    @swagger_auto_schema(
        operation_summary='粉丝列表',
        responses = DEFAULT_RESPONSES,
        tags=['我的'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class FollowView(views.APIView):
    """关注/取消关注"""

    # queryset = Fans.objects.all()
    # serializer_class = FansSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='关注/取消关注',
        operation_description='关注/取消关注',
        responses = DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def post(self, request: HttpRequest, *args, **kwargs):
        user_id = kwargs.get('user_id', 0)
        to_user = get_object_or_404(User, pk=int(user_id))

        follow: Fans = Fans.objects.filter(user=request.user, to_user=to_user).first()
        fans: Fans = Fans.objects.filter(user=to_user, to_user=request.user).first()

        # 自己关注自己
        if follow and fans and fans.pk == follow.pk:
            fans = None

        if follow:
            follow.delete()
            if fans:
                fans.type = 0
                fans.save()
            return Response({'errcode': 0, 'errmsg': '取消关注成功'}, status=status.HTTP_204_NO_CONTENT)
        else: 
            follow = Fans.objects.create(
                user=request.user, to_user=to_user, type=0
            )
            if fans:
                fans.type = 1
                fans.save()

                follow.type = 1
                follow.save()

            serializer = FansSerializer(follow, context={'request': request})
            return Response(serializer.data)


class UserBalanceView(views.APIView):
    """账户余额"""
    
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='账户余额',
        responses = {
            status.HTTP_200_OK: openapi.Response('账户余额', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'balance': openapi.Schema(type=openapi.TYPE_NUMBER)
                },
            ))
        } | DEFAULT_RESPONSES,
        tags=['我的', '用户'],
    )
    def get(self, request: HttpRequest):
        balance = get_user_balance(request.user)

        return Response({'balance': balance})


class WithdrawLogView(generics.ListCreateAPIView):
    """发起提现/提现记录"""

    serializer_class = WithdrawLogSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.method == 'GET':
            return WithdrawLog.objects.filter(user=self.request.user)
        return WithdrawLog.objects.all()

    @swagger_auto_schema(
        operation_summary='发起提现',
        operation_description='发起提现',
        responses = DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def post(self, request: HttpRequest, *args, **kwargs):
        # 检查金额
        money = request.data.get('money', 0)
        if money is None or int(money) == 0:
            return HttpResponseBadRequest('请输入提现金额')
        money = int(money)

        # 检查余额
        balance = get_user_balance(request.user)
        if balance > money:
            return HttpResponseBadRequest('余额不足')

        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        number = generate_order_sn('WD', self.request.user.pk)
        instance: WithdrawLog = serializer.save(user=self.request.user, number=number)

    @swagger_auto_schema(
        operation_summary='提现记录',
        operation_description='提现记录',
        responses = DEFAULT_RESPONSES,
        tags=['我的', '用户'],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class MoneyLogListview(generics.ListAPIView):
    """余额记录（钱包流水明细）"""
    
    # queryset = MoneyLog.objects.all()
    serializer_class = MoneyLogSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = MoneyLog.objects.filter(user=self.request.user).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='余额记录（钱包流水明细）',
        operation_description='余额记录（钱包流水明细）',
        responses = DEFAULT_RESPONSES,
        tags=['我的'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class CreditBalanceView(views.APIView):
    """积分余额"""
    
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='积分余额',
        responses = {
            status.HTTP_200_OK: openapi.Response('积分余额', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'credit': openapi.Schema(type=openapi.TYPE_NUMBER)
                },
            ))
        } | DEFAULT_RESPONSES,
        tags=['我的', '用户'],
    )
    def get(self, request: HttpRequest):
        credit = get_user_credit(request.user)
        return Response({'credit': credit})



class CreditLogListview(generics.ListAPIView):
    """积分明细"""
    
    # queryset = CreditLog.objects.all()
    serializer_class = CreditLogSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = CreditLog.objects.filter(user=self.request.user).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='积分明细',
        operation_description='积分明细',
        responses = DEFAULT_RESPONSES,
        tags=['我的'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserCreditRankingList(generics.ListAPIView):
    """积分排行"""

    serializer_class = CreditRankingSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        role = self.request.query_params.get('role', 0)
        if role is None or role == '':
            role = 0
        if int(role) == 0:
            queryset = CreditRanking.objects.exclude(user__status=User.Status.PASSED)
        else:
            queryset = CreditRanking.objects.filter(user__status=User.Status.PASSED)
        queryset = queryset.order_by('-credit', 'modify_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='积分排行',
        operation_description="""积分排行

            user_rank: 当前用户排名
        """,
        manual_parameters=[
            openapi.Parameter(
                name='role', in_=openapi.IN_QUERY,
                description='角色 - 0:用户,1:专家',
                type=openapi.TYPE_INTEGER, default=0
            )
        ],
        responses=DEFAULT_RESPONSES,
        tags=['用户'],
    )
    def get(self, request: HttpRequest, *args, **kwargs):
        response = self.list(request, *args, **kwargs)
        results = response.data['results']
        if len(results) > 0:
            last_credit = results[0]['credit']
            rank = CreditRanking.objects.filter(credit__gt=last_credit).count() + 1
            for result in results:
                if result['credit'] != last_credit:
                    last_credit = result['credit']
                    rank += 1
                result['rank'] = rank

        response.data['user_rank'] = 0
        if request.user.is_authenticated:
            result = CreditRanking.objects.filter(user=request.user).first()
            if result is None:
                result = update_user_credit(request.user)
            rank = CreditRanking.objects.filter(credit__gt=result.credit).count() + 1
            response.data['user_rank'] = rank

        return response


class ProfessionListView(generics.ListAPIView):
    """行业列表"""
    
    serializer_class = ProfessionSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = Profession.objects.all().order_by('-display', 'create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='行业列表',
        responses = DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MajorListView(generics.ListAPIView):
    """专业列表"""
    
    serializer_class = MajorSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = Major.objects.all().order_by('-display', 'create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='专业列表',
        responses = DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def get(self, request: Request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class UserAuditView(mixins.CreateModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
    """提交/获取认证申请"""

    queryset = UserAudit.objects.all()
    # serializer_class = UserAuditSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None

    def filter_queryset(self, queryset):
        if self.request.method == 'GET':
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserAuditPostSerializer
        return UserAuditSerializer

    @swagger_auto_schema(
        operation_summary='提交认证申请',
        operation_description="提交认证申请",
        request_body=UserAuditPostSerializer,
        responses = DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def post(self, request, *args, **kwargs):
        res = self.create(request, *args, **kwargs)
        return res

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

        user.status = UserAudit.Status.PROCESSING
        user.save()

    @swagger_auto_schema(
        operation_summary='获取认证申请',
        operation_description="获取认证申请",
        responses = {
            status.HTTP_200_OK: UserAuditSerializer
        } | DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)



class UserAuditUpdateView(mixins.UpdateModelMixin, generics.GenericAPIView):
    """修改认证申请"""

    queryset = UserAudit.objects.all()
    serializer_class = UserAuditPostSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='修改认证申请',
        responses = DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # 修改后状态变更为审核中
        serializer.save(status=UserAudit.Status.PROCESSING)

        user = self.request.user
        user.status = UserAudit.Status.PROCESSING
        user.save()


class ExpertView(mixins.UpdateModelMixin, generics.GenericAPIView):
    """获取/修改专家信息"""

    # serializer_class = ExpertSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return ExpertUpdateSerializer
        else:
            return ExpertSerializer

    @swagger_auto_schema(
        operation_summary='获取专家信息',
        operation_description='获取专家信息',
        responses = {
            status.HTTP_200_OK: ExpertSerializer
        } | DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def get(self, request: Request, *args, **kwargs):
        if request.user.status != UserAudit.Status.PASSED:
            raise Http404
        audit = get_object_or_404(UserAudit, user=request.user, status=UserAudit.Status.PASSED)
        expert, _ = Expert.objects.get_or_create(user=request.user, defaults={
            'name': audit.name,
            'profession_ids': audit.profession_ids,
            'major_ids': audit.major_ids,
        })

        return Response(ExpertSerializer(expert, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary='修改专家信息',
        operation_description='修改专家信息',
        request_body=ExpertUpdateSerializer,
        responses = {
            status.HTTP_200_OK: ExpertUpdateSerializer
        } | DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get_object(self) -> Expert:
        user: User = self.request.user
        if user.status != UserAudit.Status.PASSED:
            raise Http404
        audit = get_object_or_404(UserAudit, user=user, status=UserAudit.Status.PASSED)
        expert, _ = Expert.objects.update_or_create(user=user, defaults={
            'name': audit.name,
            'profession_ids': audit.profession_ids,
            'major_ids': audit.major_ids,
        })
        return expert

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ExpertDetailView(generics.RetrieveAPIView):
    """获取专家信息"""

    queryset = Expert.objects.all()
    serializer_class = ExpertSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(
        operation_summary='获取专家信息',
        responses = {
            status.HTTP_200_OK: ExpertSerializer
        } | DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ExpertListView(generics.ListAPIView):
    """专家列表"""
    
    serializer_class = ExpertSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = Expert.objects.filter(user__status=UserAudit.Status.PASSED)

        query_params: QueryDict = self.request.query_params

        # 行业
        profession_ids = query_params.get('profession_ids', '')
        if type(profession_ids) is str and len(profession_ids) > 0:
            condition = None
            for id in profession_ids.split(','):
                sub_condition = Q(profession_ids=id)|Q(profession_ids__startswith=id+',')|Q(profession_ids__contains=','+id+',')|Q(profession_ids__endswith=','+id)
                if condition is None:
                    condition = sub_condition
                else:
                    condition |= sub_condition
            queryset = queryset.filter(condition)

        # 专业
        major_ids = query_params.get('major_ids', '')
        if type(major_ids) is str and len(major_ids) > 0:
            condition = None
            for id in major_ids.split(','):
                sub_condition = Q(major_ids=id)|Q(major_ids__startswith=id+',')|Q(major_ids__contains=','+id+',')|Q(major_ids__endswith=','+id)
                if condition is None:
                    condition = sub_condition
                else:
                    condition |= sub_condition
            queryset = queryset.filter(condition)

        # 等级
        level = query_params.get('level', '')
        if type(level) is str and len(level) > 0:
            level_list = list(map(int, level.split(',')))
            queryset = queryset.filter(level__in=level_list)

        # 排序
        order_by = query_params.get('order_by', 0)
        if int(order_by) == 0:
            queryset = queryset.order_by('-score')
        else:
            queryset = queryset.order_by('score')

        return queryset

    @swagger_auto_schema(
        operation_summary='专家列表',
        manual_parameters= [
            openapi.Parameter('order_by', openapi.IN_QUERY, description="排序 - 0:评分降序,1:评分升序", type=openapi.TYPE_INTEGER, default=0),
            openapi.Parameter('profession_ids', openapi.IN_QUERY, description="行业id，多个id以英文逗号分隔", type=openapi.TYPE_STRING, required=False, default=''),
            openapi.Parameter('major_ids', openapi.IN_QUERY, description="专业id，多个id以英文逗号分隔", type=openapi.TYPE_STRING, required=False, default=''),
            openapi.Parameter('level', openapi.IN_QUERY, description="专家等级 - 0:一级,1:二级,2:三级", type=openapi.TYPE_STRING, required=False, default=''),
        ],
        responses = DEFAULT_RESPONSES,
        tags=['专家', '咨询'],
    )
    def get(self, request: Request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class UserTopicListView(generics.ListAPIView):
    """我的提问"""

    from topic.serializers import TopicSerializer

    serializer_class = TopicSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        from topic.models import Topic
        queryset = Topic.objects.filter(user=self.user, status=int(self.status)).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='我的提问',
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, '用户id', type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('status', openapi.IN_QUERY, '状态 - 0:审核中,1:审核通过,2:审核驳回', type=openapi.TYPE_INTEGER, default=0),
        ],
        responses = DEFAULT_RESPONSES,
        tags=['我的'],
    )
    def get(self, request: Request, *args, **kwargs):
        user_id = request.query_params.get('user_id', 0)
        self.user = get_object_or_404(User, pk=int(user_id))

        status = request.query_params.get('status', 0)
        if status is None or status == '':
            status = 0
        # 查看其他用户时，只能查看审核通过的问题
        if request.user.is_anonymous or request.user.pk != self.user.pk:
            status = 1
        self.status = status

        return super().list(request, *args, **kwargs)



class UserTopicReplyListView(generics.ListAPIView):
    """我的回复"""
    from topic.serializers import TopicReplySerializer

    serializer_class = TopicReplySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        from topic.models import TopicReply

        queryset = TopicReply.objects.filter(
            user=self.request.user,
            status=0,
        ).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='我的回复列表',
        operation_description='我的回复列表',
        responses = DEFAULT_RESPONSES,
        tags=['我的'],
    )
    def get(self, request: HttpRequest, *args, **kwargs):
        from topic.models import TopicReplyLiked, TopicReply

        response = super().get(request, *args, **kwargs)

        # 标记是否已点赞
        if request.user.is_authenticated:
            user_liked = TopicReplyLiked.objects.filter(user=request.user).values_list('reply', flat=True)
            user_liked_ids = list(user_liked)

            topic_reply_pk_name = TopicReply._meta.pk.name
            results = response.data.get('results', [])
            for reply in results:
                reply['is_liked'] = 1 if reply[topic_reply_pk_name] in user_liked_ids else 0

        return response



class ExpertReviewListView(generics.ListAPIView):
    """专家的评论列表"""

    from order.serializers import ReviewSerializer

    serializer_class = ReviewSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        from order.models import Review
        queryset = Review.objects.filter(order__expert=self.expert).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='专家的评论列表',
        responses = DEFAULT_RESPONSES,
        tags=['专家'],
    )
    def get(self, request, *args, **kwargs):
        expert_id = kwargs.get('expert_id', 0)
        self.expert = get_object_or_404(Expert, pk=int(expert_id))
        return super().get(request, *args, **kwargs)


class UserKnowledgeListView(generics.ListAPIView):
    """我的视频"""

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        from knowledge.serializers import KnowledgeOrderDetailSerializer
        return KnowledgeOrderDetailSerializer

    def get_queryset(self):
        from knowledge.models import KnowledgeOrder
        queryset = KnowledgeOrder.objects.filter(
            user=self.request.user,
            pay_status=KnowledgeOrder.PayStatus.PAID,
        ).order_by('-create_time')
        return queryset

    @swagger_auto_schema(
        operation_summary='我的视频',
        operation_description='用户购买的视频',
        responses = DEFAULT_RESPONSES,
        tags=['我的', '视频'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
