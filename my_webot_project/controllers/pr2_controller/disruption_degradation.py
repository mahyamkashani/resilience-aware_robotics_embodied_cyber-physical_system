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


# Def 7: Tolerable Degradation (gamma)
def degradation(S, tau, epsilon, current_task, current_goal, theta_crit, theta_base, alpha_crit, alpha_base):

    psi = monotonic_degradation(S, tau, epsilon, current_task, current_goal, alpha_crit, alpha_base)

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
