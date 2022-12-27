from django.contrib import admin
from django.utils.html import format_html, format_html_join, mark_safe
from django.conf import settings

from user.admin import BaseAdmin
from . import models

from server.utils import admin_image_view, admin_text_view


# Register your models here.

@admin.register(models.Article)
class ArticleAdmin(BaseAdmin):
    search_fields = ('title', 'content', )
    list_filter = ("status", "is_carousel", )
    list_display = ("id", "cate", "view_title", "status", "is_carousel", "view_carousel_image", "create_time", "modify_time", )
    ordering = ('-modify_time',)

    @admin.display(description='标题')
    def view_title(self, obj):
        return admin_text_view(obj.title)

    @admin.display(description='顶部大图')
    def view_banner(self, obj):
        if obj.banner:
            return admin_image_view(obj.banner.name)
        return '-'

    @admin.display(description='轮播图')
    def view_carousel_image(self, obj):
        if obj.carousel_image:
            return admin_image_view(obj.carousel_image.name)
        return '-'
