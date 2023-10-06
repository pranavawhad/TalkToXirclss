import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager

# Create your models here.
# class CustomUserManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError('The Email field must be set')
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(email, password, **extra_fields)
class User(AbstractBaseUser):
    user_id = models.UUIDField(default=uuid.uuid4,auto_created=True,primary_key=True)
    name = models.CharField(max_length=50,null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=50,null=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    
    def __str__(self):
        return str(self.user_id)
    
    
    
    
class Packages(models.Model):
    package_id=models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    email_count=models.BigIntegerField(default=0)
    sms_count=models.BigIntegerField(default=0)
    whatsapp_messages_count=models.BigIntegerField(default=0)
    price=models.BigIntegerField()
    creation_timestamp=models.DateTimeField(auto_now_add=True)
    active_status=models.BooleanField(default=True)
    
    
    def __str__(self):
        return str(self.package_id)


class Templates(models.Model):
    template_id=models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    template =models.FileField(upload_to='media/')
    event=models.CharField(max_length=20)
    created_at=models.DateTimeField(auto_now=True)
    enabled_by_xircls=models.BooleanField()
    
    def __str__(self):
        return str(self.template_id)
    
    
class Attachments(models.Model):
    attachment_id =models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    attachment =models.FileField(upload_to='media/')
    template_id =models.ForeignKey(Templates,on_delete=models.CASCADE)
    
    
    def __str__(self):
        return str(self.attachment_id)
    


    
type_choice=(
    ('general','general'),
    ('email','email'),
    ('sms','sms'),
    ('whatsapp','whatsapp')
    )
subtype_choice=(
    ('Mailchimp','Mailchimp'),
    ('SMTP','SMTP'),
    ('Nexmo','Nexmo'),
    ('Twilio','Twilio'),
    ('Brevo','Brevo'),
    ('Zapier','Zapier'),
    ('Klaviyo','Klaviyo'),
    ('Juvlon','Juvlon')
    )
class Credentials_Model(models.Model):
    cred_id =models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    credentials =models.JSONField()
   
    type =models.CharField(max_length=20,choices=type_choice)
    subtype =models.CharField(max_length=20,choices=subtype_choice)
    shop =models.CharField(max_length=100)
    app_name =models.CharField(max_length=100,default='superleadz')
   
    user_id =models.ForeignKey(User,on_delete=models.CASCADE)
    
    
    def __str__(self):
        return str(self.cred_id)
    

division_choices=(
('Platform','Platform'),
('Type','Type')
)
class Purchase_Package(models.Model):
    purchase_id =models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    package_id =models.ForeignKey(Packages,on_delete=models.CASCADE)
    shop =models.CharField(max_length=100,default="bombayclub.myshopify.com")
    app_name =models.CharField(max_length=100,default='superleadz')
    user_id =models.ForeignKey(User,on_delete=models.CASCADE)
    remaining_email_count =models.BigIntegerField()
    remaining_sms_count =models.BigIntegerField()
    remaining_whatsapp_messages_count =models.BigIntegerField()
    active_status =models.BooleanField(default=True)
    
    def __str__(self):
        return str(self.purchase_id)
    

class Division_settings(models.Model):
    division_id =models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    purchase_id =models.ForeignKey(Purchase_Package,on_delete=models.CASCADE)
    email_division_type =models.CharField(max_length=20,choices=division_choices)
    email_division =models.JSONField()
    sms_division_type =models.CharField(max_length=20,choices=division_choices)
    sms_division =models.JSONField()
    whatsapp_division_type =models.CharField(max_length=20,choices=division_choices,default='Platform')
    whatsapp_division =models.JSONField(default={'Twilio':10000})
    def __str__(self):
        return str(self.division_id)
    
class Logs(models.Model):
    log_id =models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    
    user_id =models.ForeignKey(User,on_delete=models.CASCADE)
    recipient_details =models.JSONField()
    type =models.CharField(max_length=20)
    subtype =models.CharField(max_length=20)
    
    timestamp =models.DateTimeField(auto_now_add=True)
    event =models.CharField(max_length=100)
    
    
    def __str__(self):
        return str(self.log_id)
    

class Subscriber(models.Model):
    subscriber_id=models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    username=models.CharField(max_length=100)
    email=models.EmailField()
    is_verified=models.BooleanField(default=False)
    creation_timestamp=models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.email
    
class Segments(models.Model):
        segment_id=models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
        query=models.CharField(max_length=10000)
        segment_name=models.CharField(max_length=100)
        shop=models.CharField(max_length=100)
        app=models.CharField(max_length=100)
        added_by=models.ForeignKey(User,on_delete=models.CASCADE)
        timestamp=models.DateTimeField(auto_now_add=True)
        def __str__(self):
            return str(self.segment_id)

campaign_choices=(
('Broadcast Campaign','Broadcast Campaign'),
('Triggered Campaign','Triggered Campaign'),
('Segmented Campaign','Segmented Campaign')
)
class Campaigns(models.Model):
    campaign_id=models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    user_id=models.ForeignKey(User,on_delete=models.CASCADE)
    shop=models.CharField(max_length=100)
    app=models.CharField(max_length=100,default='superleadz')
    campaign_type=models.CharField(max_length=100,choices=campaign_choices)
    campaign_name=models.CharField(max_length=100)
    smart_send=models.BooleanField()
    domain=models.CharField(max_length=100,choices=subtype_choice)
    campaign_details=models.JSONField()
    subject=models.CharField(max_length=1000,blank=True,null=True)
    preview_text=models.CharField(max_length=1000,blank=True,null=True)
    template=models.FileField(upload_to='media/')
    reply_to_address=models.BooleanField()
    event=models.CharField(max_length=100,default='discount')

    def __str__(self):
        return str(self.campaign_id)
    
class Campaign_Logs(models.Model):
        log_id=models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
        user_id=models.ForeignKey(User,on_delete=models.CASCADE)
        recipient=models.EmailField()
        timestamp=models.DateTimeField(auto_now_add=True)
        success=models.BooleanField()
        error=models.CharField(max_length=1000,blank=True,null=True)
        def __str__(self):
            return str(self.log_id)
        
class Merchant_template(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4,primary_key=True,auto_created=True)
    user_id = models.ForeignKey(User,on_delete=models.CASCADE)
    template_id = models.ForeignKey(Templates,on_delete=models.CASCADE)
    event = models.CharField(max_length=100)
    
    def __str__(self):
        return str(self.unique_id)
    
    