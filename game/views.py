from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.contrib.sessions.models import Session as Cookie
from .models import Player, PromptCard, NounCard, Session, Deck, AllCards
from .forms import NewNounCardForm, NewPromptCardForm, NewSessionForm, NewPlayerForm, NewCardForm, PlayCardForm
from random import randint
import urllib.parse

CARD_SELECT = 0
JUDGING = 1
WINNER = 2

def index(request):
    if request.method == 'POST':
        if "start" in request.POST:
            # start new session. 
            form = NewSessionForm(request.POST)
            if form.is_valid():
                new_session = form.save()
                
                # make and populate the deck
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
        elif "delete-session" in request.POST:
            # delete an existing session.
            session_pk = dict(request.POST)["delete-session"][0]

            get_object_or_404(Session, pk=session_pk).delete()
            

    # get decks and sessions, render page
    deck_list = Deck.objects.order_by("pk")
    session_list = Session.objects.order_by("name")
    if not request.session.exists(request.session.session_key):
        request.session.create() 
    return render(request, 'game/index.html', {"session_list":session_list, "decks":deck_list})

def game(request, session_pk):
    player_list = Player.objects.filter(session=session_pk)
    new_player_form = NewPlayerForm
    active_player = None
    need_judge = True

    if request.method == 'POST':
        if "join" in request.POST:
            # make a new player
            form = NewPlayerForm(request.POST)
            if form.is_valid():
                new_player = form.save(commit = False)
                player_cookie = Cookie.objects.get(session_key=request.session.session_key)
                new_player.cookie = player_cookie
                new_player.session = get_object_or_404(Session, pk=session_pk)

                for player in player_list:
                    if player.is_judge:
                        need_judge = False
                if need_judge:
                    new_player.is_judge = True

                new_player.save()

    decks = Deck.objects.order_by("name")
    players = get_players(player_list)

    for player in player_list:
        current_cookie = Cookie.objects.get(session_key=request.session.session_key)
        if player.cookie == current_cookie:
            active_player = player
    
    return render(request, 'game/game.html', {"active_player":active_player, 'players':players, "decks":decks, "session":session_pk, "form":new_player_form})

def play(request, session_pk):
    # sets up the play room 
    deck = get_object_or_404(Player, is_deck=True, session=session_pk)
    session = get_object_or_404(Session, pk=session_pk)
    decks = Deck.objects.order_by("pk")
    prompt_cards = PromptCard.objects.filter(won_by=deck)
    player_list = Player.objects.filter(session=session_pk)
    active_card = active_player = judge_player = prompt_card = None

    active_cards = PromptCard.objects.filter(is_active=True)

    for player in player_list:
        if player.is_judge:
            judge_player = player
        
        for card in active_cards:
            if card.won_by == player and player != deck:
                card.is_active = False
                card.save()
                active_card = False

    # checks for active prompt and activates one if needed 
    for card in prompt_cards:
        if card.is_active == True:            
            prompt_card = card
            active_card = True

    if not active_card:
        if(len(prompt_cards) > 0):
            card_pos = randint(0, len(prompt_cards) - 1)
            prompt_card = prompt_cards[card_pos]
            while prompt_card.num_blanks > 1:
                # TODO Make this less hacky
                card_pos = randint(0, len(prompt_cards) - 1)
                prompt_card = prompt_cards[card_pos]
            prompt_card.is_active = True
            prompt_card.save()
            active_card = True

    if session.game_stage == WINNER:        
        session.game_stage = CARD_SELECT
        session.save()

        active_card = None

        player_list = list(player_list)

        judge_index = player_list.index(judge_player)
        judge_player.is_judge = False
        judge_player.save()
        if judge_index + 1 < len(player_list):
            judge_player = player_list[judge_index + 1]
            judge_player.is_judge = True
            judge_player.save()
        else:
            judge_player = player_list[1]
            judge_player.is_judge = True
            judge_player.save()

    players = get_players(player_list)

    fill_hands(player_list, deck)

    for player in player_list:
        current_cookie = Cookie.objects.get(session_key=request.session.session_key)
        if player.cookie == current_cookie:
            active_player = player

    player_list = list(player_list)

    return render(request, 'game/play.html', {'active_player':active_player, 'players':players, "decks":decks, "prompt_card":prompt_card, "session":session_pk})

def judge(request, session_pk):
    decks = Deck.objects.order_by("pk")
    player_list = Player.objects.filter(session=session_pk)
    active_player = prompt_card = winning_card = winning_player = None
    end_round = False
    session = get_object_or_404(Session, pk=session_pk)
    play_card_form = PlayCardForm

    if "play-card" in request.POST:
        # a player plays a card
        form = PlayCardForm(request.POST)
        if form.is_valid():
            player = get_object_or_404(Player, pk=form.cleaned_data["player"])
            if not player.has_played: # makes sure player doesn't play twice
                noun_card = get_object_or_404(NounCard, pk=form.cleaned_data["noun_card"])
                prompt_card = get_object_or_404(PromptCard, pk=form.cleaned_data["prompt_card"])    

                print(prompt_card.card_text)           

                noun_card.with_prompt = prompt_card
                noun_card.save()

                player.has_played = True
                player.save()
        else: 
            print("Play card form invalid")
    
    # checks how many players have played
    players = Player.objects.filter(session=session_pk)
    done_players = 2 # 1 for the deck, 1 for judge

    for player in players:
        if player.has_played:
            done_players += 1

    # gets cards for context
    if(not prompt_card):
        prompt_cards = get_list_or_404(PromptCard, is_active=True)
        for card in prompt_cards:
            for player in player_list:
                if card.won_by == player:
                    prompt_card = card

    noun_cards = NounCard.objects.filter(with_prompt=prompt_card)

    # initiate judging
    if done_players >= len(players):
        judge_time = True
    else:
        judge_time = False

    if "judge-button" in request.POST:
        # the judge chooses a winner, retires the prompt card

        winning_card_pk = request.POST["winning_card"]
        winning_card = get_object_or_404(NounCard, pk=winning_card_pk)

        session.game_stage = WINNER
        session.save()

        for card in noun_cards:
            # removes card from player hand and removes it's association with the prompt if it is not the winner            
            if card == winning_card:
                prompt_card.won_by = card.in_hand
                prompt_card.save()

            card.in_hand = None

            if card != winning_card:
                card.with_prompt = None

            card.save()

        for player in players:
            player.has_played = False
            player.save()

        end_round = True
        judge_time = False

    if session.game_stage == WINNER:
        judge_time = False
        end_round = True

        winning_card = get_object_or_404(NounCard, with_prompt=prompt_card)
        winning_player = prompt_card.won_by

    for player in player_list:
        current_cookie = Cookie.objects.get(session_key=request.session.session_key)
        if player.cookie == current_cookie:
            active_player = player
            
    # waiting room
    return render(request, 'game/judging.html', {"active_player":active_player, "decks":decks, "judge_time":judge_time, "end_round":end_round, 'winning_player':winning_player, "winning_card":winning_card, 'players':players, "prompt_card":prompt_card, "noun_cards":noun_cards, "session":session_pk, "form":play_card_form})

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
                            rand_pos = randint(0, len(deck_cards) - 1)
                            card = deck_cards[rand_pos]
                            card.in_hand = player
                            card.save()