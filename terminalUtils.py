import numpy as np

box = {
    "reset" : '\033[0m',
    "black" : '\033[40m  \033[0m',
    "red" : '\033[41m  \033[0m',
    "green" : '\033[42m  \033[0m',
    "orange" : '\033[43m  \033[0m',
    "blue" : '\033[44m  \033[0m',
    "purple" : '\033[45m  \033[0m',
    "cyan" : '\033[46m  \033[0m',
    "white" : '\033[47m  \033[0m'
}

for key, value in box.items():
    print(key, value)

class colors:
    grid = "cyan" # initialize values to this one
    bg = "blue"
    wall = "orange"
    highlight = "purple"
    black = "black"
    white = "white"

def printGameState(state, highlight = []):
    printWalls(state.agents[1,2])
    printBoard(state, highlight)
    printWalls(state.agents[0,2])

def printWalls(walls):
    # height = 7
    height = 4
    b = [ [colors.grid for y in range(37)] for x in range(height)]
    #### blocks ####
    for row in range(height):
        for col in range(0, 36, 4):
            for i in range(1, 4):
                b[row][col+i] = colors.bg

    #### wallls ####
    for row in range(height):
        for col in range(0, 4*walls, 4):
            b[row][col] = colors.wall

    for row, arrRow in enumerate(b):
        for col, arrCol in enumerate(arrRow):
            print(box[arrCol], end="")
        print()
        
# for i, b in enumerate(box):
    # print(i, b)

## possibleMoves has been deprecated for hte more general highlight
def printBoard(state, highlight = []):
    # b for board
    b = [ [colors.grid for y in range(37)] for x in range(37)]

    #### blocks ####
    for row in range(0, 36, 4):
        for col in range(0, 36, 4):
            b[row+1][col+1] = colors.bg
            b[row+1][col+2] = colors.bg
            b[row+1][col+3] = colors.bg
            b[row+2][col+1] = colors.bg
            b[row+2][col+2] = colors.bg
            b[row+2][col+3] = colors.bg
            b[row+3][col+1] = colors.bg
            b[row+3][col+2] = colors.bg
            b[row+3][col+3] = colors.bg

    #### walls ####
    ## wall length is 7
    ## vertical wall goes 7 down
    for row, arrRow in enumerate(state.walls[0]):
        for col, arrCol in enumerate(arrRow):
            if arrCol:
                for i in range(7):
                    b[(row)*4+1+i][(col+1)*4] = colors.wall

    # for node in state.shortestPath():
        # b[node[0]*4+2, node[1]*4+2] = colors.possible

    #### highlighted blocks ####
    for move in highlight:
        b[move[0]*4+2][move[1]*4+2] = colors.highlight

    #### agents ####
    b[state.agents[0, 0]*4+2][state.agents[0, 1]*4+2] = colors.black
    b[state.agents[1, 0]*4+2][state.agents[1, 1]*4+2] = colors.white

    #### possible moves ####
    # if possibleMoves:
        # for move in state.possibleMoves():
            # b[move[0]*4+2][move[1]*4+2] = colors.possible

    ## horizontal wall goes 7 right
    for row, arrRow in enumerate(state.walls[1]):
        for col, arrCol in enumerate(arrRow):
            if arrCol:
                for i in range(7):
                    b[(row+1)*4][(col)*4+1+i] = colors.wall
    for row, arrRow in enumerate(b):
        for col, arrCol in enumerate(arrRow):
            if row % 4 == 1 and col % 4 == 1:
                print(str(row//4)+str(col//4), end="")
            else:
                print(box[arrCol], end="")
        print()

