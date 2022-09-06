from rest_framework import serializers
from .models import Image

class ImageSerializer(serializers.HyperlinkedModelSerializer):

    def validate_image_src(self, image):
        file_size = image.size
        limit_kb = 1024 * 20
        if file_size > limit_kb * 1024:
            raise serializers.ValidationError("文件大小不能超过 %s KB" % limit_kb)

        return image

    image_src = serializers.FileField(required=True)

    class Meta:
        model = Image
        fields = ('image_src', 'size',)


