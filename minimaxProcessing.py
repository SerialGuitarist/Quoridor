import numpy as np
import time
from multiprocessing import Pool

from gameState import GameState
from agent import Agent
from math import ceil
    

class MinimaxProcessing(Agent):
    ## apparently the Global Interpreter Lock doens't let me do this
    ## so this is actually slower than the normal Minimax
    ## look below for the MinimaxProcessing for actual parallelization
    def __init__(self, depth = 2, processCount = 8, delay = 0, distance=3):
        self.depth = depth
        self.processCount = processCount
        self.delay = delay
        self.distance = distance

    def shoot(self, state):
        time.sleep(self.delay)
        states = state.possibleGameStates(distance=self.distance)
        ## number of partition
        k = min(self.processCount, len(states))
        ## size of each partition
        n = ceil(len(states) / k)
        partitions = [ states[i: i+n] for i in range(0, len(states), n) ]
        # print(partitions)
        ## multi processing magic here
        ## take that, global interpreter lock!
        with Pool(self.processCount) as p:
            try:
                bests = p.map(self.run, partitions)
                best = max(bests, key=lambda x: x[1]) if state.turn else min(bests, key=lambda x: x[1])
                return best[0]
            except:
                print(f"k: {k}")
                print(f"n: {n}")
                print(f"N: {len(states)}")
                print(partitions)
                raise Exception("psyche")

    def run(self, states):
        bestScore = None
        bestMove = None
        if (1-states[0].turn):
            bestScore = -np.inf
            for i, child in enumerate(states):
                print(f"Maximizing {i} / {len(states)}", end='\r')
                score = self.minimax(child, 1, alpha=bestScore)
                if score > bestScore:
                    bestScore = score
                    bestMove = child
        else:
            bestScore = np.inf
            for i, child in enumerate(states):
                print(f"Minimizing {i} / {len(states)}", end='\r')
                score = self.minimax(child, 1, beta=bestScore)
                if score < bestScore:
                    bestScore = score
                    bestMove = child
        return (bestMove, bestScore)
    
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

