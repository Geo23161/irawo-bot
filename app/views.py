from django.shortcuts import render
from .models import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import datetime
import threading
import string
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .cohere import create_marketing, create_resume
from .core import Kkiapay

# Create your views here.

def send_by_thread(func):
    proc = threading.Thread(target=func)
    proc.start()

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    return random_string

@api_view(['GET'])
def initiate_all(request,  pk) :
    name = generate_random_string(length=10)
    email = f"{name}.{User.objects.all().order_by('-created_at').first().pk}@statusmax.site"
    password = f"{name}.{User.objects.all().order_by('-created_at').first().pk}@"
    user = User.objects.create(nom = name, email = email, image = Image.objects.get(name = 'default:image:user'))
    user.set_password(password)
    user.save()

    campaign = Campaign.objects.get(pk = pk)
    room = RoomMatch.objects.create(slug = room_slug(user, campaign.user), title = campaign.product.name, campaign = campaign)
    
    """ if typ == 'product' :
        seller = Product.objects.get(pk = pk).user
        title = Product.objects.get(pk = pk).name
    elif typ == 'seller' :
        seller = User.objects.get(pk = pk)
        title = seller.nom

    room = RoomMatch.objects.create(slug = room_slug(user, seller), title = title) """
    """ if typ == 'product' :
        prod = Product.objects.get(pk = pk)
        for img in prod.images.all() :
            room.images.add(img)
    elif typ == 'seller' :
        seller = User.objects.get(pk = pk)
        room.images.add(seller.image) """
    room.users.add(user)
    room.users.add(campaign.user)
    message = Message.objects.create(room = room, user = campaign.user.pk, text = g_v('message:product')  )
    refresh = RefreshToken.for_user(user)
    account = Account.objects.get_or_create(user = campaign.user)[0]
    return Response({
        'done' : True,
        'result' : room.slug,
        'tokens' : {
            'refresh' : str(refresh),
            'access' : str(refresh.access_token)
        },
        'other' : campaign.product.get_image()
    })

@api_view(['GET'])
def get_tokens(request, pk ) :
    camp = Campaign.objects.get(pk = pk)
    refresh = RefreshToken.for_user(camp.user)
    return Response({
        'done' : True,
        'result' : {
            'refresh' : str(refresh),
            'access' : str(refresh.access_token)
        },
        'other' : camp.product.get_image()
    })
    
@api_view(['GET', 'HEAD'])
@permission_classes([IsAuthenticated])
def ping(request):
    return Response({'done': True})

