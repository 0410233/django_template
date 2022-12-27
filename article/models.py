from django.db import models

from ckeditor_uploader.fields import RichTextUploadingField

from user.models import get_file_path

# Create your models here.


class Article(models.Model):
    """文章"""

    class Cate(models.IntegerChoices):
        OTHER = 0, '其他'
        ABOUT = 1, '关于我们'
        AGREEMENT = 2, '用户协议'
        PRIVACY = 3, '隐私政策'

    title = models.CharField('标题', max_length=50)
    banner = models.ImageField('顶部大图', upload_to=get_file_path, max_length=500, blank=True, null=True)
    content = RichTextUploadingField('内容', blank=True, default='')
    status = models.IntegerField('状态', default=0, choices=[(0, '草稿'), (1, '发布'),], help_text='状态 - 0:草稿,1:发布')

    is_carousel = models.SmallIntegerField('是否首页轮播图', blank=True, default=0, choices=[(0, '否'),(1, '是')])
    carousel_image = models.ImageField('轮播图', upload_to=get_file_path, max_length=500, blank=True, null=True)

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return str(self.pk) + '-' + str(self.title)

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ('-modify_time',)
