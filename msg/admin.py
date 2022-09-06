from django.contrib import admin
from . import models
from user.admin import BaseAdmin
from user.models import User
from django.conf import settings
from django.utils.html import format_html, format_html_join, mark_safe

# Register your models here.

@admin.register(models.Msg)
class MsgAdmin(BaseAdmin):
    search_fields = ('user__username', "content", )
    list_display = ("msg_id", 'title', 'type', "user", "content", "create_time", )
    ordering = ('-create_time',)

    raw_id_fields = ('user', )
    # autocomplete_fields = ('user',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)




@admin.register(models.MsgReaded)
class MsgReadedAdmin(BaseAdmin):
    search_fields = ('id', 'user__name', "msg__content", )
    list_display = ("id", "msg", "user", "create_time", )
    ordering = ('-create_time',)




