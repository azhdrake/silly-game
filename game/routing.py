from django.urls import re_path
from . import consumers

ws_urlpatterns = [
   re_path(r'ws/chat/(?P<session_pk>\w+)/$', consumers.ChatConsumer.as_asgi()),
   re_path(r'ws/judge/(?P<session_pk>\w+)/$', consumers.JudgeConsumer.as_asgi()),
]