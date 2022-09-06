from rest_framework import serializers


class CarouselSerializer(serializers.Serializer):

    id = serializers.IntegerField(label='目标id')
    type = serializers.IntegerField(label='类型', help_text="0:H5页面,1:专家,2:问题")
    title = serializers.IntegerField(label='标题')
    image = serializers.IntegerField(label='图片地址')
    time = serializers.IntegerField(label='时间')


class SearchSerializer(serializers.Serializer):
    """搜索"""

    keywords = serializers.CharField(required=True, help_text='关键词')
    type = serializers.IntegerField(required=False, help_text='类型 - 0:专家,1:问答,2:视频')


class SearchResponseSerializer(serializers.Serializer):
    """搜索结果"""
    from user.serializers import ExpertSerializer
    from topic.serializers import TopicSerializer
    from knowledge.serializers import KnowledgeSerializer
    
    expert = ExpertSerializer(many=True, help_text='专家')
    topic = TopicSerializer(many=True, help_text='问答',)
    knowledge = KnowledgeSerializer(many=True, help_text='视频')
