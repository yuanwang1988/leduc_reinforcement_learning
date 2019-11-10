from deuces import Card
from deuces import Deck
from deuces import Evaluator

class Poker:
    '''
    State (dict):
      currentPlayer (str): Player1, Player2, Dealer (which agent is going to take an action)
      player1Hand (list): card1, card2
      player2Hand (list): card1, card2
      player1Actions (list): check, call, ...
      communityCards (list): card1, card2, ...
      deck: current deck
      player1Bets (list): bet1, bet2 (these are additions to the pot)
      player2Bets (list): bet1, bet2 (these are additions to the pot)
      player1Stack (int): player1's stack
      player2Stack (int): player2's stack
      player1Fold (bool): if player1 folds
      player2Fold (bool): if player2 folds
    '''

    def __init__(self, num_rounds = 2, hand_size=2, player1Stack=100, player2Stack=100):
        self.num_rounds = num_rounds
        self.evaluator = Evaluator()
        self.state = {}
        self.state['deck'] = Deck()
        self.state['currentPlayer'] = 'Player1'
        self.state['player1Hand'] = [self.state['deck'].draw(1) for i in range(hand_size)]
        self.state['player2Hand'] = [self.state['deck'].draw(1) for i in range(hand_size)]
        self.state['player1Actions'] = []
        self.state['communityCards'] = []
        self.state['player1Bets'] = []
        self.state['player2Bets'] = []
        self.state['player1Stack'] = player1Stack
        self.state['player2Stack'] = player2Stack
        self.state['player1Fold'] = False
        self.state['player2Fold'] = False
        self.actions = ['call', 'bet', 'raise', 'fold', 'check']

    def printState(self):
        print('Current Game State')
        print('currentPlayer: {}'.format(self.state['currentPlayer']))
        print('player1Hand:')
        Card.print_pretty_cards(self.state['player1Hand'])
        print('player2Hand:')
        Card.print_pretty_cards(self.state['player2Hand'])
        print('player1Actions:{}'.format(self.state['player1Actions']))
        print('communityCards')
        Card.print_pretty_cards(self.state['communityCards'])
        print('player1Bets: {}'.format(self.state['player1Bets']))
        print('player2Bets: {}'.format(self.state['player2Bets']))
        print('player1Stack: {}'.format(self.state['player1Stack']))
        print('player2Stack: {}'.format(self.state['player2Stack']))
        print('player1Fold: {}'.format(self.state['player1Fold']))
        print('player2Fold: {}'.format(self.state['player2Fold']))

    def refreshState(self):
        self.state['currentPlayer'] = 'Player1'
        self.state['player1Actions'] = []

    def successor(self, state, action):
        '''
            return the successor state given the current state and action.
        '''
        current_player = self.state['currentPlayer']
        if current_player == 'Player1':
            # Player1's first action in a round
            if len(self.state['player1Actions']) == 0:
                if action == 'check':
                    # do nothing
                    pass
                elif action == 'bet':
                    self.state['player1Bets'].append(1)
                    self.state['player1Stack'] -= 1
                else:
                    print("Invalid action.")
                self.state['currentPlayer'] = 'Player2'
            else:
                if action == 'call':
                    self.state['player1Bets'].append(1)
                    self.state['player1Stack'] -= 1
                elif action == 'fold':
                    self.state['player1Fold'] = True
                else:
                    print("Invalid action.")
                self.state['currentPlayer'] = 'Dealer'
            # Append player1's action to the state.
            self.state['player1Actions'].append(action)
        elif current_player == 'Player2':
            # if player2 not raise, next player will be Dealer.
            self.state['currentPlayer'] = 'Dealer'
            if action == 'check':
                # do nothing
                pass
            elif action == 'fold':
                self.state['player2Fold'] = True
            elif action == 'call':
                self.state['player2Bets'].append(1)
                self.state['player2Stack'] -= 1
            elif action == 'raise':
                raise_amount = 1
                if self.state['player1Actions'][0] == 'bet':
                    raise_amount = 2
                self.state['player2Bets'].append(raise_amount)
                self.state['player2Stack'] -= raise_amount
                self.state['currentPlayer'] = 'Player1'
            else:
                print("Invalid action.")
        elif current_player == 'Dealer':
            num_to_draw = 1
            if len(self.state['communityCards']) == 0:
                num_to_draw = 3
            # Draw 1 or 3 random card to the communityCards. refreshState back to currentPlayer = player1.
            self.state['communityCards'].append(self.state['deck'].draw(num_to_draw))
            self.refreshState()

        else:
            print("Invalid input state.")

    def isEnd(self):
        if len(self.state['communityCards']) == self.num_rounds:
            return True
        if self.state['player1Fold'] or self.state['player2Fold']:
            return True
        else:
            return False

    def actions(self):
        def maxBet(state):
            return min(state['player1Stack'], state['player2Stack'])

        if self.state['currentPlayer'] == 'Dealer':
            return ['draw_card']

        if self.state['currentPlayer'] == 'Player1':
            if sum(self.state['player1Bets']) == sum(self.state[
                                                         'player2Bets']):  # this is the bit that tells player1 if he is going for the first time
                if maxBet(state) > 0:
                    return ['check', 'bet']
                else:
                    return ['check']
            else:
                return ['fold', 'call']

        if self.state['currentPlayer'] == 'Player2':
            if sum(self.state['player1Bets']) > sum(self.state['player2Bets']):
                return ['fold', 'call', 'raise']
            else:
                if maxBet(state) > 0:
                    return ['check', 'raise']
                else:
                    return ['check']

    def currentUtilityEstimate(self):
        def pot(state):
            return sum(state['player1Bets']) + sum(state['player2Bets'])

        if self.state['player1Fold']:
            return self.state['player1Stack'] - self.state['player2Stack'] - pot(self.state)
        if self.state['player2Fold']:
            return self.state['player1Stack'] - self.state['player2Stack'] + pot(self.state)

        player1HandVal = self.evaluator.evaluate(self.state['player1Hand'], self.state['communityCards'])
        player2HandVal = self.evaluator.evaluate(self.state['player2Hand'], self.state['communityCards'])
        if player1HandVal > player2HandVal:
            return self.state['player1Stack'] - self.state['player2Stack'] + pot(self.state)
        else:
            return self.state['player1Stack'] - self.state['player2Stack'] - pot(self.state)

    def utility(self):
        if self.isEnd():
            return self.currentUtilityEstimate()
        else:
            return 0

    def player(self):
        return self.state['currentPlayer']


num_rounds = 2
hand_size = 2
leducGame = Poker(hand_size=hand_size, num_rounds=num_rounds)
for i in range(num_rounds):
    if leducGame.isEnd():
        print('utility: {}'.format(leducGame.utility()))
        break
    while True:
        if leducGame.player() == 'Dealer':
            leducGame.state['communityCards'].append(leducGame.state['deck'].draw(1))
            leducGame.state['currentPlayer'] = 'Player1'
            break
        elif leducGame.player() == 'Player1':
            leducGame.state['currentPlayer'] = 'Player2'
        elif leducGame.player() == 'Player2':
            leducGame.state['currentPlayer'] = 'Dealer'

    leducGame.printState()
    print('currentUtilityEstimate: {}'.format(leducGame.currentUtilityEstimate()))

leducGame = Poker(hand_size=1)
leducGame.printState()
print("*********************\n")
leducGame.successor(leducGame.state, 'bet')
leducGame.successor(leducGame.state, 'raise')
leducGame.successor(leducGame.state, 'call')
leducGame.printState()
