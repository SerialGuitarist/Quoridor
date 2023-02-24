import numpy as np

## meant to be used in the various A* derivatives
class Node:
    def __init__(self, row, col, fromStart, toEnd, parent = None):
        self.row = row
        self.col = col
        self.fromStart = fromStart                      ## aka gScore
        self.toEnd = toEnd                              ## aka hScore
        self.parent = parent

    ## so I can use heaps to pick the lowest fCost for the performance
    def __lt__(self, node):
        return self.fromStart + self.toEnd < node.fromStart + node.toEnd
