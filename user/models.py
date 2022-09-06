import datetime
import json
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import AbstractUser

from server.utils import choices_to_str

# Create your models here.


def get_file_path(instance,filename):
    ext = filename.split('.')[-1]
    #日期目录和 随机文件名
    filename = '{}.{}'.format(uuid4().hex, ext)
    year = datetime.datetime.now().year
    month =datetime.datetime.now().month
    day = datetime.datetime.now().day
    return "uploads/{0}/{1}/{2}/{3}".format(year,month,day,filename)


class User(AbstractUser):

    class Gender(models.IntegerChoices):
        UNKNOWN = 0, '未知'
        MALE = 1, '男'
        FEMALE = 2, '女'
     
    class Status(models.IntegerChoices):
        INITIAL     = -1, '初始化'
        PROCESSING  = 0, '审核中'
        FAILED      = 1, '审核未通过'
        PASSED      = 2, '审核通过'

    openid = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name='小程序openid', help_text='必填，小程序openid 最多限50个字符')
    unionid = models.CharField('微信unionid', blank=True, null=True, max_length=50, unique=True, help_text='必填，微信unionid 最多限50个字符')
    session_key = models.CharField('小程序密钥', blank=True, null=True, max_length=50, help_text='必填，小程序密钥 最多限50个字符')
    wx_user_info = models.TextField('微信用户信息json', blank=True, null=True, help_text='微信用户信息json')
    name = models.CharField('用户昵称', blank=True, null=True, max_length=50, help_text='用户昵称')
    avatar = models.ImageField('头像', blank=True, null=True, upload_to=get_file_path, max_length=500,help_text='头像')
    gender = models.IntegerField('性别', blank=True, default=Gender.UNKNOWN, choices=Gender.choices, help_text=choices_to_str(Gender))
    birthday = models.DateField('生日', blank=True, null=True, help_text='生日')
    status = models.IntegerField('状态', blank=True, default=Status.INITIAL, choices=Status.choices, help_text=choices_to_str(Status))

    def __str__(self):
        return '{}-{}'.format(str(self.pk), self.get_user_name())

    def get_user_name(self):
        if self.name:
            return self.name
        try:
            wx_user_info = self.wx_user_info
            if wx_user_info:
                wx_info = json.loads(wx_user_info)
                return wx_info.get('nickname', '')
        except json.decoder.JSONDecodeError:
            pass
        return ''

    def get_expert_info(self):
        return Expert.objects.filter(user=self).first()

    def get_follow_count(self):
        return Fans.objects.filter(user=self).exclude(to_user=self).count()
        
    def get_fans_count(self):
        return Fans.objects.filter(to_user=self).exclude(user=self).count()
       
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name



class Feedback(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, help_text='用户id', verbose_name='用户id')
    content = models.TextField(verbose_name='内容 ', help_text='内容')
    status = models.IntegerField('状态 0未处理1已处理', choices=[(0, '未处理'), (1, '已处理')], default=0, help_text='状态 0未处理1已处理')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):

        return str(self.content)

    class Meta:
        verbose_name = '意见反馈'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)
        indexes = [
            models.Index(fields=['create_time']),
        ]



class QA(models.Model):
    question = models.CharField('问题', max_length=200, help_text='问题')
    answer = models.TextField('答案', help_text='答案')
    display = models.IntegerField('显示顺序', default=0, help_text='小的显示在前面')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):

        return str(self.question)

    class Meta:
        verbose_name_plural = '常见问题'
        verbose_name = verbose_name_plural
        ordering = ('-modify_time',)
        indexes = [
            models.Index(fields=['modify_time']),
        ]



class CreditLog(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='用户id', help_text='用户id')
    title = models.CharField('标题', null=True, blank=True, max_length=50, help_text='标题')
    credit = models.IntegerField(verbose_name='积分 有负数')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):

        return str(self.user) + '---' + str(self.title)

    class Meta:
        verbose_name_plural = '积分记录'
        verbose_name = verbose_name_plural
        ordering = ('-modify_time',)
        indexes = [
            models.Index(fields=['modify_time']),
            models.Index(fields=['create_time']),
        ]



