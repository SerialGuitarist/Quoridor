import numpy as np
import re
import random
import time

from gameState import GameState

class Agent:
    ## white is a boolean denoting whether the agent is white or not
    # def __init__(self, white):
        # self.white = white
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
    def shoot(self, state):
        time.sleep(0.5)
        if state.agents[state.turn, 2] > 0:
            if random.getrandbits(1):
                return random.choice(state.moveStates())
            else:
                return random.choice(state.wallStates())
        return random.choice(state.moveStates())

