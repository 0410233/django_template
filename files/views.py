from django.shortcuts import render
from .models import Image
from .serializers import ImageSerializer
from rest_framework import generics
from rest_framework import mixins
from rest_framework.response import Response
from django.forms.models import model_to_dict
from rest_framework import permissions
from rest_framework.schemas import ManualSchema
from rest_framework.compat import coreapi, coreschema
from rest_framework.exceptions import ParseError
from PIL import Image as image
from django.conf import settings
import os
from datetime import datetime
import time

from PIL import Image as image
from PIL import Image as Image1


from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import cv2
from moviepy.editor import VideoFileClip

from .forms import ImageForm
from django.views import View
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status

from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser



# Create your views here.

def returnJson(code, result = None, msg = None):
    res = {}
    res['code'] = code
    res['result'] = result
    res['msg'] = msg

    response = HttpResponse(content_type="application/json")
    response.write(json.dumps(res))

    return response


class ImagesList(mixins.CreateModelMixin,
                  generics.GenericAPIView):

    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes =  (MultiPartParser, )

    file_param = openapi.Parameter('image_src', openapi.IN_FORM, description="文件", type=openapi.TYPE_FILE)
    size_param = openapi.Parameter('size', openapi.IN_FORM, description="缩略图尺寸如 200*200(长*宽)", type=openapi.TYPE_STRING)

    @swagger_auto_schema(
        operation_summary='上传文件',
        operation_description='图片视频的缩略图地址：{file_url}.min.jpg',
        manual_parameters= [size_param, ],

        responses={
            status.HTTP_400_BAD_REQUEST: '业务异常，具体message提示。', status.HTTP_401_UNAUTHORIZED: '系身份验证失败（token过期或非法账号）',
            status.HTTP_403_FORBIDDEN: '没权限', status.HTTP_404_NOT_FOUND: '请求路径不存在', status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: '客户发送的请求大小超过了2MB限制。',
            status.HTTP_500_INTERNAL_SERVER_ERROR: '系统内部异常', status.HTTP_502_BAD_GATEWAY: '网关异常'
        },

    )
    def post(self, request, *args, **kwargs):

        size = request.POST['size'].split('*')
        width = int(size[0])
        height = int(size[1])


        res = self.create(request, *args, **kwargs)

        file = res.data['image_src'].split(settings.MEDIA_URL)[-1]

        file_name = settings.MEDIA_ROOT + file
        file_name_new = settings.MEDIA_ROOT + file.split('.')[0]

        ext = file.split('.')[-1]

        if ext.lower() in ['jpg', 'jpeg', 'png', 'bmp']:
            ext = 'jpg'

        file_new = file.split('.')[0] + '.' + ext
        res.data['image_src_ori'] = file_new
        res.data['image_src'] = res.data['image_src'].split(settings.MEDIA_URL)[0] + settings.MEDIA_URL + file_new

        if ext.lower() in ['jpg', 'jpeg', 'png', 'bmp']:
            im1 = image.open(file_name)
            if len(im1.split()) == 4:
                r, g, b, a = im1.split()  # 利用split和merge将通道从四个转换为三个
                im1 = Image1.merge("RGB", (r, g, b))


            im1.save(file_name_new + '.jpg')

            im = image.open(file_name)
            rgb_im = im.convert('RGB')
            # 图片的宽度和高度
            img_size = rgb_im.size
            rgb_im.thumbnail((width, height))
            rgb_im.save(file_name_new + '.jpg.min.jpg')



        return res


class ImagesListPC(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # @method_decorator(login_required)
    def post(self, request):

        size = request.POST['size'].split('*')
        width = int(size[0])
        height = int(size[1])

        form = ImageForm(data=request.POST, files=request.FILES)

        res = {}

        if form.is_valid():
            image1 = form.save()

            prefix = ''
            if request:
                prefix = request.scheme + '://' + request.get_host() + settings.MEDIA_URL

            file = image1.image_src.name

            file_name = settings.MEDIA_ROOT + file
            file_name_new = settings.MEDIA_ROOT + file.split('.')[0]

            ext = file.split('.')[-1]



            if ext.lower() in ['jpg', 'jpeg', 'png', 'bmp']:
                ext = 'jpg'
                file_type = 0
            else:
                file_type = 1

            file_new = file.split('.')[0] + '.' + ext
            res['image_src_ori'] = file_new
            res['image_src'] = prefix + file_new

            if ext.lower() in ['jpg', 'jpeg', 'png', 'bmp']:
                im1 = image.open(file_name)
                if len(im1.split()) == 4:
                    r, g, b, a = im1.split()  # 利用split和merge将通道从四个转换为三个
                    im1 = Image1.merge("RGB", (r, g, b))

                im1.save(file_name_new + '.jpg')



                im = image.open(file_name)
                rgb_im = im.convert('RGB')
                # 图片的宽度和高度
                img_size = rgb_im.size
                rgb_im.thumbnail((width, height))
                rgb_im.save(file_name_new + '.jpg.min.jpg')


            if ext.lower() in ['avi', 'mp4']:



                clip = VideoFileClip(file_name)
                if int(clip.duration) > 60:
                    raise ParseError('视频不能大于60秒')

                # 使用opencv按一定间隔截取视频帧，并保存为图片
                vc = cv2.VideoCapture(settings.MEDIA_ROOT + file_new)  # 读取视频文件

                if vc.isOpened():  # 判断是否正常打开

                    rval, frame = vc.read()
                else:
                    rval = False

                if rval:  # 循环读取视频帧
                    rval, frame = vc.read()

                    cv2.imwrite(settings.MEDIA_ROOT + file_new + '.min.jpg', frame)  # 存储为图像

                    cv2.waitKey(1)


                vc.release()


            res['file_type'] = file_type

        return returnJson(10000, result=res)