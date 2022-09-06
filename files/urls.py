from django.urls import re_path
from django.urls import path
from . import views

urlpatterns = [

    #图片
    re_path(r'^upload/$', views.ImagesList.as_view(), name='images-list'),

    re_path(r'^upload/pc/$', views.ImagesListPC.as_view(), name='images-list-pc'),
]
