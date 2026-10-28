# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Advanced(AbstractUser):
    id = models.UUIDField(
        auto_created=True, 
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    phone_number = models.CharField(blank=True, null=True, max_length=16)
    temporary_chat_tele_id = models.CharField(blank=True, null=True)
    chat_tele_id = models.CharField(blank=True, null=True)

    