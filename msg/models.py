from django.db import models

from server.utils import choices_to_str

# Create your models here.

class Msg(models.Model):
    """消息"""
    
    class Type(models.IntegerChoices):
        SYSTEM  = 0, '系统'
        ORDER  = 1, '订单'

    class LinkType(models.IntegerChoices):
        OTHER = 0, '其他'

    type = models.IntegerField('类型', default=Type.SYSTEM, choices=Type.choices, help_text=choices_to_str(Type))
    title = models.CharField('标题', blank=True, default='', max_length=50)
    content = models.TextField('内容')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='用户id', blank=True, null=True)

    link_type = models.SmallIntegerField('链接类型', blank=True, default=0, choices=LinkType.choices, help_text=choices_to_str(LinkType))
    link = models.CharField('链接', max_length=200, blank=True, null=True)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%d-%s'%(self.pk, self.title)

    class Meta:
        verbose_name = '消息'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)



class MsgRead(models.Model):
    """消息已读记录"""

    msg = models.ForeignKey('Msg', on_delete=models.CASCADE, verbose_name='消息id')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='用户id')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s -- %s'%(str(self.msg), str(self.user))

    class Meta:
        verbose_name = '消息已读记录'
        verbose_name_plural = verbose_name
        ordering = ('-create_time',)
