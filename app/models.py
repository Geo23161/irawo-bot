from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
import json
import io
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from cloudinary.models import CloudinaryField
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import sys
from PIL import Image as Pil
import requests
from io import BytesIO
import random

def f_3(nombre):
    return float(f"{nombre:.3f}")

IS_DEV = True

def g_v(key : str) -> str :
    return PerfectLovDetails.objects.get(key = key).value

def room_slug(user1, user2, is_group = False) :
    ordered = sorted([user1.pk, user2.pk])
    return ("" if not is_group else "g") + f"{ordered[0]}m{ordered[1]}"

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('superuser must have is_superuser set to True'))
        return self.create_user(email, password, **extra_fields)

class Image(models.Model) :
    name = models.CharField(max_length=150, null=True, blank=True)
    image = models.ImageField(upload_to='messages/images/')
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def get_details(self) :
        return [] if not self.details else json.loads(self.details)
    def set_details(self, dets) :
        self.details = json.dumps(dets)
        self.save()
    def get_image(self) :
        return self.image.url
    
    def get_preview(self):
        lis = self.get_image().split("/upload/")
        return "/upload/q_1/".join(lis) if len(lis) > 1 else ""
    
    def add_elt(self, elt ) :
        dets = self.get_details().append(elt)
        return dets

    def set_size(self) :
        res = requests.get(self.get_preview())
        img = Pil.open(BytesIO(res.content))
        width, height = img.size
        self.set_details(self.add_elt(width))
        self.set_details(self.add_elt(height))
    

class Audio(models.Model) :
    name = models.CharField(max_length=150, null=True, blank=True)
    audio = CloudinaryField(resource_type='', null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def get_details(self) :
        return [] if not self.details else json.loads(self.details)

    def get_audio(self) :
        return self.audio.url

class Video(models.Model) :
    name = models.CharField(max_length=150, null=True, blank=True)
    video = CloudinaryField(resource_type='video', null=True, blank=True)
    image = models.ImageField(upload_to='messages/images/')
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def get_preview(self) :
        lis = self.image.url.split("/upload/")
        return "/upload/q_auto:eco/".join(lis) if len(lis) > 1 else ""
    
    def get_image(self) :
        return self.image.url

    def get_details(self) :
        return [] if not self.details else json.loads(self.details)

    def get_video(self) :
        return self.video.url
    
    def add_elt(self, elt ) :
        dets = self.get_details().append(elt)
        return dets

    def set_size(self) :
        res = requests.get(self.get_preview())
        img = Pil.open(BytesIO(res.content))
        width, height = img.size
        self.set_details(self.add_elt(width))
        self.set_details(self.add_elt(height))

    def set_details(self, dets) :
        self.details = json.dumps(dets)
        self.save()


class User(AbstractBaseUser, PermissionsMixin) :
    nom = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True)
    image = models.ForeignKey(Image, related_name="users", on_delete=models.CASCADE, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    objects = CustomUserManager()
    last = models.DateTimeField(null=True, blank=True, default=timezone.now())
    telegram_id = models.IntegerField(default=0)
    whatsapp = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text_info = models.TextField(null = True, blank = True)
    username = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def get_profil(self) :
        return self.image.get_image()
    
    def get_status(self) :

        if not self.accounts.count() :
            return 'off'
        else :
            return 'on' if self.accounts.first().get_amount() > -50 else 'off'
            
    def is_seller(self) -> bool :
        return not(not self.telegram_id)
    
class AIChat(models.Model) :
    created_at = models.DateTimeField(auto_now_add=True)
    typ = models.CharField(max_length=150, default='message')
    sent = models.TextField(null=True, blank=True)
    received = models.TextField(null=True, blank=True)
    cost = models.FloatField(default=0)
    unique_id = models.IntegerField(null=True, blank=True)
    room = models.ForeignKey("RoomMatch", related_name="ai_chats", on_delete=models.CASCADE, null=True, blank=True)
    
    def get_history(self, add_role = True) :
        all_ai_chats = AIChat.objects.filter(room__pk = self.room.pk, typ = 'message').exclude(received = None).order_by('created_at')
        history = [
            {"role": "SYSTEM", "message": g_v('message:ai:context')},
            {"role" : "CHATBOT", "message" : g_v('message:product') }
        ] if add_role else []
        for chat in all_ai_chats :
            history.append({
                "role" : "CHATBOT", "message" : chat.sent
            })
            history.append({
                "role" : "USER", "message" : chat.received
            })
        
        return history
    

    

class Transaction(models.Model) :
    trans_id = models.CharField(max_length=150, null=True, blank=True)
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)  

