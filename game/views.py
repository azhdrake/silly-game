from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from .models import Player, PromptCard, NounCard, Session, Deck, AllCards
from .forms import NewNounCardForm, NewPromptCardForm, NewSessionForm, NewPlayerForm, NewCardForm, PlayCardForm
from random import randint
import urllib.parse

def index(request):
    if request.method == 'POST':
        if "start" in request.POST:
            # start new session. 
            form = NewSessionForm(request.POST)
            if form.is_valid():
                new_session = form.save()
                
                #make and populate the deck
                session_decks = dict(request.POST)["decks"]
                deck_pks = []
                for select_deck in session_decks:
                    deck_pks.append(select_deck)
                
                deck = Player(nickname="Deck", is_deck=True, hand_size=99999, session=new_session)
                deck.save()

                all_cards = []
                for deck_pk in deck_pks:
                    all_cards.append(AllCards.objects.filter(deck=deck_pk))

                for card_set in all_cards:
                    for card in card_set:
                        if card.is_noun:
                            new_card = NounCard(card_text=card.card_text, in_hand = deck)
                            new_card.save()
                        else:
                            new_card = PromptCard(card_text=card.card_text, num_blanks=card.num_blanks, won_by=deck)
                            new_card.save()
            else: 
                print("session form invalid")

    # get decks and sessions, render page
    deck_list = Deck.objects.order_by("pk")
    session_list = Session.objects.order_by("name")
    return render(request, 'game/index.html', {"session_list":session_list, "decks":deck_list})

def game(request, session_pk):
    player_list = Player.objects.filter(session=session_pk)
    new_player_form = NewPlayerForm
    if request.method == 'POST':
        if "join" in request.POST:
            # make a new player
            form = NewPlayerForm(request.POST)
            if form.is_valid():
                new_player = form.save(commit = False)
                new_player.session = get_object_or_404(Session, pk=session_pk)
                new_player.save()

    decks = Deck.objects.order_by("name")
    players = get_players(player_list)
    return render(request, 'game/game.html', {'players':players, "decks":decks, "session":session_pk, "form":new_player_form})

def play(request, session_pk):
    # sets up the play room 
    decks = Deck.objects.order_by("pk")
    deck = get_object_or_404(Player, is_deck=True, session=session_pk)
    prompt_cards = PromptCard.objects.filter(won_by=deck)
    active_card = False

    # checks for active prompt and activates one if needed 
    for card in prompt_cards:
        if card.is_active == True:
            prompt_card = card
            active_card = True

    if not active_card:
        card_pos = randint(0, len(prompt_cards) - 1)
        prompt_card = prompt_cards[card_pos]
        prompt_card.is_active = True
        prompt_card.save()

    player_list = Player.objects.filter(session=session_pk)
    players = get_players(player_list)

    fill_hands(player_list, deck)

    return render(request, 'game/play.html', {'players':players, "decks":decks, "prompt_card":prompt_card, "session":session_pk})

def judge(request, session_pk):
    prompt_card = None
    deck = get_object_or_404(Player, is_deck=True, session=session_pk)
    play_card_form = PlayCardForm

    if "play-card" in request.POST:
        # a player plays a card
        form = PlayCardForm(request.POST)
        if form.is_valid():
            player = get_object_or_404(Player, pk=form.cleaned_data["player"])
            if not player.has_played: # makes sure player doesn't play twice
                noun_card = get_object_or_404(NounCard, pk=form.cleaned_data["noun_card"])
                prompt_card = get_object_or_404(PromptCard, pk=form.cleaned_data["prompt_card"])               

                noun_card.with_prompt = prompt_card
                noun_card.save()
                player.has_played = True
                player.save()
        else: 
            print("Play card form invalid")
    
    # checks how many players have played
    players = Player.objects.filter(session=session_pk)
    done_players = 1 # 1 for the deck

    for player in players:
        if player.has_played:
            done_players += 1

    # gets cards for context
    if(not prompt_card):
        prompt_card = get_object_or_404(PromptCard, is_active=True, won_by=deck)
    noun_cards = NounCard.objects.filter(with_prompt=prompt_card)
    
    if "judge-button" in request.POST:
        # the judge chooses a winner, retires the prompt card
        winning_card_pk = request.POST["winning_card"]
        winning_card = get_object_or_404(NounCard, pk=winning_card_pk)
        winning_player = winning_card.in_hand
        winning_prompt = winning_card.with_prompt

        winning_prompt.won_by = winning_player
        winning_prompt.is_active = False
        winning_prompt.save()

        for card in noun_cards:
            # removes card from player hand and removes it's association with the prompt if it is not the winner
            card.in_hand = None
            if not winning_card:
                card.with_prompt = None
            card.save()

        for player in players:
            player.has_played = False
            player.save()

        return render(request, 'game/judging.html', {"judge_time":False, "end_round":True, 'winning_player':winning_player, "prompt_card":winning_prompt, "winning_card":winning_card, "session":session_pk})
    
    # initiate judging
    if done_players >= len(players):
        return render(request, 'game/judging.html', {"judge_time":True, "end_round":False, "noun_cards":noun_cards, 'players':players, "prompt_card":prompt_card, "session":session_pk})

    # waiting room
    return render(request, 'game/judging.html', {"judge_time":False, "end_round":False, 'players':players, "prompt_card":prompt_card, "noun_cards":noun_cards, "session":session_pk, "form":play_card_form})

def create_card(request):
    if request.is_ajax and request.method == 'POST':
       # convert ajax into dictionary 
       # TODO figure out a less hacky way of doing this
        data = (dict(request.POST)["cleanData"][0])
        data = urllib.parse.parse_qs(data)
        for key, value in data.items():
            data[key] = value[0]

        # make the new card
        form = NewCardForm(data)
    
        if form.is_valid():
            print(form)
            card = form.save()
            clean_card = serializers.serialize('json', [card, ])
            return JsonResponse({"card":clean_card,}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=200)
    else:
        return JsonResponse({"error": "404"}, status=400)

def get_players(player_list):
    # helper function to make a player : hand dictionary
    players = {}
    for player in player_list:
        hand = NounCard.objects.filter(in_hand = player)
        players[player] = hand
    return players

def fill_hands(player_list, deck):
    # fills players hands up to card limit
     for player in player_list:
            if player != deck:
                cards_left = len(NounCard.objects.filter(in_hand = deck))
                if cards_left > 0:
                    num_of_cards = len(NounCard.objects.filter(in_hand = player))
                    for x in range(num_of_cards, player.hand_size):
                        deck_cards = (NounCard.objects.filter(in_hand = deck))
                        if len(deck_cards) > 0:
                            rand_pos = randint(0, len(deck_cards))
                            card = deck_cards[rand_pos]
                            card.in_hand = player
                            card.save()