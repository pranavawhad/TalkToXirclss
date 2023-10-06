from datetime import timedelta
import datetime
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
# from mailchimp_transactional import TransactionalClient
import mailchimp_marketing as mailchimp
from urllib3 import request

from .serializers import *
import random
import sched
import nexmo
import smtplib
import threading
# import sendinblue
import time
from django.conf import settings
import requests
# from sendinblue import SendinBlueException
import sib_api_v3_sdk

from rest_framework.decorators import api_view
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import *
from django.http import JsonResponse
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


# Create your views here.
# @api_view(['POST'])
@api_view(['GET','POST'])
def default(request):
    return HttpResponse("Working")

@csrf_exempt
def send_email(request):
    if request.method =='POST':
        details = request.body
        mapping_details = json.loads(details)
        
        try:
            merchant_id = mapping_details['merchant']
            try:
                purchase_data=Purchase_Package.objects.get(user_id=merchant_id,active_status=True)
            except Purchase_Package.DoesNotExist:
                return JsonResponse("Please purchase a package first",status=400,safe=False)
        except KeyError:
            shop_name = mapping_details['shop']
            app_name = mapping_details['app']
            try:
                purchase_data=Purchase_Package.objects.get(shop=shop_name,app = app_name,active_status=True)
                merchant_id = purchase_data.user_id
            except Purchase_Package.DoesNotExist:
                
                return JsonResponse("The following shop has not purchased package",status=400,safe=False)
        
        if (purchase_data.remaining_email_count<=0):
            return JsonResponse("Could Not send email as shop has run out of package",status=400,safe=False)

        try:
            division_details = Division_settings.objects.get(purchase_id = purchase_data.purchase_id)
            
        except Division_settings.DoesNotExist:
            return JsonResponse("The merchant has not applied",status=400)
        
        if division_details.email_division_type=='Platform':
            
            email_division = division_details.email_division
            valid_keys = [key for key, value in email_division.items() if
            value > 0]
            print(valid_keys)
            email_subtype = random.choice(valid_keys)
            print("Selected email subtype:", email_subtype)
        elif division_details.email_division_type=='Type':
            email_subtype = next((item['subtype'] for item in division_details.email_division if item["type"] ==mapping_details['email_type']), None)
        else:
            return JsonResponse("Invalid Division Type",status=400,safe=False)
        if email_subtype is None:
            return JsonResponse("Division Not allotted",status=400,safe=False)
        print(email_subtype)
                        
        
        
        email_credentials = Credentials_Model.objects.get(user_id=merchant_id,type='email',subtype=email_subtype)
        if not email_credentials:
            return JsonResponse("Enter your credentials",status=400,safe=False)
        
        credentials_data = email_credentials.credentials
        
        try:
            template_id = Merchant_template.objects.get(user_id = merchant_id,event = mapping_details['event'])
        except Merchant_template.DoesNotExist:
            template_id = None
        if template_id:
            try:
                template_obj=Templates.objects.get(pk=uuid.UUID(str(template_id.template_id)))
                print(template_obj.template)
            except Templates.DoesNotExist:
                template_obj=None
        try:
                attachments_data=Attachments.objects.filter(template_id=template_id.template_id)
        except Attachments.DoesNotExist:
                attachments_data=None
                
        html_content = template_obj.template.read()
        email_content = MIMEMultipart()
        email_content.attach(MIMEText(html_content, 'html', 'utf-8'))
        email_content['Subject'] = Header('Good Morning', 'utf-8')
        email_content['From'] = Header('', 'utf-8')
        
        
        if email_subtype == 'SMTP':
            if attachments_data:
                for attachment_data in attachments_data:
                    file_path = attachments_data.attachment.path
                    if file_path.lower().endswith('.pdf'):
                        
                        with open(file_path, 'rb') as file:
                            file_content = file.read()
                        attachment = MIMEApplication(file_content)
                        attachment.add_header('Content-Disposition','attachment',filename=os.path.basename(file_path))
                        email_content.attach(attachment)
                        
            smtp_server = smtplib.SMTP(credentials_data['server_address'],credentials_data['port'])
            smtp_server.starttls()
            smtp_server.login(credentials_data['email'],credentials_data['password'])
                        
            try:
                
                smtp_server.sendmail('', mapping_details['recipient'],email_content.as_string())
                smtp_server.quit()
            except Exception as e:
                
                return JsonResponse(f"An error occurred while sending email to {mapping_details['recipient']}: {str(e)}",status=400,safe=False)                        
        
        elif email_subtype =='Mailchimp':
            recipient_data = [{'email':mapping_details['recipient'],'type':'bcc'}]
            # try:
                
            # mailchimp = TransactionalClient(api_key=credentials_data['api_key'])
            response = mailchimp.messages.send({
                                    "message": {
                                    'html': "<p>Hi My Name is welcome to my shop</p>",
                                    'text': 'Hello',
                                    'subject': 'Test Email',
                                    'from_email': credentials_data['email'],
                                    'to': recipient_data,
                                    },
                                    'async': False
                                    })
            print(response)
            print("Mail Sent")
            # except ApiClientError as error:
            #     print("An exception occurred: {}".format(error.text))
            #     return JsonResponse("Error: {}".format(error.text),safe=False)

        elif email_subtype=='Brevo':
            sendinblue_configuration=sib_api_v3_sdk.Configuration()
            sendinblue_configuration.api_key['api-key']=credentials_data['api_key']
            mail_instance=sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(sendinblue_configuration))
            subject = 'Good Morning'
            html = html_content.decode('utf-8')
            sender={'email':credentials_data['email']}
            to=[{'email':mapping_details['recipient']}]
            bcc=[{'email':mapping_details['recipient']}]
            
            mail_to_be_sent=sib_api_v3_sdk.SendSmtpEmail(to=to,bcc=bcc,html_content=html,sender=sender,subject=subject)
            # try:
            response=mail_instance.send_transac_email(mail_to_be_sent)
            print(response)
            # except SendinBlueException as e:
            #     print("An exception occurred: {}".format(e))
            #     return JsonResponse("Error: {}".format(e), safe=False)
            
        elif email_subtype=='Zapier':
            webhook_url=credentials_data['webhook_url']
            data={
            "body" : html_content.decode('utf-8'),
            "body_type":"html",
            "cc":"",
            "subject":"demo",
            "to":mapping_details['recipient']
            }
            
            response=requests.post(webhook_url,data=json.dumps(data),headers={'Content-Type':'application/json'})
            received_response=response.json()
            if received_response['status']!='success':
                return JsonResponse("An error occured while sendingMail",safe=False,status=400)
                print(response.json())  
            
            
        elif email_subtype=='Juvlon':
            juvlon_api_key=credentials_data['api_key']
            mail_url = credentials_data['mail_url']
            subscriber_url=credentials_data['subscriber_url']
            mailer_list_url=credentials_data['mailer_list_url']
            headers = {
            "accept": "application/json",
            "content-type":"application/json",
            }
            data = {"ApiKey":juvlon_api_key,
                    "requests":[{"subject":"Hello",
                    "from":"",
                    "body":html_content.decode('utf-8'),
                    "to":mapping_details['recipient']}]}
            data_json = json.dumps(data)
            response = requests.post(mail_url, data=data_json,headers=headers)
            print(response.json())
            
        purchase_data.remaining_email_count-=1
        purchase_data.save()
        if division_details.email_division_type=='Platform':
            division_details.email_division[email_subtype]-=1
            division_details.save()
        log={'user_id':uuid.UUID(str(merchant_id)),'recipient_details':{'recipient_email':mapping_details['recipient']},'type':'email','subtype':email_subtype,'event':mapping_details['event']}
        serialized_log_data=LogsSerializer(data=log)    
        if serialized_log_data.is_vaild():
            serialized_log_data.save()
            return JsonResponse("SUCCESS")
        else:
            errors = serialized_log_data.errors
            return JsonResponse(errors, status=400, safe=False)
    return JsonResponse("invalid request type",status=400,safe=False)   
    # return HttpResponse('SHOWING SMS')
    
    
    
