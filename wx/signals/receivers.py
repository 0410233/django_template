
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .signals import *

import logging
logger = logging.getLogger('django')


# @receiver(post_save, sender=CreditLog, dispatch_uid='on_creditlog_created')
# def on_creditlog_created(sender, instance: CreditLog, created, **kwargs):
#     """接收信号：创建积分日志"""

#     if created:
#         try:
#             # logger.warning('===== 接收信号：创建积分日志后更新积分排行 =====')
#             update_user_credit(instance.user) 

#         except Exception as e:
#             logger.error('===== 接收信号：创建积分日志后更新积分排行 时发生错误 =====')
#             logger.error(str(e))
