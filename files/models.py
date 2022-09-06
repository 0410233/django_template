from django.db import models
from user.models import get_file_path

# Create your models here.

class Image(models.Model):
    image_src = models.FileField(upload_to=get_file_path, max_length=500)
    size = models.CharField('缩略图尺寸如 200*200(长*宽)', null=True, blank=True, max_length=50)



    def __str__(self):
        return str(self.image_src)

    class Meta:
        verbose_name_plural = "图片"