@api_view(['POST'])
def register_seller(request) :
    name = request.POST.get('name')
    email = request.POST.get('email')
    password = request.POST.get('password')
    commerce = request.POST.get('commerce')
    description = request.POST.get('description')
    logo = request.FILES.get('logo') 
    image = Image.objects.create(image = logo, name="user:logo")

    user = User.objects.create(nom = commerce, email = email, description = description, username = name, image = image)
    user.set_password(password)
    user.save()

    Account.objects.create(user = user)

    return Response({
        'done' : True
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_company(request) :
    return Response({
        'done' : True,
        'result' : CompanySerializer(request.user).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_posts(request) :
    posts = request.user.campaigns.all().order_by('-created_at')
    return Response({
        'done' : True,
        'result' : CampaignSerializer(posts[:14], many = True).data,
        'is_on' : request.user.get_status() == 'on',
        'has_next' : posts.count() > 14
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_update(request) :
    pks = json.loads(request.data.get('pks'))
    posts = Campaign.objects.all().filter(pk__in = pks).order_by('-created_at')
    return Response({
        'done' : True,
        'result' : CampaignSerializer(posts[:14], many = True).data,
        'is_on' : request.user.get_status() == 'on'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_post(request, pk) :
    campaign = Campaign.objects.get(pk = pk)
    campaign.delete()

    return Response({
        'done' : True,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products(request) :
    return Response({
        'done' : True,
        'result' : SimpleProductSerializer(request.user.products.all().order_by('-created_at'), many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prod(request) :
    prod= Product.objects.create(user = request.user, typ = request.POST.get('typ'), name = request.POST.get('name') )
    for i in range(int(request.POST.get('img_length'))) :
        img = Image.objects.create( name = prod.name + '_img' + str(i), image = request.FILES.get('img' + str(i)) )
        prod.images.add(img)
    if int(request.POST.get('vid_length')) :
        for i in range(int(request.POST.get('vid_length'))) :
            vid = Video.objects.create(name = prod.name + '_vid' + str(i), image = request.FILES.get('prev' + str(i)), video = request.FILES.get('vid' + str(i)) )
            prod.videos.add(vid)

    return Response({
        'done' : True,
        'result' : SimpleProductSerializer(prod).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quest_mod(request, pk) :
    prod = Product.objects.get(pk = pk)
    return Response({
        'done' : True,
        'result' : json.loads(g_v(f'model:quest:{prod.typ}'))
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_quest(request, pk) :
    ai_quests = json.loads(request.data.get('quests'))
    prod = Product.objects.get(pk = pk)
    prod.description = json.dumps(FINAL_QUEST(ai_quests, prod))
    prod.save()
    return Response({
        'done' : True,
        'result' : SimpleProductSerializer(prod).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_price_per(request) :
    return Response({
        'done' : True,
        'result' : json.loads(g_v('default:estimation')),
        'other' : Account.objects.get(user = request.user).get_amount()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_campaign(request) :
    prod = Product.objects.get(pk = int(request.POST.get('prod_id')))
    camp = Campaign.objects.create(product = prod, user = request.user, goal = request.POST.get('goal'), budget = int(request.POST.get('budget')), contacts = request.POST.get('contacts'), link = request.POST.get('link') )
    my_camps = request.user.campaigns.count()
    camp.name = f"Campagne N°{my_camps} de {prod.name}"
    t,c = create_marketing(prod, camp)
    camp.text_gen = t
    camp.amount = c
    camp.save()
    prod.description = json.dumps(LAST_QUEST(json.loads(prod.description), prod, camp))
    prod.save()
    return Response({
        'done' : True,
        'result' : camp.pk
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_campaign(request, pk) :
    return Response({
        'done' : True,
        'result' : PostSerializer(Campaign.objects.get(pk = pk)).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_checked(request, slug) :
    room = RoomMatch.objects.get(slug = slug)
    room.checked = True
    room.resume = 'Converti'
    room.save()
    if room.get_goal()['goal'] == 'event' :
        return Response({
            'done' : True
        })
    name = request.data.get('name')
    email = request.data.get('email')
    tel = request.data.get('tel')
    whatsapp = request.data.get('whatsapp')
    lieu = request.data.get('lieu')

    result = dict()
    if name : result['name'] = name
    if email : result['email'] = email
    if tel : result['tel'] = tel
    if whatsapp : result['whatsapp'] = whatsapp
    if lieu : result['lieu'] = lieu

    room.result = json.dumps(result)
    room.save()

    return Response({
        'done' : True
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_prospects(request, pk) :
    campaign = Campaign.objects.get(pk = pk)
    slug = request.data.get('slug')
    pks = json.loads(request.data.get('pks'))
    rooms = campaign.get_stats()[slug]
    rooms = rooms.exclude(pk__in = pks)[:30]
    for room in rooms: 
        if room.messages.count() <= 1 and (not room.resume) :
            room.resume = "Non Interessé"
            room.save()
    return Response({
        'done' : True,
        'result' : ProspectSerializer(rooms, many = True).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def set_resume(request, pk) :
    room = RoomMatch.objects.get(pk = pk)

    return Response({
        'done' : True,
        'result' : create_resume(room)
    })

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def get_prospect(request, pk) :
    return Response({
        'done' : True,
        'result' : SingleProspectSerializer(RoomMatch.objects.get(pk = pk)).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request) :
    return Response({
        'done' : True,
        'result' : AccountSerializer(Account.objects.get(user = request.user)).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_min_pay(request) :
    return Response({
        'done' : True,
        'result' : int(g_v('min:pay')),
        'key' : g_v('kkiapay0' + (':sand' if IS_DEV else '')),
        'is_dev' : IS_DEV
    })

def getKkiapay():
    return Kkiapay(g_v('kkiapay0'+ (":sand" if IS_DEV else "")), g_v('kkiapay1'+ (":sand" if IS_DEV else "")), g_v('kkiapay2'+ (":sand" if IS_DEV else "")), sandbox= IS_DEV)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_payment(request):
    transactionId = request.data.get('transactionId')
    
    kkia = getKkiapay()
    if kkia.verify_transaction(transaction_id=transactionId).status == "SUCCESS":
        trans = Transaction.objects.create(trans_id = transactionId, amount = int(request.data.get('amount')))
        account = Account.objects.get(user = request.user)
        account.transactions.add(trans)

        return Response({
            'done': True,
        })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pays(request) :
    return Response({
        'done' : True,
        'result' : PaySerializer(Account.objects.get(user = request.user).transactions.all().order_by('-created_at'), many = True).data
    })
