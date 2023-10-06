from django.contrib import admin
from django.urls import path,include
from notifications import views
from .views import *
urlpatterns = [
        path('',views.default,name = "default"),
        path('email',views.send_email,name = "email"),
        path('sms',views.send_sms,name = "sms"),
        path('whatsapp',views.send_whatsapp,name = "whatsapp"),
        path('subs',views.subscription,name = "subs"),
        path('verify/<id>/',views.verify,name = "verify"),
        path('res',views.response,name = "res"),
        path('add',views.add_campaign,name = "add"),
        path('email_audience',views.send_email_audience,name = "email_aud"),
]


