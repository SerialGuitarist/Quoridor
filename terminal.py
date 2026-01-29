import numpy as np
import time

from gameState import GameState
from agent import *
from minimaxProcessing import MinimaxProcessing
from fast_minimax import MinimaxFast
from node import Node
from reinforcementAgent import ScoringAgent
from whiteAgent import WhiteAgent

import json

from terminalUtils import *

def compete(agentA, agentB, n=10):
    print("White:", agentA, "- Black:", agentB)
    white = agentA
    black = agentB
    tally = [0, 0]
    for i in range(n):
        state = GameState.newGame()
        while True:
            state = white.shoot(state)
            if state.checkVictory() >= 0:
                break
            state = black.shoot(state)
            if state.checkVictory() >= 0:
                break
        tally[state.checkVictory()] += 1
    print("Final Tally:", tally)

    print("White:", agentB, "- Black:", agentA)
    white = agentB
    black = agentA
    tally = [0, 0]
    for i in range(n):
        state = GameState.newGame()
        while True:
            state = white.shoot(state)
            if state.checkVictory() >= 0:
                break
            state = black.shoot(state)
            if state.checkVictory() >= 0:
                break
        tally[state.checkVictory()] += 1
    print("Final Tally:", tally)

def play(white, black):
    state = GameState.newGame()
    while True:
        # if isinstance(white, Human):
        printGameState(state, highlight=state.shortestPath())
        # printGameState(state)
        state = white.shoot(state)
        # for next_state in state.possibleGameStates():
            # if (not next_state.hasValidPath(0)) or (not next_state.hasValidPath(1)):
                # print("Given the following state")
                # printGameState(state)
                # print("The engine claims this is a valid next step")
                # printGameState(next_state)
                # print(next_state.toSerial())
                # raise
        if state.checkVictory() >= 0:
            break
        # if isinstance(black, Human):
        # printGameState(state, highlight=state.shortestPath())
        printGameState(state)
        # time.sleep(0.5)
        state = black.shoot(state)
        # for next_state in state.possibleGameStates():
            # if (not next_state.hasValidPath(0)) or (not next_state.hasValidPath(1)):
                # print("Given the following state")
                # printGameState(state)
                # print("The engine claims this is a valid next step")
                # printGameState(next_state)
                # print(next_state.toSerial())
                # raise
        # if (not state.hasValidPath(0)) or (not state.hasValidPath(1)):
            # print(state.toSerial())
        if state.checkVictory() >= 0:
            break
    printGameState(state)


# white = Human()
# black = Human()
# white = Random(delay=0.1)
# black = Random(delay=0.5)
# white = MinimaxProcessing()
# black = MinimaxProcessing()
# black = MinimaxProcessing(processCount=12, depth=2, distance=3)
# black = Random(delay=0.5)
# black = Minimax()
# white = ScoringAgent()
# black = ScoringAgent()



# compete(Random(), Random())
# compete(ScoringAgent(), Random())
# play(ScoringAgent(tau=0.1, delay=0.1), ScoringAgent(tau=1))
# play(ScoringAgent(tau=1), ScoringAgent(tau=0.1, delay=0.1))
# play(Random(), ScoringAgent(tau=0.1, delay=0.2))
# play(ScoringAgent(tau=0.1, delay=0.2), Random())
# play(ScoringAgent(tau=0.4, delay=0.1), Random())
# play(ScoringAgent(delay=0.2), Random())
# play(Random(), ScoringAgent(delay=0.2, tau=0.001))
# play(MinimaxProcessing(depth=1), ScoringAgent(tau=0.01, delay=0.2))
# play(ScoringAgent(tau=0.01, delay=0.2), MinimaxProcessing(depth=1))
# play(Random(), WhiteAgent(tau=0.01, delay=0.5), showShortest=True)
# play(WhiteAgent(tau=0.01, delay=0.5), Random())
# play(Human(), Human())
# play(Random(delay=0.1), ScoringAgent(tau=10))
# play(ScoringAgent(tau=100), ScoringAgent(tau=10))
# play(ScoringAgent(), ScoringAgent())

# minimax = MinimaxFast(depth=2, wall_cap=12, time_ms=None)  # tune these
play(Minimax(), Minimax())