@csrf_exempt
def send_sms(request):
    if request.method=='POST':
        details=request.body
        mapping_details=json.loads(details)
        print(mapping_details)
        try:
            merchant_id=mapping_details['merchant']
            try:
                purchase_data=Purchase_Package.objects.get(user_id=merchant_id,active_status=True)
            except Purchase_Package.DoesNotExist:
                return JsonResponse("Please Purchase a Package",status=400,safe=False)
        except KeyError:
            shop_name=mapping_details['shop']
            app_name=mapping_details['app']
            try:
                
                purchase_data=Purchase_Package.objects.get(shop=shop_name,app_name=app_name,active_status=True)
                merchant_id = purchase_data.user_id
            except Purchase_Package.DoesNotExist:
                return JsonResponse("The following shop has not purchased a package",status=400,safe=False)
                    
        if(purchase_data.remaining_sms_count<=0):
            return JsonResponse("Could Not send sms as shop has run out of package",status=400,safe=False)
            # try:
        division_details=Division_settings.objects.get(purchase_id=purchase_data.purchase_id)
            # except Division_settings.DoesNotExist:
                # return JsonResponse("The merchant has not applied the division settings till now",status=400,safe=False)           
        if division_details.sms_division_type=='Platform':
            sms_division = division_details.sms_division
            valid_keys = [key for key, value in sms_division.items() if value > 0]
            print(valid_keys)
            sms_subtype = random.choice(valid_keys)
            print("Selected sms subtype:", sms_subtype)
        
        elif division_details.sms_division_type=='Type':
            sms_subtype = next((item['subtype'] for item in
            division_details.sms_division if item["type"] == mapping_details['sms_type']),None)
        
        else:
            return JsonResponse("Invalid Division Type",status=400,safe=False)
        if sms_subtype is None:
            return JsonResponse("Division Not allotted",status=400,safe=False)
        print(sms_subtype)
            
            
        sms_credentials=Credentials_Model.objects.get(user_id=merchant_id,type='sms',subtype=sms_subtype)
        
        if not sms_credentials:
            
            return JsonResponse("Enter the Credentials",status=400,safe=False)
        if sms_subtype=='Nexmo':
            client = nexmo.Client(key=sms_credentials.credentials['api_key'],secret=sms_credentials.credentials['api_secret'])
            response = client.send_message({
            'from': str(sms_credentials.credentials['sender_number']),
            'to':str(mapping_details['recipient']) ,
            'text': 'Hello here'
            })
            print(response)
            if response['messages'][0]['status'] != '0':
                return JsonResponse('Message failed with error: %s' %response['messages'][0]['error-text'],safe=False,status=400)
            
        elif sms_subtype=='Twilio':
            print(mapping_details['recipient'])
            client = Client(sms_credentials.credentials['account_sid'],sms_credentials.credentials['auth_token'])
            try:
                message = client.messages.create(
                from_=str(sms_credentials.credentials['twilio_number']),
                to=str(mapping_details['recipient']),
                body='Hi')
                print(message.sid)
            except TwilioRestException as e:
                print(e)
                return JsonResponse(e,status=400)
                                
        purchase_data.remaining_sms_count-=1
        purchase_data.save()
        
        if division_details.sms_division_type=='Platform':
            
            division_details.sms_division[sms_subtype]-=1
            division_details.save()
            
            
            
        log={'user_id':uuid.UUID(str(merchant_id)),'recipient_details':{'recipient_number':mapping_details['recipient']},'type':'sms','subtype':sms_subtype,'event':'LOGIN'}
        serialized_log_data=LogsSerializer(data=log)
        if serialized_log_data.is_valid():
            
            serialized_log_data.save()
            return JsonResponse("Success", status=202, safe=False)
        else:
