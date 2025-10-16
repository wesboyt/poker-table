from pokerkit import Automation, NoLimitTexasHoldem, Mode, Folding, HoleDealing, CheckingOrCalling, BlindOrStraddlePosting, CompletionBettingOrRaisingTo, BoardDealing
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
    def __init__(self, u_hand=None):
        self.done = False
        if not u_hand:

            self.u_hand = self._from_scratch(6,100,200,200 * 20 , random.randint(200 * 100, 200 * 500))

        else:
            self.u_hand = [[], [], [], [], [], [], [], [], []]
            for index, val in enumerate(u_hand):
                sub_array = self.u_hand[index]
                for sub_val in val:
                    sub_array.append(sub_val)

            self.big_blind = parseAction(u_hand[2][-1])[1]
            self.small_blind = parseAction(u_hand[2][-2])[1]
            stacks = []
            self.player_count = len(u_hand[2]) - 2
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
                invested = self.state.bets[actor]


                if chips < 0:
                    self.state.fold()
                else:
                    minimum = self.state.checking_or_calling_amount
                    if chips <= minimum:
                        self.state.check_or_call()
                    else:
                        self.state.complete_bet_or_raise_to(chips + invested)
            if street == 3:
                self.state.burn_card('??')
                for i in range(3):
                    self.state.deal_board(u_hand[1][i])
                for action in u_hand[4]:
                    player, chips = parseAction(action)
                    actor = self.state.turn_index
                    invested = self.state.bets[actor]
                    if chips < 0:
                        self.state.fold()
                    else:
                        min = self.state.checking_or_calling_amount + invested
                        if chips <= min:
                            self.state.check_or_call()
                        else:
                            self.state.complete_bet_or_raise_to(chips + invested)
            elif street == 4:
                self.state.burn_card('??')
                self.state.deal_board(u_hand[1][3])
                for action in u_hand[5]:
                    player, chips = parseAction(action)
                    actor = self.state.turn_index
                    invested = self.state.bets[actor]
                    if chips < 0:
                        self.state.fold()
                    else:
                        min = self.state.checking_or_calling_amount + invested
                        if chips <= min:
                            self.state.check_or_call()
                        else:
                            self.state.complete_bet_or_raise_to(chips + invested)
            elif street == 5:
                self.state.burn_card('??')
                self.state.deal_board(u_hand[1][4])
                for action in u_hand[6]:
                    player, chips = parseAction(action)
                    actor = self.state.turn_index
                    invested = self.state.bets[actor]
                    if chips < 0:
                        self.state.fold()
                    else:
                        min = self.state.checking_or_calling_amount + invested
                        if chips <= min:
                            self.state.check_or_call()
                        else:
                            self.state.complete_bet_or_raise_to(chips + invested)

    def get_action_space(self):
        if self.done:
            return False
        #return player index of whos turn it is
        #return available options fold, check, call, raise, unavailable options will be missing.
        #0,{fold:0, check:0, call_chips:x, min_chips:x, max_chips:x, player:x}
        #if it is time to deal cards, do so and return next player up's action space
        options = {}
        if self.state.can_check_or_call():
            call_or_check = self.state.checking_or_calling_amount
            if self.state.checking_or_calling_amount == 0:
                options['check'] = 0
            else:
                options['call_chips'] = call_or_check
        if self.state.can_fold():
            options['fold'] = 0
        if self.state.min_completion_betting_or_raising_to_amount != None:
            options['min_chips'] = self.state.min_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
        if self.state.max_completion_betting_or_raising_to_amount != None:
            options['max_chips'] = self.state.max_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
        options['player'] = self.state.turn_index
        return options

    def make_action(self, player :int, chips :int):
        if self.done:
            return False
        current_player = self.state.turn_index
        if player != current_player:
            return False
        if chips == 0:
            if self.state.can_check_or_call() and self.state.checking_or_calling_amount == 0:
                self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c0")
                self.state.check_or_call()
            elif self.state.can_fold():
                self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "f")
                self.state.fold()
            else:
                print("ERROR: 0 chips when not possible.")
                return False
        else:
            min = self.state.checking_or_calling_amount
            if chips == min:
                self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c" + str(chips))
                self.state.check_or_call()
            elif chips < min:
                print("ERROR:", chips, min, self.state.bets)
                return False
            else:
                if self.state.min_completion_betting_or_raising_to_amount == None:
                    size = self.state.checking_or_calling_amount
                    self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c" + str(size))
                    self.state.check_or_call()
                else:
                    minimum = self.state.min_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
                    if self.state.max_completion_betting_or_raising_to_amount == None:
                        maximum = self.state.checking_or_calling_amount - self.state.bets[self.state.turn_index]
                    else:
                        maximum = self.state.max_completion_betting_or_raising_to_amount - self.state.bets[self.state.turn_index]
                    if chips > maximum:
                        chips = maximum
                    elif chips < minimum:
                        chips = minimum
                    self.u_hand[self.state.street_index + 3].append("p" + str(current_player) + "c" + str(chips))
                    self.state.complete_bet_or_raise_to(chips + self.state.bets[self.state.turn_index])
        if self.state.can_select_runout_count():
            self.state.select_runout_count(1)
        while self.state.can_burn_card():
            self.state.burn_card('??')
            while self.state.can_deal_board():
                board_cards = map(self._state_card_to_text, self.state.deal_board().cards)
                for card in board_cards:
                    self.u_hand[1].append(card)
        if self.state.street == None:
            for player_index, payoff in enumerate(self.state.payoffs):
                if payoff > 0:
                    self.u_hand[-1].append("p" + str(player_index) + "c" + str(payoff))
            self.done = True
        return True

    def _state_card_to_text(self, card):
        return card.rank + card.suit

    def get_u_hand(self):
        #get u_hand from perspective of current player
        temp_u_hand = copy.deepcopy(self.u_hand)
        player_index = self.state.turn_index
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
        self.u_hand = [[], [], [], [], [], [], [], [], []]

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
        #self.state.mode = Mode.CASH_GAME
        self.preflop_stacks = self.state.starting_stacks
        for i in range(self.player_count):
            hole_cards = "".join(map(self._state_card_to_text,self.state.deal_hole(2).cards))
            self.u_hand[0].append(hole_cards)
        return self.u_hand

#self.state.hole_cards
#self.state.payoffs->win/loss
#self.state.board_cards
#self.state.turn_index()

if __name__ == '__main__':
    hand = Hand([["","","","","","9hKc"],["Js","Ts","9s"],["p0c100","p1c99","p2c109","p3c102","p4c110","p5c85","p0c1","p1c2"],["p2f","p3f","p4f","p5c43","p0f", "p1c41"],[],[],[]])
    for i in range(5):
        hand = Hand()
