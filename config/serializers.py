from rest_framework import serializers
from .models import Config
import json


class ConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = Config
        fields = '__all__'
        