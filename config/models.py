from django.db import models
from server.utils import choices_to_str


# Create your models here.


class Config(models.Model):
    """扩展配置"""

    class Group(models.IntegerChoices):
        DEFAULT = 0, '默认分组'
    
    key = models.CharField('key', max_length=50, unique=True)
    value = models.CharField('value', max_length=1000, blank=True, null=True)
    name = models.CharField('名称', max_length=50)
    group = models.SmallIntegerField('分组', blank=True, default=0, choices=Group.choices, help_text=choices_to_str(Group))
    scope = models.SmallIntegerField('范围', blank=True, default=0, choices=[(0,'全部可见'),(1,'仅后端')], help_text='仅后端可见的配置项前端不会获取到')
    display = models.IntegerField('显示顺序', blank=True, default=0, help_text='大的靠前')

    def __str__(self):
        return str(self.key)

    class Meta:
        verbose_name = '扩展配置'
        verbose_name_plural = verbose_name
        ordering = ('-display', 'id')
        db_table = 'config'


def get_config(key=None, default=None):
    if key is not None:
        record = Config.objects.filter(key=key).first()
        if record:
            return record.value
        else:
            return default
    queryset = Config.objects.all()
    dic = {}
    for setting in queryset:
        dic[setting.key] = setting.value

    return dic


# def getSettingInfo(key=None):
#     if key is not None:
#         record = SettingInfo.objects.filter(key=key).first()
#         if record:
#             return record.value
#         else:
#             return None
#     queryset = SettingInfo.objects.all()
#     dic = {}
#     for setting in queryset:
#         dic[setting.key] = setting.value

#     return dic
