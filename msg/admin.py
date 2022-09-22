from django.contrib import admin

from user.admin import BaseAdmin
from server.utils import admin_text_view

from .models import *

# Register your models here.

@admin.register(Msg)
class MsgAdmin(BaseAdmin):
    search_fields = ('user__username', "content", )
    list_display = ("id", 'title', "view_content", 'type', "user", "create_time", )
    ordering = ('-create_time',)

    raw_id_fields = ('user', )
    # autocomplete_fields = ('user',)

    def view_content(self, obj):
        return admin_text_view(obj.content)



@admin.register(MsgRead)
class MsgReadAdmin(BaseAdmin):
    search_fields = ('id', 'user__name', "msg__content", )
    list_display = ("id", "msg", "user", "create_time", )
    ordering = ('-create_time',)
