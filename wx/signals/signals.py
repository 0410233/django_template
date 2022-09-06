from django.dispatch import Signal

# 待支付信号
pre_wx_pay = Signal()

# 已支付信号
post_wx_pay = Signal()
