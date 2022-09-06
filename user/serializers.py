import re

from rest_framework import serializers

from .models import *
import json

from django.conf import settings
from django.utils import timezone
import re
from rest_framework.validators import UniqueValidator


class UserLoginSerializer(serializers.Serializer):

    code = serializers.CharField(
        label= '小程序code',
        max_length=50,
        write_only=True,
        required=True,
        help_text="小程序login返回的code"
    )


class UserMobileModifySerializer(serializers.Serializer):

    encryptedData = serializers.CharField(
        label= '小程序加密数据',
        max_length=10000,
        write_only=True,
        required=True,

    )

    iv = serializers.CharField(
        label= '小程序初始向量',
        max_length=10000,
        write_only=True,
        required=True,

    )


class UserPutSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=False, allow_blank=False, validators=[UniqueValidator(queryset=User.objects.all(), message='手机号已经存在')])

    def validate(self, attrs):
        if 'avatar1' in dict(attrs).keys():
            attrs['avatar'] = attrs['avatar1']
            del attrs['avatar1']


        return attrs

    class Meta:
        model = User
        fields = ('id', 'username', "openid", "unionid", "session_key", "wx_user_info", "name", "avatar", "gender", "birthday", "status", 'date_joined', 'last_login',)
        read_only_fields = ('date_joined', 'last_login', "openid", "unionid", "session_key", 'username', "status", )


class FeedbackPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('user', 'status', )


class QAListSerializer(serializers.ModelSerializer):
    class Meta:
        model = QA
        fields = "__all__"


class CreditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditLog
        fields = "__all__"


class MoneyLogSerializer(serializers.ModelSerializer):
    """余额记录"""
    
    class Meta:
        model = MoneyLog
        fields = '__all__'


class WithdrawLogSerializer(serializers.ModelSerializer):
    """提现记录"""

    class Meta:
        model = WithdrawLog
        fields = '__all__'
        read_only_fields = ('user', 'number', 'status', 'audit_status')


class ProfessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profession
        fields = ('id', 'name')


class MajorSerializer(serializers.ModelSerializer):

    # parent = ProfessionSerializer()
    
    class Meta:
        model = Major
        fields = ('id', 'name',)


class UserAuditPostSerializer(serializers.ModelSerializer):

    id_front_img = serializers.CharField(required=True, write_only=True, allow_blank=True, help_text='身份证正面图片', )
    id_reverse_img = serializers.CharField(required=True, write_only=True, allow_blank=True, help_text='身份证反面图片', )
    image1 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image2 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image3 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image4 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image5 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image6 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image7 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image8 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )
    image9 = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='图片', )

    class Meta:
        model = UserAudit
        fields = "__all__"
        read_only_fields = ("user", "status", "error")



class UserAuditSerializer(serializers.ModelSerializer):

    profession_list = ProfessionSerializer(many=True, source='get_profession_list')
    major_list = MajorSerializer(many=True, source='get_major_list')
    
    class Meta:
        model = UserAudit
        exclude = ('profession_ids', 'major_ids')



class ExpertUpdateSerializer(serializers.ModelSerializer):
    """专家信息更新"""
   
    photo = serializers.CharField(required=False, write_only=True, allow_blank=True, help_text='肖像', )

    class Meta:
        model = Expert
        fields = '__all__'
        read_only_fields = (
            'user', 'level', 'price', 'is_carousel', 'carousel_image',
            'is_hot', 'order_count', 'score',
        )


class ExpertSerializer(serializers.ModelSerializer):
    """专家信息"""
   
    profession_list = ProfessionSerializer(many=True, source='get_profession_list')
    major_list = MajorSerializer(many=True, source='get_major_list')
    
    class Meta:
        model = Expert
        # fields = '__all__'
        exclude = ('profession_ids', 'major_ids')
        read_only_fields = ('user', 'level', 'price', 'order_count', 'score')


class UserSerializer(serializers.ModelSerializer):

    wx_user_info = serializers.SerializerMethodField()
    def get_wx_user_info(self, obj):
        wx_str = obj.wx_user_info
        dic = {}
        try:
            if wx_str and len(wx_str):
                dic = json.loads(wx_str)
        except json.decoder.JSONDecodeError:
            pass
        return dic

    expert_info = ExpertSerializer(read_only=True, source='get_expert_info', help_text='专家信息')

    follow_count = serializers.IntegerField(read_only=True, source='get_follow_count', help_text='关注数')
    fans_count = serializers.IntegerField(read_only=True, source='get_fans_count', help_text='粉丝数')
    is_followed = serializers.IntegerField(read_only=True, default=0, help_text='是否已关注')

    class Meta:
        model = User
        fields = (
            'id', 'username', "openid", "unionid", 'is_active',
            "wx_user_info", "name", "avatar", "gender", "birthday",
            "status", 'date_joined', 'last_login',
            'follow_count', 'fans_count', 'is_followed', 'expert_info',
        )
        read_only_fields = (
            'expert_info', 'follow_count', 'fans_count', 'is_followed',
        )


class UserSimpleSerializer(serializers.ModelSerializer):

    expert_info = ExpertSerializer(read_only=True, source='get_expert_info', help_text='专家信息')

    class Meta:
        model = User
        fields = (
            'id', "name", "avatar", "gender", "birthday", "status", "expert_info",
        )
        read_only_fields = ('expert_info',)


class FansSerializer(serializers.ModelSerializer):
    """关注列表"""

    user = UserSimpleSerializer()
    to_user = UserSimpleSerializer()
    
    class Meta:
        model = Fans
        fields = ('id', 'user', 'to_user', 'type', 'create_time')


class CreditRankingSerializer(serializers.ModelSerializer):
    """积分排行"""

    user = UserSimpleSerializer()
    rank = serializers.IntegerField(help_text='排名', default=0)
    
    class Meta:
        model = CreditRanking
        fields = '__all__'