# Get the validation errors from the serialized data
            errors = serialized_log_data.errors
            return JsonResponse(errors, status=400, safe=False)
    return JsonResponse("Invalid request type",status=400,safe=False)
        
        
        
@csrf_exempt
def send_whatsapp(request):
    
    if request.method=='POST':
        details=request.body
        mapping_details=json.loads(details)
       
        try:
            merchant_id=mapping_details['merchant']
            try:
                purchase_data=Purchase_Package.objects.get(user_id=merchant_id,active_status=True)
            except Purchase_Package.DoesNotExist:
                return JsonResponse("Please Purchase a Package",status=400,safe=False)
        except KeyError:
            shop_name=mapping_details['shop']
            app_name=mapping_details['app']
            try:
                purchase_data=Purchase_Package.objects.get(shop=shop_name,app_name=app_name,active_status=True)
                merchant_id=purchase_data.user_id
            except Purchase_Package.DoesNotExist:
                return JsonResponse("The following shop has not purchased package",status=400,safe=False)
        
        if(purchase_data.remaining_whatsapp_messages_count<=0):
            return JsonResponse("Could Not send whatsapp message as shop has run out of package",status=400,safe=False)

        
        try:
            division_details=Division_settings.objects.get(purchase_id=purchase_data.purchase_id)
        except Division_settings.DoesNotExist:
            return JsonResponse("The merchant has not applied the division settings till now",status=400,safe=False)
        
        
        if division_details.whatsapp_division_type=='Platform':
            whatsapp_division = division_details.whatsapp_division
            valid_keys = [key for key, value in whatsapp_division.items() if value > 0]
            print(valid_keys)
            whatsapp_subtype = random.choice(valid_keys)
            print("Selected whatsapp subtype:", whatsapp_subtype)
        
        elif division_details.whatsapp_division_type=='Type':
            whatsapp_subtype = next((item['subtype'] for item in
            division_details.whatsapp_division if item["type"] ==
            mapping_details['whatsapp_message_type']), None)
            
        else:
            
            return JsonResponse("Invalid Division Type",status=400,safe=False)
        if whatsapp_subtype is None:
            return JsonResponse("Division Not allotted",status=400,safe=False)
        print(whatsapp_subtype)
        whatsapp_credentials=Credentials_Model.objects.get(user_id=merchant_id,type='whatsapp',subtype=whatsapp_subtype)
        
        if whatsapp_subtype=='Twilio':
            client=Client(whatsapp_credentials.credentials['account_sid'],whatsapp_credentials.credentials['auth_token'])
            
            try:
                message = client.messages.create(from_="whatsapp:"+str(whatsapp_credentials.credentials['twilio_whatsapp_number']),
                to="whatsapp:"+str(mapping_details['recipient']),
                body="Your {{1}} appointment is coming up on {{2}}. Getready!"
                )
                print(message.sid)
            except TwilioRestException as e:
                return JsonResponse(e,status=400)
            
            print("Message Sent")
        purchase_data.remaining_whatsapp_messages_count-=1
        purchase_data.save()
        if division_details.sms_division_type=='Platform':
            division_details.sms_division[whatsapp_subtype]-=1
            division_details.save()
        log={'user_id':uuid.UUID(str(merchant_id)),'recipient_details':{'recipient_number':mapping_details['recipient']},'type':'whatsapp','subtype':whatsapp_subtype,'event':'LOGIN'}
        serialized_log_data=LogsSerializer(data=log)
        if serialized_log_data.is_valid():
            serialized_log_data.save()
            return JsonResponse("Success", status=202, safe=False)
        else:
