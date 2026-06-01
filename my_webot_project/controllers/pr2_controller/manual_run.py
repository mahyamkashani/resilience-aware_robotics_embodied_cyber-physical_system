from pr2_controller import run_simulation
from logger import log_result

CONFIG = "configs/experiment2.json"
RESULT_FILE = "../results/framework_correctness/exp1.csv"

output = run_simulation(CONFIG, use_ros=True)

log_result(RESULT_FILE, output)