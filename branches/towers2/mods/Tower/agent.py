from OpenNero import *
from common import *
import Tower
from Tower.environment import TowerEnvironment
from Tower.constants import *

from heapq import heappush, heappop

def dfs_heuristic(r,c):
    return 0

def manhattan_heuristic(r,c):
    return (ROWS - r) + (COLS - c)

def get_action_index(move):
    if move in TowerEnvironment.MOVES:
        action = TowerEnvironment.MOVES.index(move)
        print 'Picking action', action, 'for move', move
        return action
    else:
        return None

class Cell:
    def __init__(self, h, r, c):
        self.h = h
        self.r = r
        self.c = c
    def __cmp__(self, other):
        return cmp(self.h, other.h)

class TowerAgent(AgentBrain):
    """
    An agent designed to solve Towers of Hanoi
    """
    def __init__(self):
        AgentBrain.__init__(self) # have to make this call

    def initilize(self,init_info):
        # Create new Agent
        self.action_info = init_info.actions
        return True
    
    def start(self, time, sensors):
        """
        return first action given the first observations
        """
        return self.action_info.random()

    def reset(self):
        pass

    def act(self, time, sensors, reward):
        """
        return an action given the reward for the previous action and the new observations
        """
        return self.action_info.random()

    def end(self, time, reward):
        """
        receive the reward for the last observation
        """
        print  "Final reward: %f, cumulative: %f" % (reward[0], self.fitness[0])
        return True

    def destroy(self):
        """
        called when the agent is done
        """
        return True

class RandomAgent(AgentBrain):
    """
    A uniform random baseline - a very simple agent
    """
    def __init__(self):
        AgentBrain.__init__(self) # have to make this call

    def initialize(self, init_info):
        """
        create a new agent
        """
        self.action_info = init_info.actions
        return True

    def start(self, time, sensors):
        """
        return first action given the first observations
        """
        return self.action_info.random()

    def reset(self):
        pass

    def act(self, time, sensors, reward):
        """
        return an action given the reward for the previous action and the new observations
        """
        return self.action_info.random()

    def end(self, time, reward):
        """
        receive the reward for the last observation
        """
        print  "Final reward: %f, cumulative: %f" % (reward[0], self.fitness[0])
        return True

    def destroy(self):
        """
        called when the agent is done
        """
        return True

class SearchAgent(AgentBrain):
    """ Base class for maze search agents """
    
    def __init__(self):
        """ constructor """
        AgentBrain.__init__(self)
    def highlight_path(self):
        """
        backtrack to highlight the path
        """
        # retrace the path
        node = (ROWS - 1, COLS - 1)
        while node in self.backpointers:
            self.mark_path(node[0],node[1])
            next_node = self.backpointers[node]
            del self.backpointers[node]
            node = next_node

