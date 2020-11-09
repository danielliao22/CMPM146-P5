import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush
import math

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


# Done
def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        if 'Consumes' in rule:
            for item in rule['Consumes']:
                if rule['Consumes'][item] > state[item]:
                    return False
        if 'Requires' in rule:
            for item in rule['Requires']:
                if state[item] < 1:
                    return False

        return True

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].

        next_state = state.copy()
        if 'Produces' in rule:
            for item in rule['Produces']:
                next_state[item] += rule['Produces'][item]
        if 'Consumes' in rule:
            for item in rule['Consumes']:
                next_state[item] -= rule['Consumes'][item]

        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for item in goal:
            if state[item] < goal[item]:
                return False


        return True

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


def heuristic(state, prev_state, action):
    # Implement your heuristic here!
    required_items = ["bench", "furnace", "cart", "wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "wooden_axe", "stone_axe", "iron_axe"]
    
    # De-prioritize making multiple tools
    for item in required_items:
        if state[item] > 1:
            return math.inf
    
    # if can make a new tool, prioritize it; especially if it's a furnace or bench
    for item in required_items:
        if prev_state[item] < 1 and state[item] > 0:
            # priotize making a furnace and bench even more
            if item == "furnace" or item == "bench":
                return -1000000
            else:
                return -100000

    # De-priotize moves that use a weaker tool
    if (action.startswith("wooden_pickaxe") and (state["stone_pickaxe"] > 0 or state["iron_pickaxe"] > 0)) or \
        (action.startswith("stone_pickaxe") and state["iron_pickaxe"] > 0) or \
        (action.startswith("wooden_axe") and (state["stone_axe"] > 0 or state["iron_axe"] > 0)) or \
        (action.startswith("stone_axe") and state["iron_axe"] > 0):
        return math.inf/2

    # if you have a pickaxe prioritize mining if you're below a threshold; de-prioritize if above a treshold
    if action.split()[0].endswith("_pickaxe"):
        if prev_state["cobble"] < 4 and prev_state["cobble"] < state["cobble"]:
            return -10000
        elif prev_state["cobble"] > 10 and prev_state["cobble"] < state["cobble"]:
            return math.inf/4
        elif prev_state["coal"] > 12 and prev_state["coal"] < state["coal"]:
            return math.inf/4
        elif prev_state["ore"] > 12 and prev_state["ore"] < state["ore"]:
            return math.inf/4

    # if you can craft an item then do it
    if action.startswith("craft"):
        return 0

    return 10

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

    # frontier = PriorityQueue()
    frontier, visited, actions = [], [], {}
    # frontier.put(start, 0)
    heappush(frontier, (0, state))
    # came_from = dict()
    came_from = {}
    # cost_so_far = dict()
    cost_so_far = {}
    # came_from[start] = None
    came_from[state] = None
    # cost_so_far[start] = 0
    cost_so_far[state] = 0

    # while not frontier.empty():
    while time() - start_time < limit:
        #current = frontier.get()
        current_dist, current_state = heappop(frontier)
        # print(current_state)
        #if current == goal:
        if is_goal(current_state):
        #break
            break
        #for next in graph.neighbors(current):
        for action, effect, cost in graph(current_state):
            if effect not in visited:
                #new_cost = cost_so_far[current] + graph.cost(current, next)
                new_cost = current_dist + cost
                #if next not in cost_so_far or new_cost < cost_so_far[next]:
                if effect not in cost_so_far or new_cost < cost_so_far[effect]:
                    #cost_so_far[next] = new_cost
                    cost_so_far[effect] = new_cost
                    priority = new_cost + heuristic(effect, current_state, action)
    
                    #came_from[next] = current
                    came_from[effect] = current_state
                    actions[effect] = action
                    #frontier.put(next, priority)
                    heappush(frontier, (priority, effect))

        visited.append(current_state)

        
    #make path[] here
    path = []
    if is_goal(current_state):
        while current_state is not state: # state here is initial_state
            path.append((current_state, actions[current_state]))
            current_state = came_from[current_state]
        path.reverse()
        return path

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # # List of items that can be in your inventory:
    # print('All items:', Crafting['Items'])
    #
    # # List of items in your initial inventory with amounts:
    # print('Initial inventory:', Crafting['Initial'])
    #
    # # List of items needed to be in your inventory at the end of the plan:
    # print('Goal:',Crafting['Goal'])
    #
    # # Dict of crafting recipes (each is a dict):
    # print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic)

    action_cost = 0
    time_cost = 0
    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            print('\t',state)
            print(action)

        # print in-game time
        for state, action in resulting_plan:
            for recipe in all_recipes:
                # print(action, "|",recipe.name)
                if recipe.name == action:
                    time_cost += recipe.cost
        
        action_cost = len(resulting_plan)
        
    print("time-cost=",time_cost)
    print("Len=",action_cost)