from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdmin1
from django.utils.translation import gettext, gettext_lazy as _
from django.utils.html import format_html, format_html_join, mark_safe
import json
from django.conf import settings

# from platter.views import get_client_ip, getWxPayForC, _order_num
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin

from server.utils import admin_image_view
from .models import *


# Register your models here.

admin.site.site_header = '合合-工厂好医生后台'
admin.site.site_title = '合合-工厂好医生后台管理系统'

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 30


@admin.register(User)
class UserAdmin(UserAdmin1):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', "openid", "unionid", "session_key", "wx_user_info", "name", "avatar", "gender", "birthday", "status" )}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ('username', "openid", "unionid", "session_key", "wx_user_info", "name", )
    list_display = ('id', 'username',"name", 'view_wx_user_name', 'view_wx_user_photo', "gender", 'birthday', 'status', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'gender', )

    list_per_page = 30

    ordering = ('-date_joined',)


    def view_wx_user_name(self, obj):
        wx_str = obj.wx_user_info

        if wx_str is None or len(wx_str) < 1:
            return None

        try:
            dic1 = json.loads(wx_str)
        except json.decoder.JSONDecodeError:
            return None

        return dic1.get('nickname',)

    view_wx_user_name.short_description = '微信昵称'

    def view_wx_user_photo(self, obj):

        if obj.avatar:
            return mark_safe('<a href="'+settings.MEDIA_URL + obj.avatar.name+'"><img target="_top" width=50 heigh=50 src="'+settings.MEDIA_URL+obj.avatar.name+'" /></a>')
        else:
            return '-'

    view_wx_user_photo.short_description = '微信头像'


@admin.register(Feedback)
class FeedbackAdmin(BaseAdmin):
    list_display = ('id', 'user', 'content', 'status','create_time', )
    list_filter = ('status','create_time', )
    ordering = ("-create_time",)
    autocomplete_fields = ("user", )



@admin.register(QA)
class QAAdmin(BaseAdmin):
    list_display = ("id", "question", "answer", "display", "create_time", "modify_time", )
    ordering = ('-modify_time', )



@admin.register(CreditLog)
class CreditLogAdmin(BaseAdmin):
    search_fields = ( "user__name", 'user__username',)
    list_filter = ('create_time', )
    ordering = ("-modify_time",)
    list_display = ("id", "user", "title", "credit", "create_time", "modify_time", )
    autocomplete_fields = ('user', )


@admin.register(MoneyLog)
class MoneyLogAdmin(BaseAdmin):
    search_fields = ( "user__name", 'user__username',)
    list_filter = ('create_time', )
    ordering = ("-modify_time",)
    list_display = ("id", "user", "title", "money", "create_time", "modify_time", )
    autocomplete_fields = ('user', )


@admin.register(WithdrawLog)
class WithdrawLogAdmin(BaseAdmin):
    """提现记录"""

    search_fields = ("number", 'user__name',)
    list_filter = ("status", "audit_status")
    list_display = ('id', 'user', "money", "status", "audit_status", "number", "create_time")
    fields = ('user', "money", "status", "audit_status", "number")
    ordering = ('-create_time',)


@admin.register(Fans)
class FansAdmin(BaseAdmin):
    list_filter = ('type',)
    list_display = ("id", "user", "to_user", 'type', "create_time",)



@admin.register(Profession)
class ProfessionAdmin(BaseAdmin):
    search_fields = ("name",)
    list_display = ("id", "name", 'display', "create_time",)
    list_display_links = ('id', 'name')
    ordering = ('-display', 'create_time')

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "parent":
    #         kwargs["queryset"] = (
    #             Profession.objects.filter(parent=None).order_by('-display', 'create_time')
    #         )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Major)
class MajorAdmin(BaseAdmin):
    search_fields = ("name",)
    list_display = ("id", "name", 'display', "create_time",)
    list_display_links = ('id', 'name')
    ordering = ('-display', 'create_time')


@admin.register(UserAudit)
class UserAuditAdmin(BaseAdmin):
    """认证申请"""

    search_fields = ('name', "mobile",)
    list_filter = ("status",)
    list_display = (
        'id', 'user', "name", "mobile", "profession_ids", "major_ids", "view_image",
        "status", "error", "create_time", "modify_time"
    )
    ordering = ('-create_time',)

    def view_image(self, obj):
        if obj.image1:
            return admin_image_view(obj.image1.name)
        return '-'
    view_image.short_description = '图片'

    def save_model(self, request, obj: UserAudit, form, change):
        super().save_model(request, obj, form, change)
        user: User = obj.user
        user.status = obj.status
        if obj.status == UserAudit.Status.PASSED:
            user.name = obj.name
        user.save()

        if obj.status == UserAudit.Status.PASSED:
            Expert.objects.get_or_create(user=user, defaults={
                'name': obj.name,
                'profession_ids': obj.profession_ids,
                'major_ids': obj.major_ids,
                'photo': user.avatar.name,
            })


@admin.register(Expert)
class ExpertAdmin(BaseAdmin):
    """专家信息"""

    search_fields = ('name', "intro",)
    list_filter = ("level",)
    list_display = (
        'id', 'user', "name", "view_photo", "profession_ids", "major_ids",
        "level", "price", "intro", "is_carousel", "carousel_image", "is_hot",
        "order_count", "score", "create_time", "modify_time"
    )
    ordering = ('-create_time',)
    readonly_fields = ("order_count", "score")

    def view_photo(self, obj: Expert):
        if obj.photo:
            return admin_image_view(obj.photo.name)
        return '-'
    view_photo.short_description = '肖像'



@admin.register(CreditRanking)
class CreditRankingAdmin(BaseAdmin):
    """积分排行"""

    list_display = (
        'id', 'user', "credit", "modify_time"
    )
    ordering = ('-credit', 'modify_time')
    readonly_fields = ("user", "credit")
