from disruption_degradation import degradation, disruption
from itertools import combinations

# definition 8
# Return all subsets of S
def powerset(S):
    for r in range(1, len(S) + 1):
        for combo in combinations(S, r):
            yield set(combo)

# If mitigation is possible: return 1
# Otherwise: return 0
def mitigation_feasability(S, tau, epsilon, current_task, current_goal, mitigatable_devices, theta_crit, theta_base, alpha_crit, alpha_base, psi_fn=None, severity=None):

    # If system is resilient - no mitigation needed
    if disruption(S, tau, epsilon, current_task, current_goal) == 1 \
    and degradation(S, tau, epsilon, current_task, current_goal, theta_crit, theta_base, alpha_crit, alpha_base, psi_fn=psi_fn, severity=severity) == 1:
        return {'feasible': 1, 'neutralized': set()}

    # Devices in S that can be mitigated
    mitigatable = S & mitigatable_devices
    for subset in powerset(mitigatable):
        S_prime = S - subset

        if disruption(S_prime, tau, epsilon, current_task, current_goal) == 1 \
            and degradation(S_prime, tau, epsilon, current_task, current_goal, theta_crit, theta_base, alpha_crit, alpha_base, psi_fn=psi_fn, severity=severity) == 1:
            return {'feasible': 1, 'neutralized': subset}

    return {'feasible': 0, 'neutralized': set()}
