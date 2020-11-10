import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush
from math import inf

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


def heuristic(state, prev_state, action, axe_in_goals):
    # Implement your heuristic here!
    required_items = ["bench", "furnace", "cart", "wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "wooden_axe", "stone_axe", "iron_axe"]
    
    # De-prioritize making multiple tools
    for item in required_items:
        if state[item] > 1:
            return inf

    # De-priotize moves that use a weaker tool
    if (action.startswith("wooden_pickaxe") and (state["stone_pickaxe"] > 0 or state["iron_pickaxe"] > 0)) or \
        (action.startswith("stone_pickaxe") and state["iron_pickaxe"] > 0) or \
        (action.startswith("wooden_axe") and (state["stone_axe"] > 0 or state["iron_axe"] > 0)) or \
        (action.startswith("stone_axe") and state["iron_axe"] > 0):
        return inf

    # smelt if can, since coal and ore is useless on its own
    if action.startswith("smelt ore in furnace"):
        return -100

    # if the goal doesn't contain axe then deoprioritize making axes
    if "_axe" in action and not axe_in_goals:
        return inf

    # if you don't have a bench but have enough wood to make it, deprioritize everything else
    if state["bench"] == 0 and state["plank"] > 3 and state["plank"] < prev_state["plank"]:
        return inf

    # if you don't have a furnace but have enough wood to make it, deprioritize everything else
    if state["bench"] == 0 and state["cobble"] > 7 and state["cobble"] < prev_state["cobble"]:
        return inf

    # if you have a cart prioritize making rails for it
    if state["cart"] > 0 and state["iron_pickaxe"] > prev_state["iron_pickaxe"]:
        return inf

    #if state[""]
    
    # don't mine cobble after furnace
    if state['furnace'] > 0 and state["cobble"] > prev_state["cobble"]:
        return 1000
    
    # dont mine ore or coal if no furnace
    if state['furnace'] == 0 and (state["coal"] > prev_state["coal"] or state["ore"] > prev_state["ore"]):
        return 1000

    # CAP raw materials: woods, plank, stick, cobble, ingot, coal, ore
    if state["wood"] > prev_state["wood"] and prev_state["wood"] > 1:
        return inf
    if state["plank"] > prev_state["plank"] and prev_state["plank"] > 4:
        return inf
    if state["stick"] > prev_state["stick"] and prev_state["stick"] > 4:
        return inf
    if state["cobble"] > prev_state["cobble"] and prev_state["cobble"] > 8:
        return inf
    if state["ingot"] > prev_state["ingot"] and prev_state["ingot"] > 100:
        return inf
    if state["coal"] > prev_state["coal"] and prev_state["coal"] > 1:
        return inf
    if state["ore"] > prev_state["ore"] and prev_state["ore"] > 1:
        return inf
    
    return 0

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()
    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

    # check if axe is in goals
    axe_in_goals = False
    for goal in Crafting["Goal"]:
        if Crafting["Goal"][goal] > 0 and goal.endswith("_axe"):
            axe_in_goals = True

    frontier, actions = [], {}
    heappush(frontier, (0, state))

    came_from = {}
    cost_so_far = {}

    came_from[state] = None
    cost_so_far[state] = 0

    state_explored_counter = 0
    while time() - start_time < limit:
        current_dist, current_state = heappop(frontier)
        state_explored_counter +=1
        #print(current_state)
        if is_goal(current_state):
            break
        #for next in graph.neighbors(current):
        for action, effect, cost in graph(current_state):
            new_cost = cost_so_far[current_state] + cost
            if effect not in cost_so_far or new_cost < cost_so_far[effect]:
                cost_so_far[effect] = new_cost
                came_from[effect] = current_state
                actions[effect] = action

                priority = new_cost + heuristic(effect, current_state, action, axe_in_goals)
                heappush(frontier, (priority, effect))


        
    #make path[] here
    path = []
    if is_goal(current_state):
        while current_state is not state: # state here is initial_state
            path.append((current_state, actions[current_state]))
            current_state = came_from[current_state]
        path.reverse()
        return path, time() - start_time, state_explored_counter

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
    resulting_plan, compute_time, states_count = search(graph, state, is_goal, 30, heuristic)

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
    print("In-game Time Cost:",time_cost)
    print("Compute-Time",compute_time)
    print("Number of Actions:",action_cost)
    print("Number of states explored:", states_count)