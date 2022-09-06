import time, random, os
import hashlib

from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, Http404, HttpResponseBadRequest, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import permissions, status, generics, mixins
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.exceptions import ParseError

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from weixin.pay import WeixinPay, WeixinPayError

from server.utils import DEFAULT_RESPONSES
from server import hh_settings
from .WeixinPay import WeixinPayHH

from .signals import signals

# from user.models import User
# from .serializers import *

import logging
logger = logging.getLogger('django')


# Create your views here.


def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_wx_pay(request: HttpRequest = None) -> WeixinPayHH:
    if request is None:
        url = settings.BASE_URL + reverse('wx:wx-pay-notify')
    else:
        url = request.scheme + '://' + request.get_host() + reverse('wx:wx-pay-notify')

    cert_dir = os.path.join(settings.BASE_DIR, 'cert/')

    pay = WeixinPayHH(
        settings.WX_APPID,
        settings.WX_MCH_ID,
        settings.WX_PAY_MCH_KEY,
        url,
        key=cert_dir + 'apiclient_key.pem', # 可选
        cert=cert_dir + 'apiclient_cert.pem', # 可选
    )

    return pay


def wx_refund(pay, number, total_fee, refund_fee):
    """微信退款"""
    if refund_fee > 0 and total_fee > 0:
        if settings.HH_DEBUG:
            total_fee = 1
            refund_fee = 1
        result = pay.refund(
            out_trade_no=number, total_fee=total_fee, refund_fee=refund_fee,
            out_refund_no=number + 'wx'
        )
        if (result['return_code'] == 'SUCCESS' and result['return_msg'] == 'OK'):
            return True
    return False


def get_pay_sign(result):
    # 生成小程序的paySign

    xcx_dic = {}
    xcx_dic['timeStamp'] = result['time_stamp']
    xcx_dic['appId'] = result['appid']
    xcx_dic['nonceStr'] = result['nonce_str']
    xcx_dic['package'] = 'prepay_id=' + result['prepay_id']
    xcx_dic['signType'] = "MD5"

    keys = list(xcx_dic.keys())
    keys.sort()

    xcx_list = []
    for key in keys:
        xcx_list.append(key + '=' + xcx_dic[key])
    xcx_sign_str = '&'.join(xcx_list) + '&key=' + settings.WX_PAY_MCH_KEY
    pay_sign = hashlib.md5(xcx_sign_str.encode(encoding='UTF-8')).hexdigest()

    return pay_sign.upper()


def get_wx_pay_amount(order_sn: str, pay_channel: int):
    """获取需要微信支付的部分"""
    results = signals.pre_wx_pay.send(sender=None, order_sn=order_sn, pay_channel=pay_channel)
    for _, result in results:
        if type(result) is int or type(result) is float:
            return result
    return None



class Pay(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='微信支付',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_sn'],
            properties={
                'order_sn': openapi.Schema(description="订单编号", type=openapi.TYPE_STRING),
                'pay_channel': openapi.Schema(description="付款方式 - 1:微信,2:余额", type=openapi.TYPE_INTEGER, default=1),
            },
        ),
        responses=DEFAULT_RESPONSES,
        tags=['微信']
    )
    def post(self, request: Request, *args, **kwargs):
        # 单号
        order_sn = str(request.data.get('order_sn', ''))
        # 付款方式
        pay_channel = int(request.data.get('pay_channel', 1))

        # 获取需要微信支付的金额
        pay_amount = get_wx_pay_amount(order_sn, pay_channel)
        if pay_amount is None:
            raise Http404('没有该订单')

        if pay_amount <= 0:
            # 处理业务逻辑
            signals.post_wx_pay.send(sender=None, order_sn=order_sn)
            return Response({'paid': True})

        total_fee = int(pay_amount * 100)
        if hh_settings.HH_DEBUG:
            total_fee = 1

        pay = get_wx_pay(request)

        try:
            openid = request.user.openid
            result = pay.unified_order(
                trade_type="JSAPI",
                body='订单支付',
                out_trade_no=order_sn,
                total_fee=str(int(total_fee)),
                openid=openid,
                spbill_create_ip=get_client_ip(request),
            )
            if (result['return_code'] != 'SUCCESS' or result['return_msg'] != 'OK'):
                raise ParseError(result['return_msg'])

            result['time_stamp'] = str(int(time.time()))

            result['pay_sign'] = get_pay_sign(result)

            return Response(result)

        except WeixinPayError as e:
            raise ParseError(str(e))



class WxNotifyOrder(View):
    """微信支付回调"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest):
        pay = get_wx_pay(request)
        data = pay.to_dict(request.body.decode())

        pay = get_wx_pay(request,)

        if not pay.check(data):
            response = HttpResponse()
            response.write(pay.reply("签名验证失败", False))
            return response

        # 处理业务逻辑
        signals.post_wx_pay.send(sender=None, order_sn=data['out_trade_no'])

        response = HttpResponse()
        response.write(pay.reply("OK", True))
        return response


class PayStatus(APIView):
    """查询微信支付状态"""

    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='查询微信支付状态',
        # query_serializer=OrderPaySerializer,
        manual_parameters = [
            openapi.Parameter('order_sn', openapi.IN_QUERY, description="订单编号", required=True, type=openapi.TYPE_STRING),
        ],
        responses=DEFAULT_RESPONSES,
        tags=['微信']
    )
    def get(self, request: Request, *args, **kwargs):
        # 单号
        order_sn = str(request.data.get('order_sn', ''))
        try:
            pay = get_wx_pay(request,)
            res = pay.order_query(out_trade_no=order_sn)
        except WeixinPayError as e:
            raise ParseError(str(e))

        if res['return_code'] == 'SUCCESS' and res['result_code'] == 'SUCCESS' and res['trade_state'] == 'SUCCESS':
            # 处理业务逻辑
            signals.post_wx_pay.send(sender=None, order_sn=order_sn)

            return Response({'paid': True})

        raise ParseError(res['trade_state_desc'])



class PayDev(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_summary='支付（测试）',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_number'],
            properties={
                'order_sn': openapi.Schema(description="订单编号", type=openapi.TYPE_STRING),
                'pay_channel': openapi.Schema(description="付款方式 - 1:微信,2:余额", type=openapi.TYPE_INTEGER, default=1),
            },
        ),
        responses=DEFAULT_RESPONSES,
        tags=['微信']
    )
    def post(self, request: Request, *args, **kwargs):
        # 单号
        order_sn = str(request.data.get('order_sn', ''))
        # 付款方式
        pay_channel = int(request.data.get('pay_channel', 1))

        # 获取需要微信支付的金额
        pay_amount = get_wx_pay_amount(order_sn, pay_channel)
        if pay_amount is None:
            raise Http404('没有该订单')

        # 处理业务逻辑
        signals.post_wx_pay.send(sender=None, order_sn=order_sn)

        return Response({'paid': True})
