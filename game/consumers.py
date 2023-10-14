from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_pk']
        self.chat_room_name = 'chat_%s' % self.session_id

        async_to_sync(self.channel_layer.group_add)(
            self.chat_room_name,
            self.channel_name
        )

        self.accept()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chat_room_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_json = json.loads(text_data)
        message = text_json["message"]

        async_to_sync(self.channel_layer.group_send)(
            self.chat_room_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def chat_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'message':message
        }))

class JudgeConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_pk']
        self.judge_room_name = 'judge_%s' % self.session_id

        async_to_sync(self.channel_layer.group_add)(
            self.judge_room_name,
            self.channel_name
        )

        self.accept()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.judge_room_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_json = json.loads(text_data)
        message = text_json["message"]

        async_to_sync(self.channel_layer.group_send)(
            self.judge_room_name,
            {
                'type': 'judge_message',
                'message': message
            }
        )

    def judge_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'message':message
        }))

class SessionSelectSocket(WebsocketConsumer):
    def connect(self):
        self.session_room_name = 'session'

        async_to_sync(self.channel_layer.group_add)(
            self.session_room_name,
            self.channel_name
        )
        self.accept()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(  
            self.session_room_name,
            self.channel_name         
        )

    def receive(self, text_data):
        text_json = json.loads(text_data)
        message = text_json["message"]

        async_to_sync(self.channel_layer.group_send)(
            self.session_room_name,
            {
                'type': 'new_session_message',
                'message': message
            }
        )

    def new_session_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'message':message
        }))

class PlayerJoinSocket(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_pk']
        self.join_room_name = 'join_%s' % self.session_id

        async_to_sync(self.channel_layer.group_add)(
            self.join_room_name,
            self.channel_name
        )

        self.accept()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.join_room_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_json = json.loads(text_data)
        message = text_json["message"]

        async_to_sync(self.channel_layer.group_send)(
            self.join_room_name,
            {
                'type': 'join_message',
                'message': message
            }
        )

    def join_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'message':message
        }))