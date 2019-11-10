from deuces import Deck
from deuces import Card

class Poker:
	'''
	State (dict):
	  currentPlayer (str): Player1, Player2, Dealer (which agent is going to take an action)
	  player1Hand (list): card1, card2
	  player2Hand (list): card1, card2
	  communityCards (list): card1, card2, ...
	  deck: current deck
	  player1Bets (list): bet1, bet2 (these are additions to the pot)
	  player2Bets (list): bet1, bet2 (these are additions to the pot)
	  player1Stack (int): player1's stack
	  player2Stack (int): player2's stack
	  player1Fold (bool): if player1 folds
	  player2Fold (bool): if player2 folds
	'''

	def __init__(self, hand_size=2, player1Stack=100, player2Stack=100):
		self.state = {}
		self.state['deck'] = Deck()
		self.state['currentPlayer'] = 'Player1'
		self.state['player1Hand'] = [self.state['deck'].draw(1) for i in range(hand_size)]
		self.state['player2Hand'] = [self.state['deck'].draw(1) for i in range(hand_size)]
		self.state['communityCards'] = []
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
		print('communityCards')
		Card.print_pretty_cards(self.state['communityCards'])
		print('player1Bets: {}'.format(self.state['player1Bets']))
		print('player2Bets: {}'.format(self.state['player2Bets']))
		print('player1Stack: {}'.format(self.state['player1Stack']))
		print('player2Stack: {}'.format(self.state['player1Stack']))
		print('player1Fold: {}'.format(self.state['player1Fold']))
		print('player2Fold: {}'.format(self.state['player2Fold']))


leducGame = Poker(hand_size=1)
leducGame.printState()