class MoneyLog(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='用户id', help_text='用户id')
    title = models.CharField('标题', max_length=50, blank=True, null=True, help_text='标题')
    money = models.FloatField('金额', help_text='余额变动值，有负数')
    platform_cut = models.FloatField('平台抽成', blank=True, default=0)
    
    reference = models.CharField('参考值', max_length=100, blank=True, null=True, help_text='用来确定某些记录是否唯一')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return str(self.user) + '---' + str(self.title)

    class Meta:
        verbose_name_plural = '余额记录'
        verbose_name = verbose_name_plural
        ordering = ('-modify_time',)
        indexes = [
            models.Index(fields=['modify_time']),
            models.Index(fields=['create_time']),
        ]


class WithdrawLog(models.Model):
    
    class AuditStatus(models.IntegerChoices):
        CREATED = 0, '审核中'
        PASSED  = 1, '审核通过'
        FAILED  = 2, '拒绝申请'

    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='用户id', help_text='用户id')
    money = models.FloatField('金额', default=0, help_text='金额')
    status = models.IntegerField('提现状态', choices=[(0, '失败'), (1, '成功')], default=0, help_text='提现状态 0失败1成功')
    audit_status = models.IntegerField('审核状态', choices=AuditStatus.choices, default=AuditStatus.CREATED, help_text='审核状态 - ' + choices_to_str(AuditStatus))
    number = models.CharField('订单号', null=True, blank=True, max_length=50, help_text='订单号', unique=True)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('最后操作时间', auto_now=True)

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = '提现记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['modify_time']),
            models.Index(fields=['user', 'create_time']),
        ]
        db_table = 'withdraw_log'



class Fans(models.Model):
    """关注列表"""
    
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='fans', verbose_name='用户id', help_text='用户id')
    to_user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='follow', verbose_name='关注的人', help_text='关注的人')
    type = models.IntegerField('类型', blank=True, default=0, choices=[(0, '关注'), (1, '互关')], help_text='类型 - 0:关注,1:互关')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = '关注列表'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)
        db_table = 'user_fans'


class Profession(models.Model):
    """行业"""
    
    name = models.CharField('行业名称', max_length=45)
    display = models.IntegerField('显示顺序', blank=True, default=0, help_text='大的排在前面')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self) -> str:
        return '{}-{}'.format(str(self.pk), self.name)

    class Meta:
        verbose_name = '行业'
        verbose_name_plural = verbose_name
        ordering = ('-display', 'create_time',)
        db_table = 'profession'


class Major(models.Model):
    """专业"""
    
    name = models.CharField('专业名称', max_length=45)
    display = models.IntegerField('显示顺序', blank=True, default=0, help_text='大的排在前面')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self) -> str:
        return '{}-{}'.format(str(self.pk), self.name)

    class Meta:
        verbose_name = '专业'
        verbose_name_plural = verbose_name
        ordering = ('-display', 'create_time',)
        db_table = 'major'