# Get the validation errors from the serialized data
            errors = serialized_log_data.errors
            return JsonResponse(errors, status=400, safe=False)
    return JsonResponse("Invalid Request Type",safe=False,status=400)
        

@csrf_exempt
def subscription(request):
    if request.method=='POST':
        data=request.POST
        print(data)
        serialized_data=SubscriberSerializer(data=data)
        if serialized_data.is_valid():
            serialized_data.save()
            req_data=serialized_data.data
            smtp_server_address = "smtp.gmail.com"
            smtp_port = 587
            smtp_username = ""
            smtp_password = ""
            smtp_server=smtplib.SMTP(smtp_server_address,smtp_port)
            smtp_server.starttls()
            smtp_server.login(smtp_username,smtp_password)
            link="https://9fab-103-197-226-50.ngrok-free.app/accounts/verify/"+str(req_data['subscriber_id'])
            print(link)
            print(req_data['email'])
            message_data=f"Please verify your name {link}"
            subject='Welcome to my shop'
            message = MIMEText(message_data, "plain", "utf-8")
            message["Subject"] = Header(subject, "utf-8")
            message["From"] = ""
            message["To"] = req_data['email']
            
            try:
                smtp_server.sendmail(smtp_username, req_data['email'],
                message.as_string())
                smtp_server.quit()
            except Exception as e:
                return JsonResponse(f"An error occurred while sending email to{req_data['email']}: {str(e)}",status=400,safe=False)
            return JsonResponse({'success':True},status=202)
        
        else:
            error=serialized_data.errors
            print(error)
            return JsonResponse({'success':False,'error':error},status=400)
    return JsonResponse("Invalid Request method only POST allowed",safe=False,status=400)


