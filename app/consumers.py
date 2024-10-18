from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import *
from .views import send_by_thread
import time
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import *
from .cohere import *

def get_delete(pk) :
    try :
        pks = PerfectLovDetails.objects.get(key = f"{pk}:delete")
        return json.loads(pks.value)
    except :
        return []

def the_other(room, user) :
    return room.users.all().exclude(pk = user.pk).first()

class LovConsumer(JsonWebsocketConsumer) :
    
    def connect(self) :
        if self.scope['user'].is_anonymous:
            self.close()
        
        def initiate_all() :
            all_rooms = self.scope['user'].rooms.all()
            rooms = all_rooms
            messages = Message.objects.filter(room__in = all_rooms)
            
            done = {
                'rooms' : RoomSerializer(rooms, many = True).data,
                'user' : SimpleUserSerializer(self.scope['user']).data,
                'messages' : MessageSerializer(messages, many = True).data,
            }
            for room in all_rooms :   
                async_to_sync(self.channel_layer.group_add)(room.slug, self.channel_name)
            async_to_sync(self.channel_layer.group_add)(f"{self.scope['user'].pk}m{self.scope['user'].pk}", self.channel_name)
            result = {
                'type' : 'initialisation',
                'result' : done,
            }
            self.accept()

            self.send_json(result)
            
        send_by_thread(initiate_all)

    def new_room(self, ev) :
        async_to_sync(self.channel_layer.group_add)(ev['result']['slug'], self.channel_name)
        return self.send_json(ev)

    def rmvu_from_r(self, ev) :
        return self.send_json(ev)
    
    def rmvu_from_g(self, ev) :
        return self.send_json(ev)
    
    def momo_pay(self, ev) :
        return self.send_json(ev)
    
    def new_message(self, ev) :
        return self.send_json(ev)
    
    def new_group(self, ev) :
        for r in ev['result']['rooms'] :
            async_to_sync(self.channel_layer.group_add)(r['slug'], self.channel_name)
        return self.send_json(ev)
    
    def anonym_on(self, ev) :
        return self.send_json(ev)
    
    def new_post(self, ev) :
        return self.send_json(ev)
    
    def offnonym(self, ev) :
        return self.send_json(ev)
    
    def message_update(self, ev) :
        return self.send_json(ev)
    
    def d_m(self, ev) :
        return self.send_json(ev)
    
    def messsage_update(self, ev) :
        return self.send_json(ev)
    
    def send_online(self, ev) :
        if ev['result']['id'] != self.scope['user'].pk :
            return self.send_json(ev)
    
    def new_photo(self, ev) :
        return self.send_json(ev)
        
    def update_gusers(self, ev) :
        return self.send_json(ev)
    
    def s_o(self, ev) :
        """if ev['result'][0] != self.scope['user'].pk :
            return self.send_json(ev)"""
        return self.send_json(ev)
    
    def launcher_send(self, ev) :
        if ev['result']['author'] != self.scope['user'].pk :
            return self.send_json(ev)
        
    def refuse_la(self, ev) :
        if ev['result']['author'] == self.scope['user'].pk :
            return self.send_json(ev)
        else :
            return self.send_json({
                'type' : 'refused',
                'result' : 0
            })
        
    def rm_room(self, ev) :
        async_to_sync(self.channel_layer.group_discard)(ev['result'], self.channel_name)

    def new_niveau(self, ev) :
        return self.send_json(ev)
    
    def new_notif(self, ev) :
        return self.send_json(ev)
    
    def s_m(self, ev) :
        if ev['result']['target'] == self.scope['user'].pk :
            return self.send_json(ev)
        
    def g_w(self, ev) :
        if ev['result']['user'] != self.scope['user'].pk :
            return self.send_json(ev)
    
    def receive_json(self, content, **kwargs):
        user = User.objects.get(pk = self.scope['user'].pk)
        if content['type'] == 'heartbeat' :
            user.last = timezone.now()
            user.save()
            
        elif content['type'] == 'r_m' :
            mess = Message.objects.get(pk = content['result'])
            if mess.step == 'sent' :
                mess.step = 'delivered'
                mess.save()
        
        elif content['type'] == 's_s' :
            mess = Message.objects.get(pk = content['result'])
            mess.step = 'seen'
            mess.save()
        elif content['type'] == 'keeping' :
            pks = content['result']
            room_pks = content['other']['room']
            grp_pks = content['other']['group']
            messages = Message.objects.filter(pk__in = pks)
            final= [ [m.step, m.pk] for m in messages ]
            rooms = user.rooms.all().exclude(pk__in = room_pks)
            groups = user.my_groups.all().exclude(pk__in = grp_pks)
            cont = {
                'type' : 'keeping',
                'result' : final,
                'other' : {
                    'room' : RoomSerializer(rooms, many = True).data,
                    'group' : []
                }
            }
            self.send_json(cont)
        elif content['type'] == 'c_m' :
            me = content['result']
            can_cont = True
            """ if state != 'on' :
                new_state = state_messag(me['get_room'], self.scope['user'])
                if new_state == 'on' : can_cont = True
                else :
                    self.send_json({
                            'type' : 's_m',
                            'result' : {
                                'state' : new_state,
                                'target' : user.pk,
                                'old_pk' : me['old_pk']
                            }
                    })
                    Message.objects.filter(old_pk = me['old_pk']).delete() """
            if can_cont :
                try :
                    room = RoomMatch.objects.filter(pk = me['get_room'])
                    if room.exists() :
                        room = room.first()
                        message = Message.objects.create( room = room, text = me['text'], user = me['user'], old_pk = me['old_pk'] )
                        if 'get_reply' in me.keys() :
                            message.reply = me['get_reply']
                            message.save()
                        if room.ai_response :

                            response_to(message)
                        #handle_mess_perm(me['get_room'], self.scope['user'], me['old_pk'])
                    else :
                        self.send_json({
                                'type' : 's_m',
                                'result' : {
                                    'state' : 'deleted',
                                    'target' : user.pk,
                                    'old_pk' : me['old_pk']
                                }
                        })
                except Exception as e :
                    print("Erreur creation message => ",e)
        
        elif content['type'] == 'register_me' :
            async_to_sync(self.channel_layer.group_add)( content['result'], self.channel_name)
        elif content['type'] == 'initiate_chat' :
            result = content['result']
            target = User.objects.get(pk = result['target'])
            if result['author'] == user.pk :
                if not RoomMatch.objects.filter(slug = room_slug(user, target)).exists() :
                    room_match = RoomMatch.objects.get_or_create(slug = room_slug(user, target))[0]
                    room_match.save()
                    room_match.users.add(user)
                    room_match.users.add(target)
                    for use in room_match.users.all() :
                        async_to_sync(self.channel_layer.group_send)(f"{use.pk}m{use.pk}", {
                            'type' : 'new_room',
                            'result' : RoomSerializer(room_match).data
                        })
        elif content['type'] == "rmv_me" :
            async_to_sync(self.channel_layer.group_discard)(content['result'] ,self.channel_name)

        elif content['type'] == 's_w' :
            res = content['result']
            async_to_sync(self.channel_layer.group_send)(res['room'] , {
                'type' : 'g_w',
                'result' : res
            })
        elif content['type'] == 's_co' :
            res = content['result']
            room = RoomMatch.objects.get(slug = res)
            if not room.commenced :
                room.commenced = True
                room.save()
            
    def disconnect(self, code):
        if self.scope['user'].is_anonymous:
            return self.close()
        def remove_all_room() :
            all_rooms = self.scope['user'].rooms.all()
            for room in all_rooms :
                async_to_sync(self.channel_layer.group_discard)(room.slug, self.channel_name)
            async_to_sync(self.channel_layer.group_discard)(f"{self.scope['user'].pk}m{self.scope['user'].pk}", self.channel_name)
        send_by_thread(remove_all_room)
        self.close()
