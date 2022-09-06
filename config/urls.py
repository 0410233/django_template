from django.urls import path
from . import views

urlpatterns = [
    #用户相关
    path('', views.ConfigList.as_view(), name='config'),
]

app_name = 'config'
