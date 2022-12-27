from django.db import models
from server.utils import choices_to_str

# Create your models here.

# class SettingInfo(models.Model):
#     setting_id = models.AutoField('seting_id', help_text='seting_id', primary_key=True)
#     key = models.CharField('key', max_length=50, help_text='key', unique=True)
#     value = models.CharField('value', null=True, blank=True, max_length=1000, help_text='value')
#     name = models.CharField('名称', max_length=50, help_text='名称')


#     def __str__(self):
#         return str(self.key)

#     class Meta:
#         verbose_name_plural = '全局配置'
#         verbose_name = verbose_name_plural


# def getSettingInfo():
#     queryset = SettingInfo.objects.all()
#     dic = {}
#     for setting in queryset:
#         dic[setting.key] = setting.value

#     return dic


class UserSetting(models.Model):
    """用户配置"""

    class Group(models.IntegerChoices):
        OTHER = 0, '其他'
    
    key = models.CharField('key', max_length=50, unique=True)
    value = models.TextField('value', blank=True, null=True)
    name = models.CharField('名称', max_length=50)
    group = models.SmallIntegerField('分组', blank=True, default=Group.OTHER, choices=Group.choices, help_text=choices_to_str(Group))
    scope = models.SmallIntegerField('使用范围', blank=True, default=0, choices=[(0,'全部'),(1,'仅后端')], help_text='仅后端使用的配置项不会被前端获取到')
    display = models.IntegerField('显示顺序', blank=True, default=0, help_text='大的排前面')
    
    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = '用户配置'
        verbose_name_plural = verbose_name
        ordering = ('-display', 'id')
        db_table = 'user_settings'


def get_setting_value(key=None, default=None):
    """获取配置值"""
    if key is not None:
        record = UserSetting.objects.filter(key=key).first()
        if record and record.value is not None:
            return record.value
        return default
    queryset = UserSetting.objects.all()
    dic = {}
    for setting in queryset:
        dic[setting.key] = setting.value
    return dic


def get_settings(*keys, **kwargs):
    """获取配置值"""
    if len(keys) > 0:
        queryset = UserSetting.objects.filter(key__in=keys)
    else:
        queryset = UserSetting.objects.all()
    queryset = queryset.filter(**kwargs)
    result = {}
    for setting in queryset:
        result[setting.key] = setting.value
    return result


def check_bad_words(content: str):
    """检测敏感词"""
    if type(content) is not str or len(content) == 0:
        return None
    
    bad_words = get_setting_value('bad_words', '')
    if type(bad_words) is str and len(content) > 0:
        for word in bad_words.split('|'):
            word = word.strip()
            if word and word in content:
                return word
    return None



class TaskLog(models.Model):
    """后台任务日志"""

    class TaskType(models.IntegerChoices):
        OTHER = 0, '其他'
    
    task_type = models.IntegerField('类型', default=TaskType.OTHER, choices=TaskType.choices)
    remark = models.CharField('备注', max_length=200, blank=True, null=True)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = '后台任务日志'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)
        db_table = 'background_task_log'