class UserAudit(models.Model):
    """认证申请"""
    
    class Status(models.IntegerChoices):
        PROCESSING = 0, '审核中'
        FAILED  = 1, '审核未通过'
        PASSED  = 2, '审核通过'

    user = models.OneToOneField('user.User', on_delete=models.CASCADE, verbose_name='用户id', help_text='用户id')
    name = models.CharField('姓名', max_length=45, help_text='姓名')
    mobile = models.CharField('联系方式', max_length=45, help_text='联系方式')
    
    profession_ids = models.CharField('行业id', max_length=100, help_text='多个id以英文逗号分隔')
    major_ids = models.CharField('专业id', max_length=100, help_text='多个id以英文逗号分隔')

    id_front_img = models.ImageField('身份证正面图片', max_length=500, blank=True, default='', upload_to=get_file_path, help_text='身份证正面图片')
    id_reverse_img = models.ImageField('身份证反面图片', max_length=500, blank=True, default='', upload_to=get_file_path, help_text='身份证反面图片')
    image1 = models.ImageField('图片', upload_to=get_file_path, max_length=500)
    image2 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image3 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image4 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image5 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image6 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image7 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image8 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)
    image9 = models.ImageField('图片', upload_to=get_file_path, max_length=500, blank=True, null=True)

    status = models.IntegerField('状态', default=Status.PROCESSING, choices=Status.choices, help_text='状态 - ' + choices_to_str(Status))
    error = models.TextField('未通过的原因', blank=True, default='')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self) -> str:
        return '{}-{}'.format(str(self.pk), self.name)

    def get_profession_list(self):
        """获取行业列表"""
        if len(self.profession_ids) < 1:
            return []
        profession_ids = list(map(int, self.profession_ids.split(',')))
        queryset = Profession.objects.filter(pk__in=profession_ids).order_by('-display', 'create_time')
        return queryset

    def get_major_list(self):
        """获取专业列表"""
        if len(self.major_ids) < 1:
            return []
        major_ids = list(map(int, self.major_ids.split(',')))
        queryset = Major.objects.filter(pk__in=major_ids).order_by('-display', 'create_time')
        return queryset

    class Meta:
        verbose_name = '认证申请'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)
        db_table = 'user_audit'



class Expert(models.Model):
    """专家信息"""
    
    user = models.OneToOneField('user.User', on_delete=models.CASCADE, verbose_name='用户id', help_text='用户id')
    name = models.CharField('姓名', max_length=45)
    # mobile = models.CharField('联系方式', max_length=45)
    photo = models.ImageField('肖像', upload_to=get_file_path, max_length=500, blank=True, null=True)
    profession_ids = models.CharField('行业id', max_length=100, blank=True, default='', help_text='多个id以英文逗号分隔')
    major_ids = models.CharField('专业id', max_length=100, blank=True, default='', help_text='多个id以英文逗号分隔')
    level = models.SmallIntegerField('等级', blank=True, default=0, choices=[(0, '一级专家'),(1, '二级专家'),(2, '三级专家')])
    price = models.FloatField('咨询费', blank=True, default=0)
    intro = models.TextField('个人简介', blank=True, default='')

    order_count = models.IntegerField('咨询次数', blank=True, default=0)
    score = models.FloatField('评分', blank=True, default=0)

    is_carousel = models.SmallIntegerField('首页轮播', default=0, choices=[(0, '否'),(1, '是')], blank=True)
    carousel_image = models.ImageField('首页轮播图', upload_to=get_file_path, max_length=500, blank=True, null=True)

    is_hot = models.SmallIntegerField('首页热门', default=0, choices=[(0, '否'),(1, '是')], blank=True, help_text='是否首页热门专家')
    
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self) -> str:
        return '{}-{}'.format(str(self.pk), self.name)

    def get_profession_list(self):
        """获取行业列表"""
        if len(self.profession_ids) < 1:
            return []
        profession_ids = list(map(int, self.profession_ids.split(',')))
        queryset = Profession.objects.filter(pk__in=profession_ids).order_by('-display', 'create_time')
        return queryset

    def get_major_list(self):
        """获取专业列表"""
        if len(self.major_ids) < 1:
            return []
        major_ids = list(map(int, self.major_ids.split(',')))
        queryset = Major.objects.filter(pk__in=major_ids).order_by('-display', 'create_time')
        return queryset

    class Meta:
        verbose_name = '专家信息'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)
        db_table = 'expert'


class CreditRanking(models.Model):
    """积分排行"""
    
    user = models.OneToOneField('user.User', on_delete=models.CASCADE, verbose_name='用户id')
    credit = models.FloatField('积分')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return '{}-{}'.format(str(self.user), self.credit)

    class Meta:
        verbose_name = '积分排行'
        verbose_name_plural = verbose_name
        ordering = ('-credit', 'modify_time')
        db_table = 'credit_ranking'


def update_user_credit(user: User):
    """计算用户积分"""

    result = CreditLog.objects.filter(user=user).aggregate(sum_credit=models.Sum('credit'))
    credit = result['sum_credit'] or 0

    report, _ = CreditRanking.objects.update_or_create(user=user, defaults={
        'credit': credit,
    })

    return report
