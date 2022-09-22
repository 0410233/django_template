from django.urls import path
from . import views

urlpatterns = [
    #用户相关
    path('', views.UserSettingList.as_view(), name='usersetting-list'),
]

app_name = 'background'
