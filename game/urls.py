from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('game/<int:session_pk>', views.game, name='game'),
    path('play/<int:session_pk>', views.play, name='play'),
    path('judging/<int:session_pk>', views.judge, name='judge'),
    path('post/ajax/create_card', views.create_card, name='create_card')
]