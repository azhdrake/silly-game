from django import forms
from .models import NounCard, PromptCard, AllCards, Session, Player

class NewNounCardForm(forms.ModelForm):
    class Meta:
        model = NounCard
        fields = ('card_text',)

class NewPromptCardForm(forms.ModelForm):
    class Meta:
        model = PromptCard
        fields = ('card_text',)

class NewCardForm(forms.ModelForm):
    class Meta:
        model = AllCards
        fields = ('card_text', 'is_noun', 'deck', 'num_blanks')

class NewSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ('name',)

class NewPlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ('nickname',)

class PlayCardForm(forms.Form):
    noun_card = forms.IntegerField(required=True)
    prompt_card = forms.IntegerField()
    player = forms.IntegerField()
    class Meta:
        fields = ('noun_card', 'prompt_card', 'player')
    
