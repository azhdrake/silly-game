from django.contrib import admin

from .models import PromptCard, NounCard, Player, Session, Deck, AllCards

admin.site.register(PromptCard)
admin.site.register(NounCard)
admin.site.register(Player)
admin.site.register(Session)
admin.site.register(Deck)
admin.site.register(AllCards)

