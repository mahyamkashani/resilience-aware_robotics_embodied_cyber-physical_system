'''
from examples import test_example, example_A
from resilience_manager import ResilienceManager

#RM = ResilienceManager()
S = {"A4"}

test = example_A

G = test["G"]
T = test["T"]
current_goal = next(iter(G))
current_task = next(iter(T))
tau = test['tau']
epsilon = test['epsilon']


def disruption(S, tau, epsilon, current_task, current_goal):

    for d in S:
        if tau.get((d, current_task), 0) == 2 or epsilon.get((d, current_goal), 0) == 2:
            print("Critical component in S")
            return 0
    return 1


# return a value between 0 and 1
def monotonic_degradation(S, tau, epsilon, current_task, current_goal):
    value = 1

    for d in S:

        level = max(
            tau.get((d, current_task), 0), 
            epsilon.get((d, current_goal), 0)
        )

        if level == 2:
            value = value - 0.2
        elif level == 1:
            value = value - 0.05
    
    print(f'Psi value {max(value,0)}')
    return max(value, 0)



def degradation(S, tau, epsilon, current_task, current_goal):

    psi = monotonic_degradation(S, tau, epsilon, current_task, current_goal)

    for d in S:
        level = max(
            tau.get((d, current_task), 0), 
            epsilon.get((d, current_goal), 0)
        )
        if level == 2:
            theta = 0.85 # theta_crit
        elif level == 1:
            theta = 0.75 # theta_base
        else:
            continue

        if psi < theta:
            return 0
    return 1


delta = disruption(S, tau, epsilon, current_task, current_goal)
gamma = degradation(S, tau, epsilon, current_task, current_goal)

if delta == 1 and gamma == 1:
    print(f'system is resilient (Disruption = {delta} & Degradation = {gamma})') # System tolerates disruption without degradation
else:
    print(f'system is not resilient (Disruption = {delta} & Degradation = {gamma})')
'''
from itertools import combinations

S = ['a','b','c']
def powerset(S):

    for r in range(len(S) + 1):
        for combo in combinations(S, r):
            yield set(combo)

for subset in powerset(S):
    print(subset)