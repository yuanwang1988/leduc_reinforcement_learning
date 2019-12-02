import copy
from collections import defaultdict
from deuces import Card
from deuces import Deck
from deuces import Evaluator
import math
import random

########################
# Poker Game Simulator #
########################

evaluator = Evaluator()

def legalActions(state):
    def maxBet(state):
        return min(state['player1Stack'], state['player2Stack'])

    if state['currentPlayer'] == 'Dealer':
        return ['draw_card']

    if state['currentPlayer'] == 'Player1':
        if sum(state['player1Bets']) == sum(state['player2Bets']):
            if maxBet(state) > 0:
                return ['check', 'bet']
            else:
                return ['check']
        else:
            return ['fold', 'call']

    if state['currentPlayer'] == 'Player2':
        if sum(state['player1Bets']) > sum(state['player2Bets']):
            return ['fold', 'call', 'raise']
        else:
            if maxBet(state) > 0:
                return ['check', 'raise']
            else:
                return ['check']

class Poker:
    '''
    State (dict):
      currentPlayer (str): Player1, Player2, Dealer (which agent is going to take an action)
      player1Hand (list): card1, card2
      player2Hand (list): card1, card2
      player1legalActions (list): check, call, ...
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
        self.player1StackStart = player1Stack
        self.player2StackStart = player2Stack
        self.evaluator = Evaluator()
        self.future_cards_for_oracle = []
        self.state = {}
        self.state['deck'] = Deck()
        self.state['currentPlayer'] = 'Player1'
        self.state['player1Hand'] = [self.state['deck'].draw(1) for i in range(hand_size)]
        self.state['player2Hand'] = [self.state['deck'].draw(1) for i in range(hand_size)]
        self.state['player1legalActions'] = []
        self.state['communityCards'] = self.state['deck'].draw(3)
        self.state['player1Bets'] = []
        self.state['player2Bets'] = []
        self.state['player1Stack'] = player1Stack
        self.state['player2Stack'] = player2Stack
        self.state['player1Fold'] = False
        self.state['player2Fold'] = False

    def printState(self):
        print('Current Game State')
        print('currentPlayer: {}'.format(self.state['currentPlayer']))
        print('player1Hand:')
        Card.print_pretty_cards(self.state['player1Hand'])
        print('player2Hand:')
        Card.print_pretty_cards(self.state['player2Hand'])
        print('player1legalActions:{}'.format(self.state['player1legalActions']))
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
        self.state['player1legalActions'] = []

    def successor(self, state, action):
        '''
            return the successor state given the current state and action.
        '''
        current_player = self.state['currentPlayer']
        if current_player == 'Player1':
            # Player1's first action in a round
            if len(self.state['player1legalActions']) == 0:
                if action == 'check':
                    # do nothing
                    pass
                elif action == 'bet':
                    self.state['player1Bets'].append(1)
                    self.state['player1Stack'] -= 1
                elif action == 'fold':
                    # self.state['player1Bets'].append(1)
                    # self.state['player1Stack'] -= 1
                    self.state['player1Fold'] = True
                else:
                    print("Invalid action.")
                    raise
                self.state['currentPlayer'] = 'Player2'
            else:
                if action == 'call':
                    self.state['player1Bets'].append(1)
                    self.state['player1Stack'] -= 1
                elif action == 'fold':
                    self.state['player1Fold'] = True
                else:
                    print("Invalid action.")
                    raise
                self.state['currentPlayer'] = 'Dealer'
            # Append player1's action to the state.
            self.state['player1legalActions'].append(action)
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
                if self.state['player1legalActions'][0] == 'bet':
                    raise_amount = 2
                self.state['player2Bets'].append(raise_amount)
                self.state['player2Stack'] -= raise_amount
                self.state['currentPlayer'] = 'Player1'
            else:
                print("Invalid action.")
                raise
        elif current_player == 'Dealer':
            num_to_draw = 1
            if len(self.state['communityCards']) == 0:
                num_to_draw = 3
            # Draw 1 or 3 random card to the communityCards. refreshState back to currentPlayer = player1.
            self.state['communityCards'] += [self.state['deck'].draw(1) for i in range(num_to_draw)]
            self.refreshState()
        else:
            print("Invalid input state.")
            raise

    def isEnd(self):
        if len(self.state['communityCards']) == self.num_rounds:
            return True
        if self.state['player1Fold'] or self.state['player2Fold']:
            return True
        else:
            return False

    def legalActions(self, state):
        return legalActions(state)

    def currentUtilityEstimate(self):
        def pot(state):
            return sum(state['player1Bets']) + sum(state['player2Bets'])

        if self.state['player1Fold']:
            return self.state['player1Stack'] - self.player1StackStart
        if self.state['player2Fold']:
            return self.state['player1Stack'] + pot(self.state) - self.player1StackStart

        player1HandVal = self.evaluator.evaluate(self.state['player1Hand'], self.state['communityCards'])
        player2HandVal = self.evaluator.evaluate(self.state['player2Hand'], self.state['communityCards'])
        if player1HandVal > player2HandVal:
            return self.state['player1Stack'] + pot(self.state) - self.player1StackStart
        else:
            return self.state['player1Stack'] - self.player1StackStart

    def utility(self):
        if self.isEnd():
            return self.currentUtilityEstimate()
        else:
            return 0

    def player(self):
        return self.state['currentPlayer']

    def getState(self):
        return copy.deepcopy(self.state)

################
# RL Simulator #
# Assume only player1 can be a RL player, 
# player1 and player2 can both be random, baseline, random players.
################

def simulate(player1, player2, numTrials=1000, verbose=False, sort=False):
    # Return i in [0, ..., len(probs)-1] with probability probs[i].
    num_rounds = 5
    hand_size = 2

    totalRewards = []  # The rewards we get on each trial
    for trial in range(numTrials):
        leducGame = Poker(hand_size=hand_size, num_rounds=num_rounds)
        player1Sequence = [] # The sequence is state, action, reward, newState
        # For player2 is oracle player usecase.
        if isinstance(player2, OraclePlayer):
            leducGame.future_cards_for_oracle = leducGame.state['deck'].draw(2)
            leducGame.state['deck'].putBack(leducGame.future_cards_for_oracle)
        while True:
            if leducGame.isEnd():
                totalReward = leducGame.utility()
                player1.incorporateFeedback(player1Sequence[-4], player1Sequence[-3], totalReward, None)
                # print('action: {}'.format(player1Sequence[-3]))
                totalRewards.append(totalReward)
                break
            if leducGame.player() == 'Player1':
                currState = leducGame.getState()
                action = player1.getAction(leducGame)
                leducGame.successor(leducGame.state, action)
                newState = leducGame.getState()
                player1Sequence.append(currState) # currState
                player1Sequence.append(action) # action
                player1Sequence.append(0.0) # reward
                if leducGame.isEnd():
                    player1Sequence.append(newState) # newState
                # print('action: {}'.format(action))
            elif leducGame.player() == 'Player2':
                action = player2.getAction(leducGame)
                leducGame.successor(leducGame.state, action)
                if leducGame.player() == 'Player1' or leducGame.isEnd():
                    player1Sequence.append(leducGame.getState())
                if leducGame.player() == 'Player1':
                    player1.incorporateFeedback(player1Sequence[-4], player1Sequence[-3], 0, player1Sequence[-1])
            else:
                action = 'draw_card'
                leducGame.successor(leducGame.state, action)
                if leducGame.player() == 'Player1' or leducGame.isEnd():
                    player1Sequence.append(leducGame.getState())
                if leducGame.player() == 'Player1':
                    player1.incorporateFeedback(player1Sequence[-4], player1Sequence[-3], 0, player1Sequence[-1])

        if trial % 10000 == 0:
            print('******* Game {} *******'.format(trial))
            print('avg utility so far: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))

    return totalRewards

#################
# Player Agents #
#################
class Player:
    def getAction(self, game):
        return random.choice(game.legalActions(game.getState()))
    
    def incorporateFeedback(self, state, action, reward, newState):
        pass

class RandomPlayer(Player):
    def getAction(self, game):
        return random.choice(game.legalActions(game.getState()))

class BaselinePlayer(Player):
    def getAction(self, game):
        def action_given_hand_strength_pct(hand_strength_pct):
            #print('hand_strength_pct: {}'.format(hand_strength_pct))
            action_preference = []
            if hand_strength_pct > 0.9:
                action_preference = ['raise', 'call', 'bet', 'check']
            elif hand_strength_pct > 0.8:
                action_preference = ['call', 'bet', 'check']
            else:
                action_preference = ['check', 'fold']

            for action in action_preference:
                if action in game.legalActions(game.getState()):
                    return action

        if game.player() == 'Player1':
            hand_strength = game.evaluator.evaluate(game.state['player1Hand'], game.state['communityCards'])
            hand_strength_pct = game.evaluator.get_five_card_rank_percentage(hand_strength)
            return action_given_hand_strength_pct(hand_strength_pct)

        elif game.player() == 'Player2':
            hand_strength = game.evaluator.evaluate(game.state['player2Hand'], game.state['communityCards'])
            hand_strength_pct = game.evaluator.get_five_card_rank_percentage(hand_strength)
            return action_given_hand_strength_pct(hand_strength_pct)

        else:
            return 'draw_card'

class OraclePlayer(Player):
    def getAction(self, game):
        def action_given_hand_both_strength_pct(my_hand_strength_pct, opponent_hand_strength_pct, full_community_cards):
            # print('my_hand_strength_pct: {}, opponent_hand_strength_pct: {}'.format(my_hand_strength_pct, opponent_hand_strength_pct))
            # fold, check, bet, call, raise
            if my_hand_strength_pct < opponent_hand_strength_pct:
                    return 'fold'
            else:
                if 'raise' in game.legalActions(game.getState()):
                    return 'raise'
                elif 'call' in game.legalActions(game.getState()):
                    return 'call'
                elif 'bet' in game.legalActions(game.getState()):
                    return 'bet'
                else:
                    return 'check'

        full_community_cards = game.state['communityCards']
        if len(game.state['communityCards']) == 3:
            full_community_cards = game.state['communityCards'] + game.future_cards_for_oracle
        elif len(game.state['communityCards']) == 4:
            full_community_cards = game.state['communityCards'] + [game.future_cards_for_oracle[0]]

        hand_strength1 = game.evaluator.evaluate(game.state['player1Hand'], full_community_cards)
        hand_strength_pct1 = game.evaluator.get_five_card_rank_percentage(hand_strength1)
        hand_strength2 = game.evaluator.evaluate(game.state['player2Hand'], full_community_cards)
        hand_strength_pct2 = game.evaluator.get_five_card_rank_percentage(hand_strength2)

        if game.player() == 'Player1':
            return action_given_hand_both_strength_pct(hand_strength_pct1, hand_strength_pct2, full_community_cards)

        elif game.player() == 'Player2':
            return action_given_hand_both_strength_pct(hand_strength_pct2, hand_strength_pct1, full_community_cards)

        else:
            return 'draw_card'

# Abstract class: an RLAlgorithm performs reinforcement learning.  All it needs
# to know is the set of available actions to take.  The simulator (see
# simulate()) will call getAction() to get an action, perform the action, and
# then provide feedback (via incorporateFeedback()) to the RL algorithm, so it can adjust
# its parameters.
class RLAlgorithm:
    # Your algorithm will be asked to produce an action given a state.
    def getAction(self, state): raise NotImplementedError("Override me")

    # We will call this function when simulating an MDP, and you should update
    # parameters.
    # If |state| is a terminal state, this function will be called with (s, a,
    # 0, None). When this function is called, it indicates that taking action
    # |action| in state |state| resulted in reward |reward| and a transition to state
    # |newState|.
    def incorporateFeedback(self, state, action, reward, newState): raise NotImplementedError("Override me")

# Performs Q-learning.  Read util.RLAlgorithm for more information.
# actions: a function that takes a state and returns a list of actions.
# discount: a number between 0 and 1, which determines the discount factor
# featureExtractor: a function that takes a state and action and returns a list of (feature name, feature value) pairs.
# explorationProb: the epsilon value indicating how frequently the policy
# returns a random action
class QLearningAlgorithm(RLAlgorithm):
    def __init__(self, actions, featureExtractor, explorationProb=0.2):
        self.featureExtractor = featureExtractor
        self.actions = actions
        self.explorationProb = explorationProb
        self.weights = defaultdict(float)
        self.numIters = 0

    # Return the Q function associated with the weights and features
    def getQ(self, state, action):
        score = 0
        for f, v in self.featureExtractor(state, action):
            score += self.weights[f] * v
        return score

    # This algorithm will produce an action given a state.
    # Here we use the epsilon-greedy algorithm: with probability
    # |explorationProb|, take a random action.
    def getAction(self, game):
        self.numIters += 1
        if random.random() < self.explorationProb:
            return random.choice(self.actions(game.getState()))
        else:
            actions = self.actions(game.getState())
            random.shuffle(actions)
            return max((self.getQ(game.getState(), action), action) for action in actions)[1]

    # Call this function to get the step size to update the weights.
    def getStepSize(self):
        return 1.0 / math.sqrt(self.numIters + 10.0)

    # We will call this function with (s, a, r, s'), which you should use to update |weights|.
    # Note that if s is a terminal state, then s' will be None.  Remember to check for this.
    # You should update the weights using self.getStepSize(); use
    # self.getQ() to compute the current estimate of the parameters.
    def incorporateFeedback(self, state, action, reward, newState):
        # BEGIN_YOUR_CODE (our solution is 9 lines of code, but don't worry if you deviate from this)
        V_estimate_new_state = 0
        if newState != None:
            V_estimate_new_state = max([self.getQ(newState, a) for a in self.actions(newState)])

        new_Q_estimate = reward + V_estimate_new_state
        current_Q_estimate = self.getQ(state, action)
        step_size = self.getStepSize()
        for f, v in self.featureExtractor(state, action):
            self.weights[f] += step_size * (new_Q_estimate - current_Q_estimate)*v
        # END_YOUR_CODE

# Return a single indicator of the (hand strength (rounded to 1 decimal place), action)
def handActionFeatureExtractor(state, action):
    hand_strength = evaluator.evaluate(state['player1Hand'], state['communityCards'])
    hand_strength_pct = evaluator.get_five_card_rank_percentage(hand_strength)
    rounded_hand_strength = '{0:.1f}'.format(hand_strength_pct)

    return [((rounded_hand_strength, action), 1.0)]

# Return a single indicator of the (hand strength (rounded to 1 decimal place), pot, action)
def handPotActionFeatureExtractor(state, action):
    hand_strength = evaluator.evaluate(state['player1Hand'], state['communityCards'])
    hand_strength_pct = evaluator.get_five_card_rank_percentage(hand_strength)
    rounded_hand_strength = '{0:.1f}'.format(hand_strength_pct)
    pot = sum(state['player1Bets']) + sum(state['player2Bets'])

    return [((rounded_hand_strength, pot, action), 1.0)]    

# Return a single indicator of the (hand strength (rounded to 1 decimal place), pot, round #, action)
def handPotRoundsActionFeatureExtractor(state, action):
    hand_strength = evaluator.evaluate(state['player1Hand'], state['communityCards'])
    hand_strength_pct = evaluator.get_five_card_rank_percentage(hand_strength)
    rounded_hand_strength = '{0:.1f}'.format(hand_strength_pct)
    pot = sum(state['player1Bets']) + sum(state['player2Bets'])
    round_num = len(state['communityCards'])

    return [((rounded_hand_strength, pot, round_num, action), 1.0)]    

# print('Oracle vs. Random')
# utilities3 = []
# # Simulate oracle player against random player
# for i in xrange(N):
#     oracle_player = OraclePlayer()
#     random_player = RandomPlayer()

#     leducGame = Poker(hand_size=hand_size, num_rounds=num_rounds)
#     self.future_cards_for_oracle = leducGame.state['deck'].draw(2)
#     leducGame.state['deck'].putBack(self.future_cards_for_oracle)
#     while True:
#         if leducGame.isEnd():
#             #print('utility: {}'.format(leducGame.utility()))
#             utilities3.append(leducGame.utility())
#             break
#         #print('player: {}'.format(leducGame.player()))
#         #print('legal legalActions: {}'.format(leducGame.legalActions()))
#         if leducGame.player() == 'Player1':
#             action = oracle_player.getAction(leducGame)
#         elif leducGame.player() == 'Player2':
#             action = random_player.getAction(leducGame)
#         else:
#             action = 'draw_card'
        
#         # print('action take: {}'.format(action))
#         leducGame.successor(leducGame.state, action)
#     if i % 1000 == 0:
#         print("************game:{}***************".format(i))

# print('avg utility: {}'.format(sum(utilities3)*1.0/len(utilities3)))


# baseline_player = BaselinePlayer()
# random_player = RandomPlayer()
# totalRewards = simulate(baseline_player, random_player, numTrials=1000)

# print('avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))

# print('Random vs. Random')
# random_player = RandomPlayer()
# totalRewards = simulate(random_player, random_player, numTrials=5000)

# print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
# print('==============')

# print('Baseline vs. Random')
# baseline_player = BaselinePlayer()
# random_player = RandomPlayer()
# totalRewards = simulate(baseline_player, random_player, numTrials=5000)

# print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
# print('==============')

#-------------------Trainning-------------------#
print('=========================')
print('Hand Action RL vs. Random')
print('=========================')
hand_action_rl_player = QLearningAlgorithm(legalActions, handActionFeatureExtractor, explorationProb=0.2)
random_player = RandomPlayer()
totalRewards = simulate(hand_action_rl_player, random_player, numTrials=50000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')
#-------------------Evaluation-------------------#
hand_action_rl_player.explorationProb = 0.0
totalRewards = simulate(hand_action_rl_player, random_player, numTrials=10000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')

# print('Weights Learned:')
# weights =  sorted([(k, v) for k, v in hand_action_rl_player.weights.items()], key=lambda x: x[1])

# for k, v in weights:
#     if v != 0:
#         print('{}: {:.2f}'.format(k, v))

#-------------------Trainning-------------------#
print('=============================')
print('Hand Pot Action RL vs. Random')
print('=============================')
hand_pot_action_rl_player = QLearningAlgorithm(legalActions, handPotActionFeatureExtractor, explorationProb=0.2)
random_player = RandomPlayer()

totalRewards = simulate(hand_pot_action_rl_player, random_player, numTrials=50000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')
#-------------------Evaluation-------------------#
hand_pot_action_rl_player.explorationProb = 0.0
totalRewards = simulate(hand_pot_action_rl_player, random_player, numTrials=10000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')

# print('Weights Learned:')
# weights =  sorted([(k, v) for k, v in hand_pot_action_rl_player.weights.items()], key=lambda x: x[1])

# for k, v in weights:
#     if v != 0:
#         print('{}: {:.2f}'.format(k, v))

#-------------------Trainning-------------------#
print('========================================')
print('Hand Pot Action Num Rounds RL vs. Random')
print('========================================')
hand_pot_rounds_action_rl_player = QLearningAlgorithm(legalActions, handPotRoundsActionFeatureExtractor, explorationProb=0.2)
random_player = RandomPlayer()

totalRewards = simulate(hand_pot_rounds_action_rl_player, random_player, numTrials=50000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')
#-------------------Evaluation-------------------#
hand_pot_rounds_action_rl_player.explorationProb = 0.0
totalRewards = simulate(hand_pot_rounds_action_rl_player, random_player, numTrials=10000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')

# print('Weights Learned:')
# weights =  sorted([(k, v) for k, v in hand_pot_rounds_action_rl_player.weights.items()], key=lambda x: x[1])

# for k, v in weights:
#     if v != 0:
#         print('{}: {:.2f}'.format(k, v))

#-------------------Trainning-------------------#
print('==========================================')
print('Hand Pot Action Num Rounds RL vs. Baseline')
print('==========================================')
hand_pot_rounds_action_rl_player = QLearningAlgorithm(legalActions, handPotRoundsActionFeatureExtractor, explorationProb=0.2)
baseline_player = BaselinePlayer()

totalRewards = simulate(hand_pot_rounds_action_rl_player, baseline_player, numTrials=50000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')
#-------------------Evaluation-------------------#
hand_pot_rounds_action_rl_player.explorationProb = 0.0
totalRewards = simulate(hand_pot_rounds_action_rl_player, baseline_player, numTrials=10000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')

# print('Weights Learned:')
# weights =  sorted([(k, v) for k, v in hand_pot_rounds_action_rl_player.weights.items()], key=lambda x: x[1])

# for k, v in weights:
#     if v != 0:
#         print('{}: {:.2f}'.format(k, v))


#-------------------Trainning-------------------#
print('==========================================')
print('Hand Pot Action Num Rounds RL vs. Oracle')
print('==========================================')
hand_pot_rounds_action_rl_player = QLearningAlgorithm(legalActions, handPotRoundsActionFeatureExtractor, explorationProb=0.2)
oracle_player = OraclePlayer()

totalRewards = simulate(hand_pot_rounds_action_rl_player, oracle_player, numTrials=1000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')
#-------------------Evaluation-------------------#
hand_pot_rounds_action_rl_player.explorationProb = 0.0
totalRewards = simulate(hand_pot_rounds_action_rl_player, oracle_player, numTrials=1000)
print('Final avg utility: {}'.format(sum(totalRewards)*1.0/len(totalRewards)))
print('==============')

print('Weights Learned:')
weights =  sorted([(k, v) for k, v in hand_pot_rounds_action_rl_player.weights.items()], key=lambda x: x[1])

for k, v in weights:
    if v != 0:
        print('{}: {:.2f}'.format(k, v))