class DFSSearchAgent(SearchAgent):
    """
    Depth first search implementation
    """
    def __init__(self):
        """
        A new Agent
        """
        # this line is crucial, otherwise the class is not recognized as an AgentBrainPtr by C++
        SearchAgent.__init__(self) 
        self.visited = set([])
        self.adjlist = {}
        self.parents = {}
        self.backpointers = {}

    def dfs_action(self, sensors):
        r = sensors[0]
        c = sensors[1]
        # if we have not been here before, build a list of other places we can go
        if (r,c) not in self.visited:
            tovisit = []
            for m, (dr,dc) in enumerate(TowerEnvironment.MOVES):
                r2, c2 = r+dr, c+dc
                if not sensors[2 + m]: # can we go that way?
                    if (r2,c2) not in self.visited:
                        tovisit.append( (r2,c2) )
                        self.parents[ (r2,c2) ] = (r,c)
            # remember the cells that are adjacent to this one
            self.adjlist[(r, c)] = tovisit
        # if we have been here before, check if we have other places to visit
        adjlist = self.adjlist[(r,c)]
        k = 0
        while k < len(adjlist) and adjlist[k] in self.visited:
            k += 1
        # if we don't have other neighbors to visit, back up
        if k == len(adjlist):
            current = self.parents[(r,c)]
        else: # otherwise visit the next place
            current = adjlist[k]
        self.visited.add((r,c)) # add this location to visited list
        Tower.module.getMod().mark_maze_blue(r, c) # mark it as blue on the maze
        v = self.constraints.get_instance() # make the action vector to return
        dr, dc = current[0] - r, current[1] - c # the move we want to make
        v[0] = get_action_index( (dr, dc) )
        # remember how to get back
        if (r+dr,c+dc) not in self.backpointers:
            self.backpointers[(r+dr, c+dc)] = (r,c)
        return v

    def initialize(self, init_info):
        self.constraints = init_info.actions
        return True

    def start(self, time, sensors):
        # interpret the sensors
        row = int(sensors[0])
        col = int(sensors[1])
        # return action
        return self.dfs_action(sensors)

    def reset(self):
        self.visited = set([])
        self.adjlist = {}
        self.parents = {}
        self.backpointers = {}

    def act(self, time, sensors, reward):
        # interpret the sensors
        row = int(sensors[0])
        col = int(sensors[1])
        # return action
        return self.dfs_action(sensors)

    def end(self, time, reward):
        print  "Final reward: %f, cumulative: %f" % (reward[0], self.fitness[0])
        self.highlight_path()
        self.reset()
        return True

    def destroy(self):
        return True
        
    def mark_path(self, r, c):
        Tower.module.getMod().mark_maze_white(r,c)

