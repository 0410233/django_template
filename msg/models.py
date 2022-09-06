from django.db import models

from server.utils import choices_to_str

# Create your models here.

class Msg(models.Model):
    
    class Type(models.IntegerChoices):
        SYSTEM  = 0, '系统'
        CONSULT = 1, '咨询'

    class TargetType(models.IntegerChoices):
        TOPIC = 0, '问题'
        TOPIC_REPLY = 1, '回答'
        TOPIC_REPLY_COMMENT = 2, '评论'

    msg_id = models.AutoField('消息id', help_text='消息id', primary_key=True)
    type = models.IntegerField(verbose_name='类型', default=Type.SYSTEM, choices=Type.choices, help_text=choices_to_str(Type))
    user = models.ForeignKey('user.User', null=True, blank=True, on_delete=models.CASCADE, help_text='用户id', verbose_name='用户id')
    title = models.CharField('标题', null=True, blank=True, max_length=50, help_text='标题')
    content = models.TextField('内容', help_text='内容')
    
    target_type = models.SmallIntegerField('跳转目标', blank=True, null=True, choices=TargetType.choices, help_text=choices_to_str(TargetType))
    target_id = models.IntegerField('跳转目标id', blank=True, null=True)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return str(self.content)

    class Meta:
        verbose_name_plural = '消息'
        verbose_name = verbose_name_plural
        ordering = ('-create_time',)
        indexes = [
            models.Index(fields=['user', 'create_time']),
            models.Index(fields=['create_time']),
        ]



class MsgReaded(models.Model):
    msg = models.ForeignKey('Msg', on_delete=models.CASCADE, help_text='消息id', verbose_name='消息id')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, help_text='用户id', verbose_name='用户id')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return str(self.msg)

    class Meta:
        verbose_name_plural = '消息已读记录'
        verbose_name = verbose_name_plural
        ordering = ('-create_time',)
        indexes = [
            models.Index(fields=['user', 'create_time']),
            models.Index(fields=['create_time']),
        ]



