from rest_framework import serializers
from .models import *


class SubscriberSerializer(serializers.ModelSerializer):
       class Meta:
           
            model = Subscriber
            fields = '__all__'
    

class LogsSerializer(serializers.ModelSerializer):
       class Meta:
           
            model = Logs
            fields = '__all__'

class CampaignLogSerializer(serializers.ModelSerializer):
       class Meta:
           
            model = Campaign_Logs
            fields = '__all__'
    
    
class CampaignsSerializer(serializers.ModelSerializer):
       class Meta:
           
            model = Campaigns
            fields = '__all__'