class AStarSearchAgent(SearchAgent):
    """
    Egocentric A* algorithm
    """
    def __init__(self):
        """
        A new Agent
        """
        # this line is crucial, otherwise the class is not recognized as an AgentBrainPtr by C++
        SearchAgent.__init__(self) 
        self.backpointers = {}
        self.reset()

    def reset(self):
        self.highlight_path()
        self.adjlist = {}
        self.parents = {}
        self.pq = [] # empty priority queue
        self.visited = set([]) # set of nodes we have visited
        self.enqueued = set([]) # set of things in the queue (superset of visited)
        self.backpointers = {} # a dictionary from nodes to their predecessors
        self.goal = None # we have no idea where to go at first
        self.heuristic = manhattan_heuristic # minimize the Manhattan distance

    def initialize(self, init_info):
        """
        A new soul
        """
        self.constraints = init_info.actions
        return True

    def get_next_step(self, r1, c1, r2, c2):
        """
        return the next step when trying to get from current r1,c1 to target r2,c2
        """
        back2 = [] # cells between origin and r2,c2
        r,c = r2,c2 # back track from target
        while (r,c) in self.backpointers:
            r,c = self.backpointers[(r,c)]
            if (r1,c1) == (r,c): # if we find starting point, we need to move forward
                return back2[-1] # return the last step
            back2.append((r,c))
        return self.backpointers[(r1,c1)]

    def get_action(self, r, c, sensors):
        """
        Given: 
         - some places we could go in our queue
         - some backtracking links on how we got there
        """
        if not self.goal: # first, figure out where we are trying to go
            cell = heappop(self.pq)
            h, r2, c2 = cell.h, cell.r, cell.c
            self.mark_target(r2,c2)
            self.goal = (r2, c2)
        # then, check if we can get there
        r2, c2 = self.goal
        dr, dc = r2 - r, c2 - c
        action = get_action_index((dr,dc))
        v = self.constraints.get_instance() # make the action vector to return
        # first, is the node reachable in one action?
        if action is not None and sensors[2 + action] == 0:
            v[0] = action # if yes, do that action!
        else:
            # if not, we have to figure out a path to get there from the backtracking dictionary
            (r2,c2) = self.get_next_step(r,c,r2,c2)
            dr, dc = r2 - r, c2 - c # how to get back there?
            v[0] = get_action_index((dr,dc)) # what action is that?
        return v # return the action

    def visit(self, row, col, sensors):
        """
        visit the node row, col and decide where we can go from there
        """
        if (row,col) not in self.visited:
            self.mark_visited(row,col)
        # we are at row, col, so we mark it visited:
        self.visited.add((row,col))
        self.enqueued.add((row,col)) # just in case
        # if we have reached our current subgoal, mark it visited
        if self.goal == (row, col):
            print  'reached goal: ' + str((row, col)) 
            self.goal = None
        # then we queue up some places to go next
        for i, (dr,dc) in enumerate(TowerEnvironment.MOVES):
            if sensors[2+i] == 0: # are we free to perform this action?
                # the action index should correspond to sensor index - 2
                r2 = row + dr # compute the row we could move to
                c2 = col + dc # compute the col we could move to
                if (r2,c2) not in self.enqueued:
                    self.mark_the_front(row,col,r2,c2)
                    self.enqueued.add((r2,c2))
                    heappush(self.pq, Cell(self.heuristic(r2, c2), r2, c2))
                    assert self.backpointers.get((row,col)) != (r2,c2)
                    self.backpointers[(r2,c2)] = row, col # remember where we (would) come from
    
    def start(self, time, sensors):
        """
        Choose initial action after receiving the first sensor vector.
        For the manual A* search, we enqueue the neighboring nodes and move to one of them.
        """
        # interpret the sensors
        row = int(sensors[0])
        col = int(sensors[1])
        # first, visit the node we are in and queue up some places to go
        self.visit(row, col, sensors)
        # now we have some candidate states and a way to return if we don't like it there, so let's try one!
        return self.get_action(row,col,sensors)

    def act(self, time, sensors, reward):
        """
        Choose an action after receiving the current sensor vector and the instantaneous reward from the previous time step.
        For the manual A* search, we deque our next node and check if we can go there. If we can, we do, and mark the node visited. 
        If we cannot, we have to follow the path to the goal.
        """
        # interpret the sensors
        row = int(sensors[0])
        col = int(sensors[1])
        # first, visit the node we are in and queue up some places to go
        self.visit(row, col, sensors)
        # now we have some candidate states and a way to return if we don't like it there, so let's try one!
        return self.get_action(row,col,sensors)

    def end(self, time, reward):
        """
        at the end of an episode, the environment tells us the final reward
        """
        print  "Final reward: %f, cumulative: %f" % (reward[0], self.fitness[0])
        self.reset()
        return True

    def destroy(self):
        """
        After one or more episodes, this agent can be disposed of
        """
        return True

    def mark_the_front(self, r, c, r2, c2):
        Tower.module.getMod().mark_maze_green(r2,c2)
        
    def mark_target(self, r, c):
        Tower.module.getMod().mark_maze_yellow(r,c)
    
    def mark_visited(self, r, c):
        Tower.module.getMod().mark_maze_blue(r,c)
        
    def mark_path(self, r, c):
        Tower.module.getMod().mark_maze_white(r,c)

class FrontAStarSearchAgent(AStarSearchAgent):
    """
    Egocentric A* algorithm with teleportation between fronts
    """
    def get_action(self, r, c, sensors):
        if not self.goal: # first, figure out where we are trying to go
            cell = heappop(self.pq)
            h, r2, c2 = cell.h, cell.r, cell.c
            Tower.module.getMod().unmark_maze_agent(r2,c2)
            Tower.module.getMod().mark_maze_yellow(r2,c2)
            self.goal = (r2, c2)
        # then, check if we can get there
        r2, c2 = self.goal
        dr, dc = r2 - r, c2 - c
        action = get_action_index((dr,dc)) # try to find the action (will return None if it's not there)
        v = self.constraints.get_instance() # make the action vector to return
        # first, is the node reachable in one action?
        if action is not None and sensors[2 + action] == 0:
            v[0] = action # if yes, do that action!
        else:
            # if not, we should teleport and return null action
            get_environment().teleport(self, r2, c2)
            v[0] = 4
        return v # return the action

