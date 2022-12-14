from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "初始化配置"

    # 初始化配置
    def handle(self, *args, **options):
        from background.models import UserSetting
        
        self.stdout.write("正在初始化配置 ...")

        # 添加配置项
        usersetting_list = [{
            'key': 'platform_cut_ratio',
            'value': '0.01',
            'name': '平台提成比例',
        }]

        display = len(usersetting_list)
        for item in usersetting_list:
            record = UserSetting.objects.filter(key=item['key']).first()
            if record is None:
                record = UserSetting(**item)
            record.name = item['name']
            record.display = display
            if item.get('scope') is not None:
                record.scope = item['scope']
            if item.get('group') is not None:
                record.group = item['group']
            record.save()
            display -= 1

        # 删除配置信息
        keys = [item['key'] for item in usersetting_list]
        UserSetting.objects.exclude(key__in=keys).delete()

        self.stdout.write("初始化配置完成。")
