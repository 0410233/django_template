from django.utils import timezone
from django.db import models

from rest_framework import serializers

from server.utils import choices_to_str


# class OrderPaySerializer(serializers.Serializer):
#     """订单付款"""

#     from order.models import Order

#     order_number = serializers.CharField(required=True, write_only=True, help_text='订单编号')
#     pay_channel = serializers.IntegerField(required=False, write_only=True, default=Order.PayChannel.WEIXIN, help_text=choices_to_str(Order.PayChannel))
