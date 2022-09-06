from django.db import models

# Create your models here.

class WxAccessTokenCache(models.Model):
    """微信 access_token 缓存"""

    token = models.CharField('access_token', max_length=512)
    expire_time = models.DateTimeField('过期时间')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return str(self.token)

    class Meta:
        verbose_name = '微信 access_token 缓存'
        verbose_name_plural = verbose_name
        db_table = 'wx_access_token_cache'
        ordering = ('-expire_time',)
