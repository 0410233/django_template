from django.urls import path, re_path
from django.urls import path
from . import views

urlpatterns = [
    # 消息列表
    path('list/<int:type>/', views.MsgList.as_view(), name='msg-list'),
    # 新消息数
    path('tips/', views.TipsInfo.as_view(), name='tips-info'),
]

app_name = 'msg'
