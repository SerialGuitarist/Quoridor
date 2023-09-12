import numpy as np
import heapq
from collections import deque

from node import Node

class GameState:
    ## walls is (2,8,8) vector where first 8x8 is vertical walls and second 8x8 is horizontal walls
    ## agents is (2, 3) vector
        ## agents[0] is black
        ## angets[1] is white
        ## agents[1][0] is white y coord (row)
        ## agents[1][1] is white x coord (col)
        ## agents[1][2] is walls white has left
        ## and vice versa
    def __init__(self, walls, agents, turn = 1):
        self.walls = walls
        self.agents = agents
        self.turn = turn ## is it white's turn?

    ## returns np.array of the possible game states reachable
    ## with a single move from this gamestate
    def possibleStates(self):
        return np.array([])

    def __eq__(self, state):
        return np.array_equal(self.walls, state.walls) and np.array_equal(self.agents, state.agents) and self.turn == state.turn

    def copy(self):
        return GameState(self.walls.copy(), self.agents.copy(), self.turn)

    @classmethod
    def newGame(state):
        return GameState(np.full((2, 8, 8), False), np.array([[8, 4, 10], [0, 4, 10]]))

    def passTurn(self):
        self.turn = 1 - self.turn

    ## some helpers for the pathfinding
    ## start is np.array([row, col])
    # def checkLeft(self, start):
    def checkUp(self, row, col):
            ## can't be at the top row
            ## not blocked by wall above
            ## not blocked by wall left above
        return row != 0 and \
            (not self.walls[1, row - 1, col] if col < 8 else True) and \
            (not self.walls[1, row - 1, col - 1] if col > 0 else True)

    def checkDown(self, row, col):
            ## can't be at the top row
            ## not blocked by wall right below
            ## not blocked by wall left above
        return row != 8 and \
            (not self.walls[1, row, col] if col < 8 else True) and \
            (not self.walls[1, row, col-1] if col > 0 else True)

    def checkLeft(self, row, col):
            ## can't be at the leftmost col
            ## not blocked by wall right to left
            ## not blocked by wall left above
        return col != 0 and \
            (not self.walls[0, row, col - 1] if row < 8 else True) and \
            (not self.walls[0, row - 1, col - 1] if row > 0 else True)

    def checkRight(self, row, col):
            ## can't be at the rightmost col
            ## not blocked by wall right to right
            ## not blocked by wall right and above
        return col != 8 and \
            (not self.walls[0, row, col] if row < 8 else True) and \
            (not self.walls[0, row - 1, col] if row > 0 else True)


    ## returns a list of possible coordinates for the current player to move
    ## returns list of [row, col]
    def possibleMoves(self):
        turn = self.turn
        row = self.agents[turn, 0]
        col = self.agents[turn, 1]
        oppRow = self.agents[1-turn, 0]
        oppCol = self.agents[1-turn, 1]
        output = []
        # print(row, col)
        # print(oppRow, oppCol)

        #### up ####
        if  self.checkUp(row, col):
            # blocked by opponent
            if oppCol == col and oppRow == row - 1:
                output += self.possibleMovesOver(0);
            else:
                output.append([row-1, col])

        #### down ####
        if  self.checkDown(row, col):  
            # blocked by opponent
            if oppCol == col and oppRow == row + 1:
                output += self.possibleMovesOver(1);
            else:
                output.append([row+1, col])

        #### left ####
        if  self.checkLeft(row, col):     
            # blocked by opponent
            if oppCol == col - 1 and oppRow == row:
                output += self.possibleMovesOver(2);
            else:
                output.append([row, col-1])

        #### right ####
        if  self.checkRight(row, col): \
            # blocked by opponent
            if oppCol == col + 1 and oppRow == row:
                output += self.possibleMovesOver(3);
            else:
                output.append([row, col+1])
        return output;

    ## helper function for possibeOver
    ## in case the two players are right next to each other
    ## and need to jump over one another
    def possibleMovesOver(self, pos):
        # pos 0 == up
        # pos 1 == down
        # pos 2 == left
        # pos 3 == right
        turn = 1 - self.turn
        row = self.agents[turn, 0]
        col = self.agents[turn, 1]
        output = []

        #### up ####
        if  pos != 1 and self.checkUp(row, col):
            output.append([row-1, col])

        #### down ####
        if  pos != 0 and self.checkDown(row, col):  
            output.append([row+1, col])

        #### left ####
        if  pos != 3 and self.checkLeft(row, col):     
            output.append([row, col-1])

        #### right ####
        if  pos != 2 and self.checkRight(row, col):
            output.append([row, col+1])
        return output;

    ## returns a list of np.array([row, col]) for nodes accessible from here
    ## implemented seperately from possibleMoves because doesn't need to account
    ## for jumping over the opponent here
    def possibleNodes(self, row, col):
        output = []
        if self.checkUp(row, col):
            output.append(np.array([row-1, col]))
        if self.checkDown(row, col):
            output.append(np.array([row+1, col]))
        if self.checkLeft(row, col):
            output.append(np.array([row, col-1]))
        if self.checkRight(row, col):
            output.append(np.array([row, col+1]))
        return output

    ## returns a list of [row, col] for the shortest path
    ## including the start and end nodes
    ## returns empyy array if no path is found
    def shortestPathBetweenNodes(self, startRow, startCol, endRow, endCol):
        toCheck = []
        ## keeps track of both whether we've checked the node
        ## and the lowest gScore to get there
        lowest = []
        for i in range(9):
            temp = []
            for j in range(9):
                temp.append(None)
            lowest.append(temp)

        heapq.heapify(toCheck)
        heapq.heappush(toCheck,Node(startRow, startCol, 0, abs(endRow-startRow)+abs(endCol-startCol)))

        ## for the edge case where the start node and end node is the same
        lowest[startRow][startCol] = toCheck[0]

        while toCheck:
            current = heapq.heappop(toCheck)
            if current.row == endRow and current.col == endCol:
                ## found our target
                path = [lowest[endRow][endCol]]
                while path[-1].parent:
                    path.append(path[-1].parent)
                
                return [[node.row, node.col] for node in path[::-1]]

            for neighbor in self.possibleNodes(current.row, current.col):
                node = Node(neighbor[0], neighbor[1], current.fromStart+1, abs(endRow-neighbor[0])+abs(endCol-neighbor[1]), current)
                if lowest[node.row][node.col] == None:
                    ## then we've never seen this before
                    lowest[node.row][node.col] = node
                    heapq.heappush(toCheck, node)
                elif lowest[node.row][node.col].fromStart > node.fromStart:
                    ## then we've found a beter path to reach here
                    lowest[node.row][node.col] = node                 

        return []

    ## returns list of [row, col] for the shortest path to victory for current player
    def shortestPath(self, turn = None):
        turn = self.turn if turn == None else turn
        toCheck = []
        startRow = self.agents[turn, 0]
        startCol = self.agents[turn, 1]
        endRow = 8 if turn else 0
        ## keeps track of both whether we've checked the node
        ## and the lowest gScore to get there
        lowest = []
        for i in range(9):
            temp = []
            for j in range(9):
                temp.append(None)
            lowest.append(temp)

        heapq.heapify(toCheck)
        heapq.heappush(toCheck,Node(startRow, startCol, 0, abs(endRow-startRow)))

        ## for the edge case where the start node and end node is the same
        lowest[startRow][startCol] = toCheck[0]

        while toCheck:
            current = heapq.heappop(toCheck)
            if current.row == endRow:
                ## found our target
                path = [lowest[current.row][current.col]]
                while path[-1].parent:
                    path.append(path[-1].parent)
                
                return [[node.row, node.col] for node in path[::-1]]

            for neighbor in self.possibleNodes(current.row, current.col):
                node = Node(neighbor[0], neighbor[1], current.fromStart+1, abs(endRow-neighbor[0]), current)
                if lowest[node.row][node.col] == None:
                    ## then we've never seen this before
                    lowest[node.row][node.col] = node
                    heapq.heappush(toCheck, node)
                elif lowest[node.row][node.col].fromStart > node.fromStart:
                    ## then we've found a beter path to reach here
                    lowest[node.row][node.col] = node                 

        return []

    ## does the current player have a valid path to their destination?
    def hasValidPath(self, turn = None):
        turn = self.turn if turn == None else turn
        queue = deque()
        targetRow = 8 if self.turn else 0
        queue.append((self.agents[turn, 0], self.agents[turn, 1]))
        checkedNodes = np.full((9,9), False)
        try:
            while True:
                node = queue.popleft()
                checkedNodes[node[0], node[1]] = True
                if node[0] == targetRow:
                    return True
                if self.checkUp(node[0], node[1]) and not checkedNodes[node[0]-1, node[1]]:
                    queue.append((node[0]-1, node[1]))
                if self.checkDown(node[0], node[1]) and not checkedNodes[node[0]+1, node[1]]:
                    queue.append((node[0]+1, node[1]))
                if self.checkLeft(node[0], node[1]) and not checkedNodes[node[0], node[1]-1]:
                    queue.append((node[0], node[1]-1))
                if self.checkRight(node[0], node[1]) and not checkedNodes[node[0], node[1]+1]:
                    queue.append((node[0], node[1]+1))
        except:
            return False


    ## Deprecated
    ## new implementatin through BFS is O(n^2) instead of O(n^3) of A*
    # def hasValidPath(self, turn = None):
        # turn = self.turn if turn == None else turn
        # # print(f"===========TURN: {turn}")
        # # print(self.shortestPath(turn))
        # return len(self.shortestPath(turn)) > 0

    ## can you put a wall there?
    def checkWall(self, orientation, row, col):
        ## orientation == 0 => vertical
        ## orientation == 1 => horizontal
        ## above is same as how it's stored in self.walls

        ## blocked by a wall there or its hor/ver counterpart
        # print(orientation, row, col)
        if self.walls[orientation, row, col] or self.walls[1 - orientation, row, col]:
            return False

        if orientation:
            ## horizontal
            ## blocked by next wall over
            if col < 7 and self.walls[1, row, col+1]:
                return False
            ## blocked by previous wall over
            if col > 0 and self.walls[1, row, col-1]:
                return False
        else:
            ## vertical
            ## blocked by next wall over
            if row < 7 and self.walls[0, row+1, col]:
                return False
            ## blocked by previous wall over
            if row > 0 and self.walls[0, row-1, col]:
                return False

        ## if no walls are blocking, try putting it there and see if
        ## blocks the path of either players
        self.walls[orientation, row, col] = True
        output = self.hasValidPath(0) and self.hasValidPath(1)
        self.walls[orientation, row, col] = False
        return output

    ## -1 if no one has won
    ## 0 if black won
    ## 1 if white won
    def checkVictory(self):
        if self.agents[0, 0] == 0:
            return 0
        if self.agents[1, 0] == 8:
            return 1
        return -1

    ## returns list of [orientation, row, col] of possible places a wall can be placed in
    ## giving a natural number value to distance only considers putting walls 
    ## within that distance from an existing wall or either player
    def possibleWalls(self, distance = None):
        output = []
        if distance == None:
            for orientation in [0, 1]:
                for row in range(8):
                    for col in range(8):
                        if self.checkWall(orientation, row, col):
                            output.append([orientation, row, col])
        else:
            pointsOfInterest = [(self.agents[0, 0], self.agents[0, 1]), (self.agents[1, 0], self.agents[1, 1])]
            for row in range(8):
                for col in range(8):
                    if self.walls[0, row, col] or self.walls[1, row, col]:
                        pointsOfInterest.append((row, col))
            # print(pointsOfInterest)
            for orientation in [0, 1]:
                for row in range(8):
                    for col in range(8):
                        for point in pointsOfInterest:
                            if abs(point[0]-row)+abs(point[1]-col) <= distance and self.checkWall(orientation, row, col):
                                output.append([orientation, row, col])
                                break

        return output

    ## useful to have the following two separetely
    def moveStates(self):
        output = []
        for move in self.possibleMoves():
            state = self.copy()
            state.agents[state.turn, 0] = move[0]
            state.agents[state.turn, 1] = move[1]
            state.passTurn()
            output.append(state)
        return output
    
    def wallStates(self, distance = None):
        output = []
        if self.agents[self.turn, 2] > 0:
            for wall in self.possibleWalls(distance=distance):
                state = self.copy()
                state.walls[wall[0], wall[1], wall[2]] = True
                state.agents[state.turn, 2] -= 1
                state.passTurn()
                output.append(state)
        return output

    ## returns list of possible game states from here
    def possibleGameStates(self, distance=None):
        return self.moveStates() + self.wallStates(distance=distance)