""" class Client(models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    cost = models.IntegerField(default=10)
    name = models.TextField(null=True, blank=True)
    ai_chats = models.ManyToManyField(AIChat, related_name="clients", blank=True) """



class Account(models.Model) :
    user = models.ForeignKey(User, related_name="accounts", on_delete=models.CASCADE, null=True, blank=True)
    transactions = models.ManyToManyField(Transaction, related_name="accounts", blank=True)
    amount = models.IntegerField(default=0)
    ai_chats = models.ManyToManyField(AIChat, related_name="clients", blank=True)

    def get_amount(self) :
        total_add = self.amount
        total_cost = 0
        for camp in self.user.campaigns.all() : total_cost += (camp.amount / 10000)
        for trans in self.transactions.all() : total_add += trans.amount
        for room in self.user.rooms.all() : total_cost += room.total_costs()

        return f_3(total_add - (total_cost))
    
    def get_image(self) :
        return self.user.get_profil()

    def name(self) :
        return self.user.nom
    
    def num_camp(self) :
        return self.user.campaigns.all().count()



class Product(models.Model) :
    name = models.CharField(max_length=150, null=True, blank=True)
    images = models.ManyToManyField(Image, related_name="products", )
    videos = models.ManyToManyField(Video, related_name="videos", blank = True, null =True)
    description= models.TextField(null=True, blank=True)
    option = models.TextField(null=True, blank=True)
    typ = models.CharField(max_length = 150, null = True, blank = True)
    user = models.ForeignKey(User, related_name="products", on_delete=models.CASCADE, null=True, blank=True)
    created_at= models.DateTimeField(auto_now = True, null=True, blank=True)

    def get_pictures(self) :
        return [  img.get_image() for img in self.images.all() ]
    
    def get_option(self) :
        return json.loads(self.option)
    
    def get_images(self) :
        return ImageSerializer(self.images.all().order_by('-created_at'), many = True).data 
    
    def get_videos(self) :
        return VideoSerializer(self.videos.all(), many = True).data
    
    def get_image(self) :
        return self.get_images()[0]['get_image']

    def get_description(self) :
        return [] if not self.description else json.loads(self.description)
    
