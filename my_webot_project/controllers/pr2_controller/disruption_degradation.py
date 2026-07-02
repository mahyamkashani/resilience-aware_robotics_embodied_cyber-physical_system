import math

# Def 6: Tolerable disruption (delta)
def disruption(S, tau, epsilon, current_task, current_goal):

    for d in S:
        if tau.get((d, current_task), 0) == 2 or epsilon.get((d, current_goal), 0) == 2:
            return 0
    return 1


# Def 7: monotonic degradation function
def monotonic_degradation(S, tau, epsilon, current_task, current_goal, alpha_crit, alpha_base):
    value = 1
    for d in S:

        level = max(
            tau.get((d, current_task), 0), 
            epsilon.get((d, current_goal), 0)
        )
        if level == 2:
            value = value - alpha_crit
        elif level == 1:
            value = value - alpha_base
        else:
            continue
    
    #print(f'Psi value {max(value,0)}')
    return max(value, 0)

def exponential_degradation(S, tau, epsilon, current_task, current_goal, alpha_crit, alpha_base, severity=None):
    severity = severity or {}
    k_crit = 0
    k_base = 0
    for d in S:
        level = max(
            tau.get((d, current_task), 0),
            epsilon.get((d, current_goal), 0)
        )
        w = severity.get(d, 1.0)
        if level == 2:
            k_crit += w
        elif level == 1:
            k_base += w

    # Criterion 1 (crit device, level=2): steep exponential decay
    psi_crit = math.exp(-alpha_crit * k_crit)

    # Criterion 2 (non-crit device, level=1): gentle exponential decay
    psi_base = math.exp(-alpha_base * k_base)

    # Piecewise function:
    # When k_crit=0 then psi_crit=1, only criterion 2 active.
    # When k_base=0 then psi_base=1, only criterion 1 active.
    return psi_crit * psi_base


# Def 7: Tolerable Degradation (gamma)
def degradation(S, tau, epsilon, current_task, current_goal, theta_crit, theta_base, alpha_crit, alpha_base, psi_fn=None, severity=None):
    if psi_fn is None:
        psi_fn = monotonic_degradation

    if psi_fn is exponential_degradation:
        psi = psi_fn(S, tau, epsilon, current_task, current_goal, alpha_crit, alpha_base, severity=severity)
    else:
        psi = psi_fn(S, tau, epsilon, current_task, current_goal, alpha_crit, alpha_base)

    # Check if any critical devices exist in S
    has_critical = False
    for d in S:
        level = max(
            tau.get((d, current_task), 0), 
            epsilon.get((d, current_goal), 0)
        )
        if level == 2: # required
            has_critical = True
            break
        
    # Select threshold
    if has_critical:
        theta = theta_crit
    else:
        theta = theta_base

    # Evaluate degradation
    if psi < theta:
        return 0
    return 1
