from django.urls import path, re_path
from . import views

urlpatterns = [
    # 支付
    path('pay/', views.Pay.as_view(), name='wx-pay'),
    path('notify/wx/', views.WxNotifyOrder.as_view(), name='wx-pay-notify'),
    # 查询支付状态
    path('pay/status/', views.PayStatus.as_view(), name='wx-pay-status'),
    
    # 测试阶段使用，直接付款成功
    path('pay/dev/', views.PayDev.as_view(), name='wx-pay-dev')
]

app_name = 'wx'
