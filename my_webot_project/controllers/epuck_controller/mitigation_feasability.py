from dispruption_degradation import degradation, disruption
from itertools import combinations


# Return all subsets of S
def powerset(S):
    for r in range(len(S) + 1):
        for combo in combinations(S, r):
            yield set(combo)

# Subset of devices that can be neutralized thorough such mitigations
mitiagtable_devices = {'camera', 'distance_sensor'}

# my returns 0 or 1 if mitigation strategy can be applied
# Return true if possible, otherwise return false
def mitigation_feasability(S, tau, epsilon, current_task, current_goal):

    # If system is resilient - no mitigation needed
    if disruption(S, tau, epsilon, current_task, current_goal) == 1 \
    and degradation(S, tau, epsilon, current_task, current_goal) == 1:
        return {'feasible': 1, 'neutralized': set()}

    # Devices in S that can be mitigated
    mitigatable = S & mitiagtable_devices
    for subset in powerset(mitigatable):
        S_prime = S - subset

        if disruption(S_prime, tau, epsilon, current_task, current_goal) == 1 \
            and degradation(S_prime, tau, epsilon, current_task, current_goal) == 1:
            return {'feasible': 1, 'neutralized': subset}

    return {'feasible': 0, 'neutralized': None}
