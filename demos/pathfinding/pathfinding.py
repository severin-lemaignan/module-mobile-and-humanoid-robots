import heapq
import math

MAZE0="""
S...
.#..
.##.
.#G.
"""


MAZE1="""
.....................##.......
.S...................##.......
.....................##.......
...##................##.......
...##........##......##.......
...##........##......#####....
...##........##......#####....
...##........##...............
...##........##...............
...##........##...............
...##........##...............
...##........##...............
.............##...............
.............##..........G....
.............##..............."""

iterations=0

class Maze:

    def __init__(self, maze):
        self.maze = maze.strip()
        self.size = (len(self.maze.split()[0]), len(self.maze.split()))
        self.maze = "".join(self.maze.split())
        self.start = (self.maze.find("S") % self.size[0], self.maze.find("S") // self.size[0])
        self.goal = (self.maze.find("G") % self.size[0], self.maze.find("G") // self.size[0])
    
    def isfree(self, x, y):
        if x < 0 or y < 0 or x >= self.size[0] or y >= self.size[1]:
            return False

        return self.maze[x + y * self.size[0]] != "#"

    def neighbours(self, node):
        
        x, y = node
        result = set()

        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if self.isfree(x+dx, y+dy):
                    result.add((x+dx, y+dy))
        result.discard((x,y))
        return result

    def weight(self, nodeA, nodeB):
        """ Constant weight all over the maze
        """
        return 1

    def __iter__(self):
        """Returns all the cells in the maze that are free
        """
        for node in [(x,y) for x in range(self.size[0]) 
                           for y in range(self.size[1]) 
                           if self.isfree(x,y)]:
            yield node

    def __str__(self):
        """Inserts a line break at the end of each maze row
        and returns the corresponding string.
        """
        return "\n".join([self.maze[i:i+self.size[0]] for i in range(0, len(self.maze), self.size[0])]) + "\n"

    def printpath(self, path):
        """ Overlays 'o' on top of the maze, at the coordinates given in the
        path, and prints the result.
        """
        printout = list(self.maze)
        for x,y in path:
            printout[x + y * self.size[0]] = 'o'

        print("\n".join(["".join(printout[i:i+self.size[0]]) for i in range(0, len(printout), self.size[0])]) + "\n")



class PriorityQueue:
    """ Simple priority queue: get_cheapest always returns the node with the
    lowest 'priority' value.

    Implementation taken from https://www.redblobgames.com/pathfinding/a-star/implementation.html
    """
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get_cheapest(self):
        return heapq.heappop(self.elements)[1]


def dijkstra(graph):
  global iterations

  cost_to = {} # maps nodes to cost to 'start'
  come_from = {} # needed to reconstruct shortest path

  for node in graph:
    cost_to[node] = math.inf # initial cost from 'start' to 'node'. Requires Python >=3.5!

  cost_to[graph.start] = 0

  frontier = PriorityQueue()
  frontier.put(graph.start, 0)

  while not frontier.empty():
    u = frontier.get_cheapest() # remove best node

    if u == graph.goal:
       break

    for v in graph.neighbours(u): # iterate over nodes connected to u
        if cost_to[u] + graph.weight(u, v) < cost_to[v]: # new shorter path to v!
            cost_to[v] = cost_to[u] + graph.weight(u, v)
            frontier.put(v, cost_to[v])
            come_from[v] = u
            iterations+=1

        #path = getpath(v, come_from)
        #maze.printpath(path)
        #input()


  return cost_to, come_from

def getpath(goal, come_from):
    path = []
    node = goal
    while node in come_from:
        path = [node] + path # append at the front of our path
        node = come_from[node]

    return path


if __name__=="__main__":

    maze = Maze(MAZE1)
    
    print(maze)
    input()

    cost_to, come_from = dijkstra(maze)
    path = getpath(maze.goal, come_from)

    maze.printpath(path)

    print("%d iterations" % iterations)
