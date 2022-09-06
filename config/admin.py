from django.contrib import admin

from . import models
from user.admin import BaseAdmin

# Register your models here.

@admin.register(models.Config)
class ConfigAdmin(BaseAdmin):

    list_filter = ('group', 'scope')
    list_display = ('name', 'value', 'display', 'group', 'scope')
    readonly_fields = ('key','name',)
    ordering = ('-display', 'id')
    # readonly_fields = ('name',)