class Campaign(models.Model) :
    user = models.ForeignKey(User, related_name="campaigns", on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, related_name="campaigns", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text_gen = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    budget = models.IntegerField(default=0)
    goal = models.CharField(max_length=150, null = True, blank=True)
    link = models.URLField(null=True, blank=True)
    contacts = models.TextField(null=True, blank=True)
    amount = models.IntegerField(default=0)

    def name_of(self) :
        name = ""
        camps = self.user.campaigns.all()
        for i in range(camps.count()) :
            if camps[i].pk == self.pk : name = f"Campagne N°{i+1} de {self.product.name}"
        return name[:45] + '...'

    def get_link(self) :
        return g_v('funnel:link').format(id = self.pk)
    
    def get_goal(self) :
        return {
            'goal' : self.goal,
            'link' : self.link,
            'contacts' : json.loads(self.contacts) if self.contacts else []
        }
    
    def get_stats(self) :
        rooms = self.rooms.all().order_by('-created_at')
        sucess = rooms.filter(checked = True)
        ambi = rooms.filter(checked = False)

        return {
            'global' : rooms,
            'success' : sucess,
            'ambigu' : ambi
        }
    
    def get_mod(self, slug) :
        rooms = self.get_stats()[slug]
        moy = 0
        for room in rooms :
            moy += room.total_costs()
        return {
            'customers' : rooms.count(),
            'moy' : f_3(moy * float(g_v('convert:fcfa_to_dol')) / rooms.count()) if rooms.count() else 0 
        }
    
    def get_global(self) :
        return self.get_mod('global')
    
    def get_success(self) :
        return self.get_mod('success')
    
    def get_ambigu(self) :
        return self.get_mod('ambigu')

    def get_media(self) :
        return self.product.get_images()[0] if len(self.product.get_images()) else self.product.get_videos()[0]

    def get_visitors(self) :
        return self.rooms.all().count()
    
    def get_ready(self) :
        return self.rooms.all().filter(checked = True).count()
    
    def get_price(self) :
        price = 0
        for room in self.rooms.all() :
            price += room.total_costs()

        return f_3(price * float(g_v('convert:fcfa_to_dol')) / self.rooms.all().count()) if self.rooms.all().count() else 0
    

class RoomMatch(models.Model) :
    campaign = models.ForeignKey(Campaign, related_name="rooms", on_delete=models.CASCADE, null=True, blank=True)
    users = models.ManyToManyField(User, related_name="rooms", null=True, blank=True)
    slug = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_proposed = models.BooleanField(default=False)
    why = models.TextField(default='Bienvenue')
    anonymous_obj = models.TextField(null = True, blank = True)
    is_categorized = models.BooleanField(default=False)
    images = models.ManyToManyField(Image, related_name='appears_in_room', blank=True)
    title = models.TextField(null=True, blank=True)
    ai_response = models.BooleanField(default=True)
    checked = models.BooleanField(default=False)
    commenced = models.BooleanField(default=False)
    result = models.TextField(null=True, blank=True)
    resume = models.TextField(null = True, blank=True)

    def open_link(self) :
        return g_v('default:discussion:link').format(self.campaign.pk, self.slug)

    def get_messages(self) :
        return self.messages.all().count()
    
    def get_cost(self) :
        return int(self.total_costs() * float(g_v('convert:fcfa_to_dol')) * 1000) / 1000

    def name_of(self) :
        
        rooms = self.campaign.rooms.all().order_by('created_at')
        for i in range(rooms.count()) : 
            if rooms[i].pk == self.pk : return f"Prospect N°{i+1}"

    def get_result(self) :
        return json.loads(self.result) if self.result else None

    def get_goal(self) :
        return self.campaign.get_goal()

    def get_medias(self) :
        prod = self.campaign.product
        return prod.get_images() + prod.get_videos()

    def get_amount(self) :
        return int(int(g_v('default:price:starter')) / (1 if (self.messages.all().count() > 1) else (2 if self.commenced else 5)))

    def total_costs(self) :
        
        total = 0
        for ai in self.ai_chats.all() : total += (ai.cost/10000)
        return f_3(total + self.get_amount())

    def is_critical(self) :
        return self.ai_chats.count().exclude(received = None) > 15 

    def get_anonymous(self) :
        return json.loads(self.anonymous_obj) if self.anonymous_obj else None

    def __str__(self) -> str:
        try :
            us = [u for u in self.users.all()]
            return f"{us[0].prenom}+{us[1].prenom}"
        except :
            return f"Room{self.pk}"
        
    def get_images(self) :
        return [img.get_image() for img in self.images.all()]

class Message(models.Model) :
    room = models.ForeignKey(RoomMatch, related_name="messages", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    step = models.CharField(max_length=150, default='sent')
    text = models.TextField(null=True, blank=True)
    image = models.OneToOneField(Image, related_name='message', on_delete=models.CASCADE, null=True, blank=True)
    audio = models.OneToOneField(Audio, related_name="message", on_delete=models.CASCADE, null=True, blank=True)
    video = models.OneToOneField(Video, related_name="message", on_delete=models.CASCADE, null=True, blank=True)
    functional = models.TextField(null = True, blank = True)
    user = models.IntegerField(default=0)
    old_pk = models.BigIntegerField(default=0)
    reply = models.TextField(null = True, blank =True)

    def get_reply(self) :
        rep = json.loads(self.reply) if self.reply else None
        return rep      

    def get_room(self) :
        return self.room.pk 
    
class PerfectLovDetails(models.Model) :
    key = models.CharField(max_length=150, null=True, blank=True)
    value = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.key
    



##########################################################
##!                   Serializer                       !##
##########################################################

class SimpleUserSerializer(serializers.ModelSerializer) :

    class Meta :
        model = User
        fields = ('id', 'nom', 'get_profil', 'last', 'get_status', 'is_seller')


class ImageSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Image
        fields = ('id', 'name', 'get_image', 'get_preview', 'get_details')

class RoomSerializer(serializers.ModelSerializer) :
    users = SimpleUserSerializer(many = True)
    class Meta :
        model = RoomMatch
        fields = ('id', 'users', 'slug', 'created_at', 'is_proposed', 'get_images', 'title', 'get_goal', 'get_medias')

class AudioSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Audio
        fields = ('id', 'name', 'get_audio', 'get_details')
    
class VideoSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Video
        fields = ('id', 'name', 'get_video', 'get_details', 'get_preview', 'get_image')
    
class MessageSerializer(serializers.ModelSerializer) :
    image = ImageSerializer()
    audio = AudioSerializer()
    video = VideoSerializer()
    class Meta :
        model = Message
        fields = ('id', 'get_room', 'created_at', 'step', 'text', 'image', 'audio', 'video' ,'user', 'old_pk', 'get_reply', 'functional' )

class CompanySerializer(serializers.ModelSerializer) :

    class Meta : 
        model = User
        fields = ('id', 'nom', 'description', 'email')

class CampaignSerializer(serializers.ModelSerializer) :

    class Meta :
        model = Campaign
        fields = ('id', 'name', 'created_at', 'get_media', 'get_visitors', 'get_ready', 'get_price', 'name_of')


class SimpleProductSerializer(serializers.ModelSerializer) :

    class Meta :
        model = Product
        fields = ('id', 'name', 'get_image', 'get_description' )

class PostSerializer(serializers.ModelSerializer) :

    class Meta :
        model = Campaign
        fields = ('id', 'text_gen', 'get_link', 'get_global', 'get_success', 'get_ambigu', 'name_of')

class ProspectSerializer(serializers.ModelSerializer) :

    class Meta :
        model = RoomMatch
        fields = ('id', 'name_of', 'checked', 'commenced', 'slug', 'resume', 'created_at', 'get_messages', 'get_cost', 'open_link')

class SingleProspectSerializer(serializers.ModelSerializer) :

    class Meta :
        model = RoomMatch
        fields = ('id', 'name_of', 'get_result')

class AccountSerializer(serializers.ModelSerializer) :

    class Meta :
        model = Account
        fields = ('id', 'get_amount', 'name', 'get_image', 'num_camp')

class PaySerializer(serializers.ModelSerializer) :

    class Meta :
        model = Transaction
        fields = ('id', 'created_at', 'trans_id', 'amount')

##########################################################
##!                   Signals                          !##
##########################################################


@receiver(post_save, sender = Message)
def send_message(sender, instance : Message, **kwargs):
    channel_layer = get_channel_layer()
    if kwargs['created'] :

        async_to_sync(channel_layer.group_send)(instance.room.slug, {
                'type' : 'new_message',
                'result' : MessageSerializer(instance).data
        })

        if ( not User.objects.get(pk = instance.user).is_seller()) and instance.room.ai_response :
            pass
        
    else :
        async_to_sync(channel_layer.group_send)(instance.room.slug, {
                'type' : 'messsage_update',
                'result' : [instance.step, instance.pk, instance.get_reply()]
        })

##########################################################
##!                   Utility                          !##
##########################################################

def SELLER_QUEST(seller : User) :
    return [
        {
            "question" : "Nom, Informations, Localisation et contact du vendeur ou promoteur",
            "title" : "",
            "typ" : "text",
            "answers" : f"""
                Nom : {seller.nom} -
                {seller.description}
            """
        }
    ]

def FINAL_QUEST(quest : list[dict], prod : Product) -> list[dict] :
    return quest + SELLER_QUEST(prod.user) 
    
def LAST_QUEST(quest : list[dict], prod : Product, camp : Campaign) -> list[dict] :
    return quest + [json.loads(g_v(f'command:{camp.goal}'))]
