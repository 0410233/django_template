from uuid import uuid4
from datetime import datetime, date, time, timedelta

from django.conf import settings
from django.utils.html import format_html
from django.utils import timezone

from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        data = {}
        data['errcode'] = response.status_code
        print('error,===', response.data)
        for key, value in response.data.items():
            if type(value) == list:
                data['errmsg'] = value[0]
            else:
                if key == 'detail':
                    data['errmsg'] = value
                else:
                    data['errmsg'] = key + value
            break
        response.data = data

    return response



def get_file_path(instance, filename: str):
    ext = filename.split('.').pop()
    filename = '{}.{}'.format(uuid4().hex, ext)
    now = timezone.localtime(timezone=timezone.get_default_timezone())
    return "uploads/%d/%02d/%02d/%s"%(now.year, now.month, now.day, filename)


def generate_order_sn(prefix, suffix):
    """生成订单号"""
    import random

    prefix = str(prefix)[-2:]
    suffix = str(suffix)[-2:]

    # 当前日期时间
    local_time = timezone.localtime().strftime('%Y%m%d%H%M%S')[-12:]

    # 前缀（后2位）+ 下单时间的年月日12 + 后缀（后2位）+ 随机数4位
    result = prefix + local_time + suffix + str(random.randint(1000, 9999))

    return result


def choices_to_str(choices):
    from django.db.models import IntegerChoices
    if issubclass(choices, IntegerChoices):
        choices = choices.choices
    keyvalues = [str(choice[0])+':'+str(choice[1] or '') for choice in choices]
    return ','.join(keyvalues)


def admin_text_view(content, width=200):
    if content is None:
        return '-'
    content = str(content)
    if len(content) < 1:
        return '-'
        
    import html
    content = html.escape(content)
    return format_html(
        '<span style="display:inline-block;max-width:{}px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{}">{}</span>',
        str(width),
        content,
        content,
    )


def admin_image_view(image):
    if image is None or image == '':
        return '-'
    url = settings.MEDIA_URL + image
    return format_html(
        '<a href="{}" target="_top" title="{}" style="display:inline-block;width:50px;height:50px;box-sizing:border-box;padding:1px;border:1px solid #eee;border-radius:2px;background:#fff;"><img style="width:100%;height:100%;object-fit:contain;" src="{}"></a>',
        url,
        image,
        url,
    )

def admin_file_view(file: str, link_text=None):
    if file is None or file == '':
        return '-'
    url = settings.MEDIA_URL + file
    if link_text is None:
        link_text = file.split('/').pop()
    return format_html(
        '<a href="{}" target="_top" title="{}">{}</a>',
        url,
        file,
        link_text,
    )

def admin_media_view(media: str, link_text=None):
    if media is None or media == '':
        return '-'
    ext = media.split('.').pop()
    if ext.lower() in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp']:
        return admin_image_view(media)
    else:
        return admin_file_view(media, link_text)


DEFAULT_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: '业务异常，具体message提示。',
    status.HTTP_401_UNAUTHORIZED: '系身份验证失败（token过期或非法账号）',
    status.HTTP_403_FORBIDDEN: '没权限',
    status.HTTP_404_NOT_FOUND: '请求路径不存在',
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: '客户发送的请求大小超过了2MB限制。',
    status.HTTP_500_INTERNAL_SERVER_ERROR: '系统内部异常',
    status.HTTP_502_BAD_GATEWAY: '网关异常'
}


def get_time_range(now=None, scope='month') -> tuple[datetime, datetime]:
    """获取时间范围"""

    tz = timezone.get_current_timezone()
    if isinstance(now, datetime) and now.tzinfo is not None:
        tz = now.tzinfo

    if now is None:
        now = timezone.localtime(timezone=tz)
    elif isinstance(now, datetime):
        now = now.astimezone(tz)
    elif isinstance(now, date):
        now = datetime.combine(now, time.min, tz)
    else:
        now = timezone.localtime(timezone=tz)

    # 月
    if scope == 'month':
        import calendar
        _, last_day = calendar.monthrange(now.year, now.month)
        start_time = timezone.datetime(
            year=now.year, month=now.month, day=1,
            hour=0, minute=0, second=0, microsecond=0,
            tzinfo=tz
        )
        end_time = start_time.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        start_time = start_time.astimezone(timezone.utc)
        end_time = end_time.astimezone(timezone.utc)

    # 天
    elif scope == 'day':
        start_time = timezone.datetime(
            year=now.year, month=now.month, day=now.day,
            hour=0, minute=0, second=0, microsecond=0,
            tzinfo=tz
        )
        end_time = start_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_time = start_time.astimezone(timezone.utc)
        end_time = end_time.astimezone(timezone.utc)
    
    # 周
    elif scope == 'week':
        weekday = now.weekday()
        start_time = timezone.datetime(
            year=now.year, month=now.month, day=now.day,
            hour=0, minute=0, second=0, microsecond=0,
            tzinfo=tz
        )
        start_time = start_time - timedelta(days=weekday)
        end_time = start_time + timedelta(days=6)
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_time = start_time.astimezone(timezone.utc)
        end_time = end_time.astimezone(timezone.utc)
        
    # 年
    elif scope == 'year':
        start_time = timezone.datetime(
            year=now.year, month=1, day=1,
            hour=0, minute=0, second=0, microsecond=0,
            tzinfo=tz
        )
        end_time = timezone.datetime(
            year=now.year, month=12, day=31,
            hour=23, minute=59, second=59, microsecond=999999,
            tzinfo=tz
        )
        
        start_time = start_time.astimezone(timezone.utc)
        end_time = end_time.astimezone(timezone.utc)
        
    else:
        start_time = timezone.now()
        end_time = timezone.now()

    return (start_time, end_time)