@csrf_exempt
def verify(request,id):
        if request.method=='GET':
            try:
                 user_obj=Subscriber.objects.get(pk=id)
            except Subscriber.DoesNotExist:
                
                return JsonResponse("User not Found",safe=False,status=404)
            user_obj.is_verified=True
            user_obj.save()
            return JsonResponse("You are verified",safe=False,status=202)
        return JsonResponse("Invalid Request Type",safe=False,status=400)
    

def response(query):
 
    url=f"{settings.SHOP_DOMAIN}/admin/api/{settings.SHOPIFY_API_VERSION}/graphql.json"
    first_query=f"""{{
        customerSegmentMembers(first:50 query:"{query}"){{
        edges{{
        node{{
        defaultEmailAddress{{
        emailAddresss
        }}
        }}
        }}
        pageInfo{{
        hasNextPage
        endCursor
        }}
        }}
        }}
        """
    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': settings.SHOPIFY_ADMIN_ACCESS_TOKEN,
        'X-Shopify-Api-Key':settings.SHOPIFY_API_KEY
        }
    first_response = requests.post(url, headers=headers,data=json.dumps({'query': first_query}))
    first_response=json.loads(first_response.text)
    final_email_list = [items['node']['defaultEmailAddress']['emailAddress']
    for items in first_response['data']['customerSegmentMembers']['edges']]
    
    
    has_next_page=first_response['data']['customerSegmentMembers']['pageInfo']
    ['hasNextPage']
    end_cursor=first_response['data']['customerSegmentMembers']['pageInfo']['endCursor']
    if has_next_page==True:
        while has_next_page!=False:
            query=f"""
        {{
        customerSegmentMembers(first:50 after:"{end_cursor}"
        query:"{query}"){{
        edges{{
        node{{
            defaultEmailAddress{{
emailAddress
        }}
        }}
        }}
        pageInfo{{
        hasNextPage
        endCursor
        }}
        }}
        }}
        """
    headers = {
'Content-Type': 'application/json',
'X-Shopify-Access-Token': settings.SHOPIFY_ADMIN_ACCESS_TOKEN,
'X-Shopify-Api-Key':settings.SHOPIFY_API_KEY
}
    
    response = requests.post(url, headers=headers,data=json.dumps({'query': query}))
    response=json.loads(response.text)
    email_list=[items['node']['defaultEmailAddress']['emailAddress']
for items in response['data']['customerSegmentMembers']['edges']]
    final_email_list.extend(email_list)
    print("has next page =>"+response['data']['customerSegmentMembers']['pageInfo']['hasNextPage'])
    print("next cursor => "+response['data']['customerSegmentMembers']['pageInfo']['endCursor'])
    end_cursor=response['data']['customerSegmentMembers']['pageInfo'][
    'endCursor']
    has_next_page=response['data']['customerSegmentMembers']['pageInfo']['hasNextPage']
    return final_email_list

            
