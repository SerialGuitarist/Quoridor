import numpy as np
import time

from gameState import GameState
from agent import *
from minimaxProcessing import MinimaxProcessing
from node import Node

# class box:
    # reset = '\033[0m'
    # black = '\033[40m  \033[0m'
    # red = '\033[41m  \033[0m'
    # green = '\033[42m  \033[0m'
    # orange = '\033[43m  \033[0m'
    # blue = '\033[44m  \033[0m'
    # purple = '\033[45m  \033[0m'
    # cyan = '\033[46m  \033[0m'
    # white = '\033[47m  \033[0m'
# 
# print(box.black)
# print(box.red) # wall
# print(box.green) # black
# print(box.orange) # empty wall
# print(box.blue) # possible
# print(box.purple)
# print(box.cyan) # bg
# print(box.white) # white

# class box:
    # wall = '\033[41m  \033[0m'
    # wallbg = '\033[43m  \033[0m'
    # possible = '\033[44m  \033[0m'
    # bg = '\033[46m  \033[0m'
    # black = '\033[42m  \033[0m'
    # white = '\033[47m  \033[0m'

box = ['\033[45m  \033[0m',
       '\033[46m  \033[0m',
       '\033[41m  \033[0m',
       '\033[43m  \033[0m',
       '\033[44m  \033[0m',
       '\033[42m  \033[0m',
       '\033[47m  \033[0m']

class colors:
    grid = 3
    bg = 1
    wall = 2
    wallbg = 0
    possible = 6
    black = 5
    white = 4

def printGameState(state, possibleMoves = False):
    printWalls(state.agents[1,2])
    printBoard(state, possibleMoves)
    printWalls(state.agents[0,2])

def printWalls(walls):
    b = np.zeros((7, 37), dtype=int)
    #### blocks ####
    for row in range(7):
        for col in range(0, 36, 4):
            for i in range(1, 4):
                b[row, col+i] = colors.bg

    #### wallls ####
    for row in range(7):
        for col in range(0, 4*walls, 4):
            b[row, col] = colors.wall

    for row, arrRow in enumerate(b):
        for col, arrCol in enumerate(arrRow):
            print(box[arrCol], end="")
        print()
        

def printBoard(state, possibleMoves = False):
    # b for board
    b = np.zeros((37, 37), dtype=int)

    #### blocks ####
    for row in range(0, 36, 4):
        for col in range(0, 36, 4):
            b[row+1, col+1] = colors.bg
            b[row+1, col+2] = colors.bg
            b[row+1, col+3] = colors.bg
            b[row+2, col+1] = colors.bg
            b[row+2, col+2] = colors.bg
            b[row+2, col+3] = colors.bg
            b[row+3, col+1] = colors.bg
            b[row+3, col+2] = colors.bg
            b[row+3, col+3] = colors.bg

    #### walls ####
    ## wall length is 7
    ## vertical wall goes 7 down
    for row, arrRow in enumerate(state.walls[0]):
        for col, arrCol in enumerate(arrRow):
            if arrCol:
                for i in range(7):
                    b[(row)*4+1+i, (col+1)*4] = colors.wall

    # for node in state.shortestPath():
        # b[node[0]*4+2, node[1]*4+2] = colors.possible

    #### agents ####
    b[state.agents[0, 0]*4+2, state.agents[0, 1]*4+2] = colors.black
    b[state.agents[1, 0]*4+2, state.agents[1, 1]*4+2] = colors.white

    # if startRow != None:
        # for node in state.shortestPathBetweenNodes(startRow, startCol, endRow, endCol):
            # # b[move.agents[state.turn, 0]*4+2, move.agents[state.turn, 1]*4+2] = colors.possible
            # b[node[0]*4+2, node[1]*4+2] = colors.possible

    #### possible moves ####
    if possibleMoves:
        for move in state.possibleMoves():
            # b[move.agents[state.turn, 0]*4+2, move.agents[state.turn, 1]*4+2] = colors.possible
            b[move[0]*4+2, move[1]*4+2] = colors.possible
            # print("daaaaaaaaaaaaaaaaaaaa")

    ## horizontal wall goes 7 right
    for row, arrRow in enumerate(state.walls[1]):
        for col, arrCol in enumerate(arrRow):
            if arrCol:
                for i in range(7):
                    b[(row+1)*4, (col)*4+1+i] = colors.wall
    for row, arrRow in enumerate(b):
        for col, arrCol in enumerate(arrRow):
            if row % 4 == 1 and col % 4 == 1:
                print(str(row//4)+str(col//4), end="")
            else:
                print(box[arrCol], end="")
        print()

state = GameState.newGame()
# white = Random(delay=0.5)
# black = Random(delay=0.5)
# white = MinimaxProcessing()
# black = MinimaxProcessing()
# black = MinimaxProcessing(processCount=12, depth=2, distance=3)
white = Human()
black = Human()
# black = Random(delay=0.5)
# black = Minimax()

while True:
    # if isinstance(white, Human):
    printGameState(state, True)
    state = white.shoot(state)
    if state.checkVictory() >= 0:
        break
    # if isinstance(black, Human):
    printGameState(state, True)
    # time.sleep(0.5)
    state = black.shoot(state)
    if state.checkVictory() >= 0:
        break

printGameState(state)

# 
# def minimaxVsMinimax():
    # state = GameState.newGame()
    # agent = Minimax()
    # while True:
        # printGameState(state, True)
        # state = agent.shoot(state)
        # if state.checkVictory() >= 0:
            # break
    # printGameState(state, True)
# 
# import cProfile
# cProfile.run('minimaxVsMinimax()')
# 
