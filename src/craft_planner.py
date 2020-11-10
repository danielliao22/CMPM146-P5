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


def heuristic(state, prev_state, action):
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
        return inf/2

    if action.startswith("smelt ore in furnace"):
        return -100
    
    goal_items = Crafting["Goal"].keys()
    deprioritize_iron_pickaxe = False
    for g_item in goal_items:
        if g_item == "cart":
            deprioritize_iron_pickaxe = True
    # print(goal_items)

    # if can make a new tool, prioritize it; especially if it's a furnace or bench
    for item in required_items:
        if prev_state[item] < 1 and state[item] > 0:
            # priotize making a furnace and bench even more
            if item == "furnace" or item == "bench":
                return -1000
            if deprioritize_iron_pickaxe and item == "iron_pickaxe":
                return 10
            if item.endswith("cart"):
                return -100
            elif item.endswith("_axe"): # de-priotize axes
                return inf
    
        # if prev_state["ingot"] > 15 and state["ingot"] > prev_state["ingot"]:
    #     return inf

    return 0

def heuristic2(state, action):
    # Takes a next state, returns a heuristic value

    value = 0

    # current action rule
    for name, rule in Crafting['Recipes'].items():
        if name == action:
            action_rule = rule

    # list of tools/tables
    tools_tables_list = ["bench",
                         "furnace",
                         "iron_axe",
                         "iron_pickaxe",
                         "stone_axe",
                         "stone_pickaxe",
                         "wooden_axe",
                         "wooden_pickaxe"]

    # PRUNE 1
    # don't craft duplicate tools
    if 'Produces' in action_rule:
        for t in tools_tables_list:
            if (state[t] > 1) and (t in action_rule['Produces']):
                value += inf


    # PRUNE 2
    # follow logical tool crafting flow

    # prioritize bench
    if state['bench'] == 0 and ('stick' in action_rule['Produces']):
        value += inf

    # prioritize wooden pickaxe
    if state['wooden_pickaxe'] == 0 and ('wooden_axe' in action_rule['Produces']):
        value += inf

    # prioritize stone pickaxe
    if state['stone_pickaxe'] == 0 and ('stone_axe' in action_rule['Produces']):
        value += inf

    # prioritize furnace
    if state['furnace'] == 0 and ('stone_axe' in action_rule['Produces']):
        value += inf

    # prioritize iron pickaxe
    if state['iron_pickaxe'] == 0 and ('stone_axe' in action_rule['Produces'] or \
                                        'wooden_axe' in action_rule['Produces'] or \
                                        'iron_axe' in action_rule['Produces']):
        value += inf

    # don't mine coal/ore without furnace
    if state['furnace'] == 0 and ('coal' in action_rule['Produces'] or \
                                    'ore' in action_rule['Produces']):
        value += inf

    # don't mine cobble after furnace
    if state['furnace'] > 0 and 'cobble' in action_rule['Produces']:
        value += 100


    # PRUNE 3
    # general limiters (confine to min(item as recipe output, item as recipe input))
    if state['wood'] > 1:
        value += 100
    if state['plank'] > 4:
        value += 100
    if state['stick'] > 4:
        value += 100
    if state['cobble'] > 8:
        value += 100
    if state['coal'] > 1:
        value += 100
    if state['ore'] > 1:
        value += 100
    if state['ingot'] > 6:
        value += 100
    if state['cart'] > 1:
        value += 100

    # balance coal/ore/ingot
    if state['ore'] > state['coal']+1:
        value += 100
    if state['coal'] > state['ore']+1:
        value += 100
    if state['ore'] > state['ingot']+1:
        value += 100



    # solve order-insensitive?
    if 'Consumes' in action_rule:
        value += 0
    else:
        value += 5

    # return final heuristic value
    return value

# not working
def get_required_list(goal):
    required_needed = State({key: 0 for key in Crafting['Items']})
    tools = ['bench', 'wooden_pickaxe', 'wooden_axe', 'stone_axe', 'stone_pickaxe', 'iron_pickaxe', 'iron_axe', 'furnace']
    queue = []

    for item in goal:
        queue.append((item, goal[item]))

    while queue:
        item, amount = queue.pop()
        # print(item, amount)

        if item in tools:
            required_needed[item] = 1

        for action in Crafting['Recipes']:
            if item in Crafting['Recipes'][action]['Produces']:


                if 'Consumes' in Crafting['Recipes'][action]:
                    for consumable in Crafting['Recipes'][action]['Consumes']:
                        queue.append((consumable, Crafting['Recipes'][action]['Consumes'][consumable]))


                if 'Requires' in Crafting['Recipes'][action]:
                    for requireable in Crafting['Recipes'][action]['Requires']:
                        if required_needed[requireable] == 0:
                            print(action,"|", requireable)
                            queue.append((requireable, 1))
                
    return required_needed

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()
    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

    # frontier = PriorityQueue()
    frontier, actions = [], {}
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

    visited = set()
    visited.add(state)

    #required_items = get_required_list(Crafting["Goal"])
    #print(required_items)
    # while not frontier.empty():
    while time() - start_time < limit:
        #current = frontier.get()
        current_dist, current_state = heappop(frontier)
        # print(current_state)
        #if current == goal:
        if is_goal(current_state):
        #break
            print(time() - start_time)
            break
        #for next in graph.neighbors(current):
        for action, effect, cost in graph(current_state):
            #new_cost = cost_so_far[current] + graph.cost(current, next)
            new_cost = current_dist + cost

            #if next not in cost_so_far or new_cost < cost_so_far[next]:
            if effect not in cost_so_far or new_cost < cost_so_far[effect]:
                #cost_so_far[next] = new_cost
                cost_so_far[effect] = new_cost
                priority = new_cost + heuristic2(effect, action) # heuristic(effect, current_state, action)

                #came_from[next] = current
                came_from[effect] = current_state
                actions[effect] = action
                #frontier.put(next, priority)
                heappush(frontier, (priority, effect))


        
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
    print("HELLO")
    print("time-cost=",time_cost)
    print("Len=",action_cost)