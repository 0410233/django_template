from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "初始化配置"

    # 初始化配置
    def handle(self, *args, **options):
        from config.models import Config
        
        self.stdout.write("正在初始化配置 ...")

        # 添加配置项
        configs = [{
            'key': 'platform_cut_ratio',
            'value': '0.01',
            'name': '平台提成比例',
        }]

        display = len(configs)
        for item in configs:
            record = Config.objects.filter(key=item['key']).first()
            if record is None:
                record = Config(**item)
            record.name = item['name']
            record.display = display
            if item.get('scope') is not None:
                record.scope = item['scope']
            if item.get('group') is not None:
                record.group = item['group']
            record.save()
            display -= 1

        # 删除配置信息
        keys = [item['key'] for item in configs]
        Config.objects.exclude(key__in=keys).delete()

        self.stdout.write("初始化配置完成。")
