from pr2_controller import run_simulation
from logger import log_result

theta_crit = 0.85
run_id = 1

output = run_simulation("configs/experiment1.json", use_ros=True)

log_result(theta_crit, run_id, output)