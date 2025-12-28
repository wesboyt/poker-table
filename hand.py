from concurrent.futures import ProcessPoolExecutor

from pokerkit import Automation, NoLimitTexasHoldem, Mode, parse_range, calculate_equities, StandardHighHand, calculate_hand_strength
import random
import copy


def parseAction(input):
    playerSeat = int(input[1:2])
    if input[2] == 'f':
        playerChips = -1
    else:
        playerChips = int(input[3:])
    return playerSeat, playerChips

class Hand:
    def __init__(self, u_hand=None, auto_deal=True):
        self.auto_deal = auto_deal
        self.done = False
        self.processor = None
        if not u_hand:
            self.u_hand = self._from_scratch(6,100,200, 200 * 20, random.randint(200*100, 200 * 500))
            self.active_players = 6

        else:
            self.u_hand = [[], [], [], [], [], [], [], []]
            for index, val in enumerate(u_hand):
                sub_array = self.u_hand[index]
                for sub_val in val:
                    sub_array.append(sub_val)

            self.big_blind = parseAction(u_hand[2][-1])[1]
            self.small_blind = parseAction(u_hand[2][-2])[1]
            stacks = []
            self.player_count = len(u_hand[2]) - 2
            self.active_players = self.player_count
            for i in range(self.player_count):
                stacks.append(parseAction(u_hand[2][i])[1])
            stacks = tuple(stacks)
            self.state = NoLimitTexasHoldem.create_state(
                (
                    Automation.ANTE_POSTING,
                    Automation.BET_COLLECTION,
                    Automation.BLIND_OR_STRADDLE_POSTING,
                    Automation.HAND_KILLING,
                    Automation.CHIPS_PUSHING,
                    Automation.CHIPS_PULLING,
                ),
                True,
                0,
                (self.small_blind, self.big_blind),
                self.big_blind,
                stacks,
                self.player_count,
            )
            self.state.mode = Mode.CASH_GAME
            for i in range(self.player_count):
                if u_hand[0][i]:
                    self.state.deal_hole(u_hand[0][i])
                else:
                    self.state.deal_hole('????')

            self.preflop_stacks = self.state.starting_stacks
            street = len(u_hand[1])
            for action in u_hand[3]:
                player, chips = parseAction(action)
                actor = self.state.turn_index
                if actor != None:
                    invested = self.state.bets[actor]
                else:
                    invested = 0


                if chips < 0:
                    if self.state.checking_or_calling_amount != 0:
                        self.state.fold()
                        self.active_players -= 1
                    else:
                        print("chips:", chips, "action:", action, "hand:", self.u_hand)
                else:
                    minimum = self.state.checking_or_calling_amount
                    if chips <= minimum:
                        self.state.check_or_call()
                    else:
                        self.state.complete_bet_or_raise_to(chips + invested)
            if street > 0:
                self.state.burn_card('??')
                for i in range(3):
                    self.state.deal_board(u_hand[1][i])
                for action in u_hand[4]:
                    player, chips = parseAction(action)
                    actor = self.state.turn_index
                    invested = self.state.bets[actor]
                    if chips < 0:
                        self.state.fold()
                        self.active_players -= 1
                    else:
                        min = self.state.checking_or_calling_amount
                        if chips <= min:
                            self.state.check_or_call()
                        else:
                            self.state.complete_bet_or_raise_to(chips + invested)
            if street > 3:
                self.state.burn_card('??')
                self.state.deal_board(u_hand[1][3])
                for action in u_hand[5]:
                    player, chips = parseAction(action)
                    actor = self.state.turn_index
                    invested = self.state.bets[actor]
                    if chips < 0:
                        self.state.fold()
                        self.active_players -= 1
                    else:
                        min = self.state.checking_or_calling_amount
                        if chips <= min:
                            self.state.check_or_call()
                        else:
                            self.state.complete_bet_or_raise_to(chips + invested)
            if street > 4:
                self.state.burn_card('??')
                self.state.deal_board(u_hand[1][4])
                for action in u_hand[6]:
                    player, chips = parseAction(action)
                    actor = self.state.turn_index
                    invested = self.state.bets[actor]
                    if chips < 0:
                        self.state.fold()
                        self.active_players -= 1
                    else:
                        min = self.state.checking_or_calling_amount
                        if chips <= min:
                            self.state.check_or_call()
                        else:
                            self.state.complete_bet_or_raise_to(chips + invested)

    def get_action_space(self):
        if self.done:
            return False
        options = {}
        if self.state.can_check_or_call():
            call_or_check = self.state.checking_or_calling_amount
            if self.state.checking_or_calling_amount == 0:
                options['check'] = 0
            else:
                options['call'] = call_or_check
        if self.state.checking_or_calling_amount != 0:
            options['fold'] = 0
        if self.state.min_completion_betting_or_raising_to_amount != None:
            options['min_bet'] = self.state.min_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
        if self.state.max_completion_betting_or_raising_to_amount != None:
            options['max_bet'] = self.state.max_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
        options['player'] = self.state.turn_index
        return options

    def shuffle(self):
        random.shuffle(self.state.deck_cards)

    def equity(self):
        ranges = []
        found_unknown = False
        player_count = 0

        for holecards in self.state.hole_cards:
            if len(holecards):
                if holecards[0].unknown_status:
                    found_unknown = True
                    player_count += 1
                else:
                    ranges.append(tuple([tuple(holecards)]))
                    player_count += 1
        ranges = tuple(ranges)
        board = []

        for cardlist in self.state.board_cards:
            for card in cardlist:
                board.append(card)
        board = tuple(board)
        if found_unknown:
            return [calculate_hand_strength(player_count, ranges[0], board, 2,5, self.state.deck,(StandardHighHand,), sample_count=1000)]
        else:
            equities = calculate_equities(ranges, board, 2,5, self.state.deck,(StandardHighHand,), sample_count=1000)
            equity = []
            eq_index = 0
            for hc in self.state.hole_cards:
                if hc:
                    equity.append(equities[eq_index])
                    eq_index += 1
                else:
                    equity.append(0)
            return equity



    def post_action(self):
        if self.state.can_select_runout_count():
            self.state.select_runout_count(1)
        if self.active_players > 1:
            if self.auto_deal:
                while self.state.can_burn_card():
                    self.state.burn_card('??')
                    while self.state.can_deal_board():
                        board_cards = map(self._state_card_to_text, self.state.deal_board().cards)
                        for card in board_cards:
                            self.u_hand[1].append(card)
        if self.state.street == None and self.auto_deal:
            for player_index, payoff in enumerate(self.state.payoffs):
                if payoff > 0:
                    tax = min(payoff * .05, 2 * self.big_blind)
                    payoff -= tax
                    self.u_hand[-1].append("p" + str(player_index) + "c" + str(int(payoff)))
            self.done = True

    def pot_size(self):
        return sum(self.state.starting_stacks) - sum(self.state.stacks)

    def call(self):
        current_player = self.state.turn_index
        chips = self.state.checking_or_calling_amount
        if self.state.can_check_or_call() and chips:
                self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c" + str(chips))
                self.state.check_or_call()
        self.post_action()
        return True

    def bet_or_raise(self, chips :int):
        #chips is the additional amount placed in middle, not the new total.
        current_player = self.state.turn_index
        minimum = self.state.min_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
        if self.state.max_completion_betting_or_raising_to_amount == None:
            maximum = self.state.checking_or_calling_amount - self.state.bets[self.state.turn_index]
            print("found none")
        else:
            maximum = self.state.max_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
        if chips > maximum:
            chips = maximum
        elif chips < minimum:
            chips = minimum
        self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c" + str(chips))
        self.state.complete_bet_or_raise_to(chips + self.state.bets[self.state.turn_index])
        self.post_action()
        return True

    def check(self):
        current_player = self.state.turn_index
        if self.state.can_check_or_call() and self.state.checking_or_calling_amount == 0:
            self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c0")
            self.state.check_or_call()
            self.post_action()
            return True
        else:
            print("check:", self.state.can_check_or_call(), self.state.checking_or_calling_amount, self.u_hand)
            return False

    def fold(self):
        if self.state.can_fold():
            current_player = self.state.turn_index
            self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "f")
            self.state.fold()
            self.active_players = self.active_players - 1
            self.post_action()
            return True
        else:
            print("couldnt fold:", self.u_hand, )
            return False

    def _state_card_to_text(self, card):
        return card.rank + card.suit

    def get_u_hand(self, player=None):
        #get u_hand from perspective of current player
        temp_u_hand = copy.deepcopy(self.u_hand)
        if player == None:
            player_index = self.state.turn_index
        else:
            player_index = player
        for i in range(self.player_count):
            if i != player_index:
                temp_u_hand[0][i] = ""
        return temp_u_hand

    def _from_scratch(self,  player_count : int, small_blind :int, big_blind :int, min_stack_size :int, max_stack_size :int):
        #deal hole cards, randomly assign starting stacks, finish setting up state.
        self.big_blind = big_blind
        self.small_blind = small_blind
        stacks = []
        self.player_count = player_count
        self.u_hand = [[], [], [], [], [], [], [], []]

        for i in range(player_count):
            stack = random.randint(min_stack_size, max_stack_size)
            stacks.append(stack)
            self.u_hand[2].append("p" + str(i) + "c" + str(stack))
        self.u_hand[2].append("p0c" + str(self.small_blind))
        self.u_hand[2].append("p1c" + str(self.big_blind))
        stacks = tuple(stacks)
        self.state = NoLimitTexasHoldem.create_state(
            (
                Automation.ANTE_POSTING,
                Automation.BET_COLLECTION,
                Automation.BLIND_OR_STRADDLE_POSTING,
                Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
                Automation.HAND_KILLING,
                Automation.CHIPS_PUSHING,
                Automation.CHIPS_PULLING,
                Automation.RUNOUT_COUNT_SELECTION
            ),
            True,
            0,
            (self.small_blind, self.big_blind),
            self.big_blind,
            stacks,
            self.player_count,
        )
        self.preflop_stacks = self.state.starting_stacks
        for i in range(self.player_count):
            hole_cards = "".join(map(self._state_card_to_text,self.state.deal_hole(2).cards))
            self.u_hand[0].append(hole_cards)
        return self.u_hand

if __name__ == '__main__':
    hand = Hand([["", "", "", "", "4d5h", ""], ["7s", "6s", "3d"], ["p0c30457", "p1c23785", "p2c7234", "p3c18815", "p4c12575", "p5c10289", "p0c100", "p1c200"], ["p2f", "p3f", "p4c200", "p5c875", "p0f", "p1f", "p4c675"], [], [], [], []])
    print(hand.equity())
    for i in range(1):
        hand = Hand()
        hand.fold()
        print(hand.equity())