class CloningAStarSearchAgent(FrontAStarSearchAgent):
    """
    Egocentric A* algorithm with teleportation between fronts and fronts marked by stationary agents
    """
    def get_action(self, r, c, sensors):
        if not self.goal: # first, figure out where we are trying to go
            cell = heappop(self.pq)
            h, r2, c2 = cell.h, cell.r, cell.c
            Tower.module.getMod().unmark_maze_agent(r2,c2)
            Tower.module.getMod().mark_maze_yellow(r2,c2)
            self.goal = (r2, c2)
        # then, check if we can get there
        r2, c2 = self.goal
        dr, dc = r2 - r, c2 - c
        action = get_action_index((dr,dc)) # try to find the action (will return None if it's not there)
        v = self.constraints.get_instance() # make the action vector to return
        # first, is the node reachable in one action?
        if action is not None and sensors[2 + action] == 0:
            v[0] = action # if yes, do that action!
        else:
            # if not, we should teleport and return null action
            get_environment().teleport(self, r2, c2)
            v[0] = 4
        return v # return the action

    def mark_the_front(self, r, c, r2, c2):
        Tower.module.getMod().mark_maze_agent("data/shapes/character/SydneyStatic.xml", r, c, r2, c2)

    def mark_visited(self, r, c):
        Tower.module.getMod().unmark_maze_agent(r,c)
        Tower.module.getMod().mark_maze_blue(r,c)

class MoveForwardAndStopAgent(AgentBrain):
    """
    Just move forward and stop!
    Warning, this messes with the environment internals
    """
    def __init__(self):
        AgentBrain.__init__(self) # do not remove!
    def initialize(self, init_info):
        self.actions = init_info.actions # action constraints
        self.idle_action = self.actions.get_instance()
        self.idle_action[0] = -1 # do-nothing action
        return True
    def start(self, time, sensors):
        v = self.actions.get_instance()
        state = get_environment().get_state(self) # our state
        maze = get_environment().maze # the maze we are in
        dr, dc = 0, 0
        if self.state.id in Tower.module.getMod().marker_states:
            ((r1, c1), (r2, c2)) = Tower.module.getMod().marker_states[self.state.id] # what are we marking?
            state.prev_rc, state.rc = (r1,c1), (r1,c1) # pretend like we were always there
            state.sensors = False # don't want sensors
            dr, dc = r2 - r1, c2 - c1 # figure out where we are going
        action = get_action_index( (dr, dc) )
        if action:
            v[0] = action
        else:
            v[0] = 4
        return v
    def act(self, time, sensors, reward):
        return self.idle_action
    def end(self, time, reward):
        return self.idle_action
    def destroy(self):
        return True

class RTNEATAgent(AgentBrain):
    """
    rtNEAT agent
    """
    def __init__(self):
        """
        Create an agent brain
        """
        # this line is crucial, otherwise the class is not recognized as an AgentBrainPtr by C++
        AgentBrain.__init__(self)

    def initialize(self, init_info):
        """
        Initialize an agent brain with sensor information
        """
        self.actions = init_info.actions # constraints for actions
        self.sensors = init_info.sensors # constraints for sensors
        return True

    def start(self, time, sensors):
        """
        start of an episode
        """
        return self.network_action(sensors)

    def act(self, time, sensors, reward):
        """
        a state transition
        """
        # return action
        return self.network_action(sensors)

    def end(self, time, reward):
        """
        end of an episode
        """
        print  "Final reward: %f, cumulative: %f" % (reward[0], self.fitness[0])
        get_ai("rtneat").release_organism(self)
        return True
        
    def destroy(self):
        """
        the agent brain is discarded
        """
        return True
        
    def network_action(self, sensors):
        """
        Take the current network
        Feed the sensors into it
        Activate the network to produce the output
        Collect and interpret the outputs as valid maze actions
        """
        assert(self.sensors.validate(sensors))
        inputs = Tower.module.input_to_neurons(self.sensors, sensors)
        org = get_ai("rtneat").get_organism(self)
        org.time_alive += 1
        net = org.net
        net.load_sensors(inputs)
        net.activate()
        outputs = net.get_outputs()
        actions = Tower.module.neurons_to_output(self.actions, outputs)
        assert(self.actions.validate(actions))
        return actions