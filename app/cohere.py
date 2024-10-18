import cohere
from app.views import *
import os
import time
import threading

def send_by_thread(func):
    proc = threading.Thread(target=func)
    proc.start()

def create_resume(room : RoomMatch) -> str :
    if not room.get_messages() :
        room.resume = "Non intéressé"
        room.save()
        return room.resume
    aichat = AIChat.objects.create(typ = 'resume', sent = g_v('sent:ai:resume'), unique_id = (-8544 * room.pk), room = room  )
    api_key = os.environ.get('COHERE_KEY')
    co = cohere.Client(api_key)
    chat_history = [
        {'role' : "SYSTEM", "message" : g_v('resume:ai:context') }
    ] +  aichat.get_history(False)
    docs = room.campaign.product.get_description()
    formatted_docs = [
        { 'title' : doc['question'], 'text' : doc['answers'] } for doc in docs
    ]
    response = co.chat(
        model="command-r",
        chat_history= chat_history,
        message=aichat.sent,
        documents = formatted_docs
    )
    aichat.received = response.text
    aichat.save()
    cohere_price : list[int] = json.loads(g_v('cohere:price'))
    profit_coeff = float(g_v('profit:coeff'))
    aichat.cost = float(float((response.meta.billed_units.input_tokens * cohere_price[0] + response.meta.billed_units.output_tokens * cohere_price[1]) * 10000) ) 
    if response.meta.billed_units.classifications :  aichat.cost =+ float(response.meta.billed_units.classifications * cohere_price[2] * profit_coeff * 10000 )
                             
    aichat.save()
    room.resume = aichat.received
    room.save()

    return response.text

def create_marketing(prod : Product, camp : Campaign) -> str :
    aichat = AIChat.objects.create(typ = 'marketing', sent = g_v('sent:ai:marketing'), unique_id = (-8 * prod.pk)  )
    api_key = os.environ.get('COHERE_KEY')
    co = cohere.Client(api_key)
    chat_history = [
        {'role' : "SYSTEM", "message" : g_v('marketing:ai:context') }
    ]
    docs = prod.get_description()
    formatted_docs = [
        { 'title' : doc['question'], 'text' : doc['answers'] } for doc in docs
    ]
    response = co.chat(
        model="command-r",
        chat_history= chat_history,
        message=aichat.sent,
        documents = formatted_docs
    )
    aichat.received = response.text
    aichat.save()
    cohere_price : list[int] = json.loads(g_v('cohere:price'))
    profit_coeff = float(g_v('profit:coeff'))
    aichat.cost = float(float((response.meta.billed_units.input_tokens * cohere_price[0] + response.meta.billed_units.output_tokens * cohere_price[1]) * 10000) ) 
    if response.meta.billed_units.classifications :  aichat.cost =+ float(response.meta.billed_units.classifications * cohere_price[2] * profit_coeff * 10000 )
                             
    aichat.save()
    return aichat.received, aichat.cost



def send_to_ai(ai_chat : AIChat, room : RoomMatch ) :
    user = room.campaign.user
    api_key = os.environ.get('COHERE_KEY')
    co = cohere.Client(api_key)
    chat_history = ai_chat.get_history()
    docs = room.campaign.product.get_description()
    formatted_docs = [
        { 'title' : doc['question'], 'text' : doc['answers'] } for doc in docs
    ]
    response = co.chat(
        model="command-r",
        chat_history= chat_history,
        message=ai_chat.sent,
        documents = formatted_docs
    )
    ai_chat.received = response.text
    ai_chat.save()
    rep_message = Message.objects.get(old_pk = ai_chat.unique_id)
    message = Message.objects.create( room = ai_chat.room, text = ai_chat.received, user = user.pk, old_pk = random.randint( -100000000, -1), reply = json.dumps({
        'author' : rep_message.user,
        'typ' : 'text',
        'content' : ai_chat.sent
    }))
    cohere_price : list[int] = json.loads(g_v('cohere:price'))
    profit_coeff = float(g_v('profit:coeff'))
    ai_chat.cost = float(float((response.meta.billed_units.input_tokens * cohere_price[0] + response.meta.billed_units.output_tokens * cohere_price[1]) * 10000) ) 
    if response.meta.billed_units.classifications :  ai_chat.cost =+ float(response.meta.billed_units.classifications * cohere_price[2] * profit_coeff * 10000 )
                             
    ai_chat.save()


def response_to(mes : Message) :
    aichat = AIChat.objects.create(unique_id = mes.old_pk, sent = mes.text, room = mes.room )
    account = Account.objects.get(user = mes.room.users.exclude(pk = mes.user).first())
    account.ai_chats.add(aichat)
    account.save()
    def send_ai() :
        send_to_ai(ai_chat = aichat, room=mes.room)
    send_by_thread(send_ai)
    """while not AIChat.objects.get(unique_id = mes.old_pk).received :
        channel_layer = get_channel_layer()
        heure_utc = datetime.datetime.now().astimezone(datetime.timezone.utc)
        heure_utc_string = heure_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        async_to_sync(channel_layer.group_send)(mes.room.slug, {
            'type' : 'g_w',
            'result' : {
                'room' : mes.room.slug,
                'user' : mes.room.users.exclude(pk = mes.user).first().pk,
                'last' : heure_utc_string
            }
        })
        time.sleep(0.4)"""
