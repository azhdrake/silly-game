from django.db import models
from django.db.models.aggregates import Count
from random import randint

class Session(models.Model):
    name = models.CharField(max_length = 50)
    def __str__(self):
        return self.name

class Deck(models.Model):
    name = models.CharField(max_length = 50)
    def __str__(self):
        return self.name

class Player(models.Model):
    nickname = models.CharField(max_length = 50)
    is_deck = models.BooleanField(default = False)
    is_judge = models.BooleanField(default = False)
    has_played = models.BooleanField(default = False)
    hand_size = models.IntegerField(default = 7)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    def __str__(self):
        return self.nickname

class PromptCard(models.Model):
    card_text = models.CharField(max_length = 1000)
    num_blanks = models.IntegerField(default = 1)
    is_active = models.BooleanField(default = False)
    won_by = models.ForeignKey(Player, on_delete=models.CASCADE, blank = True, null = True)
    def __str__(self):
        return self.card_text

class NounCard(models.Model):
    card_text = models.CharField(max_length = 1000)
    in_hand = models.ForeignKey(Player, on_delete=models.CASCADE, blank = True, null = True)
    with_prompt = models.ForeignKey(PromptCard, on_delete=models.CASCADE, blank = True, null = True)
    def __str__(self):
        return self.card_text

class AllCards(models.Model):
    card_text = models.CharField(max_length = 1000)
    is_noun = models.BooleanField(default = True)
    num_blanks = models.IntegerField(default = 0, blank = True, null = True)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, default = 1)
    def __str__(self):
        return self.card_text


