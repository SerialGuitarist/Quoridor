import numpy as np
import re
import random
import time
import threading
from math import ceil
from multiprocessing import Pool

from gameState import GameState

class Agent:
    pass

class Human(Agent):
    ## returns a valid gamestate ##
    def shoot(self, state):
        # if state.turn != self.white:
            # raise Exception("Mismatching turns")
        print("Human player move: " + ("white" if state.turn else "black"))
        print("Format: [vhm][0-8][0-8]")
        command = input("Input: ")
        if not re.match(r'[vhm][0-9][0-9]', command):
            print("Not a valid command")
            ## i feel dirty doing this
            return self.shoot(state)

        act = command[0]
        row = int(command[1])
        col = int(command[2])

        if act == 'v' or act == 'h':
            if state.agents[state.turn, 2] == 0:
                print("Not enough walls")
                return self.shoot(state)
            if not state.checkWall(0 if act == 'v' else 1, row, col):
                print("Can't put wall there")
                return self.shoot(state)
        else:
            if not self.searchMove(row, col, state.possibleMoves()):
                print("Can't move there")
                return self.shoot(state)

        newState = state.copy()
        if act == 'v':
            newState.walls[0, row, col] = True
            newState.agents[newState.turn, 2] -= 1
        elif act == 'h':
            newState.walls[1, row, col] = True
            newState.agents[newState.turn, 2] -= 1
        else:
            newState.agents[newState.turn, 0] = row
            newState.agents[newState.turn, 1] = col

        newState.passTurn()
        return newState

    ## used to determine if the provided move is legal
    def searchMove(self, row, col, listOfMoves):
        for move in listOfMoves:
            if move[0] == row and move[1] == col:
                return True
        return False

class Random(Agent):
    def __init__(self, delay=0):
        self.delay = delay

    def shoot(self, state):
        time.sleep(self.delay)
        if state.agents[state.turn, 2] > 0:
            if random.getrandbits(1):
                return random.choice(state.moveStates())
            else:
                return random.choice(state.wallStates())
        return random.choice(state.moveStates())

class Minimax(Agent):
    def __init__(self, depth = 2, distance = None):
        self.depth = depth
        self.distance = distance

    def shoot(self, state):
        bestMove = None
        ## white is maximizing player
        if state.turn:
            ## maximizing
            bestScore = -np.inf
            children = state.possibleGameStates(distance=self.distance)
            for i, child in enumerate(children):
                print(f"Maximizing: child {i} / {len(children)}", end="\r")
                score = self.minimax(child, 1)
                if score > bestScore:
                    bestScore = score
                    bestMove = child
        else:
            ## minimizing
            bestScore = np.inf
            children = state.possibleGameStates(distance=self.distance)
            for i, child in enumerate(children):
                print(f"Minimizing: child {i} / {len(children)}", end="\r")
                score = self.minimax(child, 1)
                if score < bestScore:
                    bestScore = score
                    bestMove = child
        return bestMove
    
    def minimax(self, state, depth, alpha = -np.inf, beta = np.inf):
        if depth == self.depth:
            return self.score(state)
        bestScore = None
        ## white is maximizing player
        if state.turn:
            ## maximizing
            bestScore = -np.inf
            for child in state.possibleGameStates():
                score = self.minimax(child, depth+1, alpha, beta)
                bestScore = max(score, bestScore)
                alpha = max(alpha, bestScore)
                if beta <= alpha:
                    break
        else:
            ## minimizing
            bestScore = np.inf
            for child in state.possibleGameStates():
                score = self.minimax(child, depth+1, alpha, beta)
                bestScore = min(score, bestScore)
                beta = min(beta, bestScore)
                if beta <= alpha:
                    break
        return bestScore

    def score(self, state):
        return len(state.shortestPath(0)) - len(state.shortestPath(1))

class MinimaxThreading(Agent):
    ## apparently the Global Interpreter Lock doens't let me do this
    ## so this is actually slower than the normal Minimax
    ## look below for the MinimaxProcessing for actual parallelization
    def __init__(self, depth = 2, threadCount = 128, delay = 0):
        self.depth = depth
        self.threadCount = threadCount
        self.delay = delay

    class MinimaxThread(threading.Thread):
        def __init__(self, states, maximizing, minimax):
            threading.Thread.__init__(self)
            self.bestMove = None
            self.bestScore = None
            self.states = states
            self.maximizing = maximizing
            self.minimax = minimax
        
        def run(self):
            if self.maximizing:
                self.bestScore = -np.inf
                for i, child in enumerate(self.states):
                    print(f"Maximizing {i} / {len(self.states)}", end='\r')
                    score = self.minimax.minimax(child, 1, alpha=self.bestScore)
                    if score > self.bestScore:
                        self.bestScore = score
                        self.bestMove = child
            else:
                self.bestScore = np.inf
                for i, child in enumerate(self.states):
                    print(f"Minimizing {i} / {len(self.states)}", end='\r')
                    score = self.minimax.minimax(child, 1, beta=self.bestScore)
                    if score < self.bestScore:
                        self.bestScore = score
                        self.bestMove = child


    def shoot(self, state):
        time.sleep(self.delay)
        bestMove = None
        states = state.possibleGameStates()
        n = ceil(len(states) / self.threadCount)
        threads = [ self.MinimaxThread(states[i: i+n], state.turn, self) for i in range(0, self.threadCount*n, n) ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        best = max(threads, key=lambda x: x.bestScore) if state.turn else min(threads, key=lambda x: x.bestScore)
        return best.bestMove

    
    def minimax(self, state, depth, alpha = -np.inf, beta = np.inf):
        if depth == self.depth:
            return self.score(state)
        bestScore = None
        ## white is maximizing player
        if state.turn:
            ## maximizing
            bestScore = -np.inf
            for child in state.possibleGameStates():
                score = self.minimax(child, depth+1, alpha, beta)
                bestScore = max(score, bestScore)
                alpha = max(alpha, bestScore)
                if beta <= alpha:
                    break
        else:
            ## minimizing
            bestScore = np.inf
            for child in state.possibleGameStates():
                score = self.minimax(child, depth+1, alpha, beta)
                bestScore = min(score, bestScore)
                beta = min(beta, bestScore)
                if beta <= alpha:
                    break
        return bestScore

    def score(self, state):
        return len(state.shortestPath(0)) - len(state.shortestPath(1))