# @api_view(['POST'])
def send_email_audience(request):
    
    if request.method =='POST':
        
        campaign_data = requests.request.POST.get('campaign_data')
    


        query_data=Segments.objects.get(pk=uuid.UUID(str(campaign_data['campaign_details']['send_to'])))
        audience=response(query_data.query)
        try:
            restricted_audience_segement=campaign_data['campaign_details']['dont_send_to']
        except KeyError:
            restricted_audience_segement=None
        if restricted_audience_segement is not None:
            restricted_query_data=Segments.objects.get(pk=uuid.UUID(str(restricted_audience_segement)))
            restricted_audience=response(restricted_query_data.query)
            final_audience=list(set(audience).difference(set(restricted_audience))
            )
        else:
            final_audience = audience   
        if final_audience:
            if campaign_data['domain']=='SMTP':
                print(campaign_data['template'])
                template=open("."+campaign_data['template'],'rb')
                html_content=template.read()
                email_content = MIMEMultipart()
                email_content.attach(MIMEText(html_content, 'html', 'utf-8'))
                email_content['Subject'] = Header(campaign_data['subject'], 'utf-8')
                email_content['From'] = Header('Bombay Club','utf-8')
                smtp_server=smtplib.SMTP('smtp.gmail.com',587)
                smtp_server.starttls()
                smtp_server.login('','')
                logs=[]
                for person in final_audience:
                    try:
                        smtp_server.sendmail('', person,email_content.as_string())
                        log={'user_id':campaign_data['user_id'],'recipient':person,'success':True}
                        logs.append(log)
                    except Exception as e:
                        log={'user_id':campaign_data['user_id'],'recipient':person,'success':False,'error':str(e)}
                        logs.append(log)
                smtp_server.quit()
                serialized_data=CampaignLogSerializer(data=logs,many=True)
                if serialized_data.is_valid():
                    validated_logs = serialized_data.data
                    print(validated_logs)
                    logs_instances=[]
                    for log_data in validated_logs:
                        user_id = log_data.pop('user_id')
                        user = User.objects.get(pk=user_id)
                        logs_instance = Campaign_Logs(user_id=user, **log_data)
                        logs_instances.append(logs_instance)
                    print(logs_instances)
                    
                    
                    Campaign_Logs.objects.bulk_create(logs_instances)
                else:
                    error=serialized_data.errors
                    campaign_data_final=Campaigns.objects.get(pk=campaign_data['campaign_id'])
                    campaign_data_final.campaign_details['completed']=True
                    campaign_data_final.save()
            else:
                error={'success':False,'error':'Domain Not set yet'}
                return JsonResponse(error,status=400)
            return JsonResponse({'success':True},status=200)
        else:
            return JsonResponse({'success':True,'note':'No emails were sent as there were no recipients left'},status=200)
    return HttpResponse('SUCCESS')
        

@api_view(['POST'])
# @permission_classes([AllowAny])
def add_campaign(request):
        if request.method == 'POST':
            serialized_data = CampaignsSerializer(data=request.data)
            if serialized_data.is_valid():
                serialized_data.save()
                data = serialized_data.data
                if data['campaign_type']=='Broadcast Campaign' or 'SegmentedCampaign':
                    def schedule_and_run(time_difference):
                        scheduler = sched.scheduler(time.time, time.sleep)
                        scheduler.enter(time_difference, 1, send_email_audience,(data,))
                        scheduler.run()
                    if data['campaign_details']['schedule'] == False:
                        time_difference=0
                        thread = threading.Thread(target=schedule_and_run,args=(time_difference,))
                        thread.start()
                    else:
                        
                        now = datetime.now()
                        schedule_time = now.replace(hour=int(data['campaign_details']['schedule_time'][:2]
                            ),minute=int(data['campaign_details']['schedule_time'][3 :5]),
                        second=0,
                        microsecond=0)
                        if now > schedule_time:
                            schedule_time += timedelta(days=1)
                            time_difference = (schedule_time - now).total_seconds()
                            thread = threading.Thread(target=schedule_and_run,args=(time_difference,))
                            thread.start()
                            
            else:
                errors = serialized_data.errors
                print(errors)
                return JsonResponse(errors, status=400)
            campaign_data = Campaigns.objects.get(pk=data['campaign_id'])
            # campaign_data_serialize = C('json', [campaign_data])
            # campaign_data_final=json.loads(campaign_data_serialize)
            return JsonResponse(campaign_data,safe=False,status=202)
        return JsonResponse("Invalid Request Type",safe=False,status=400)
    
    

                        