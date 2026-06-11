from pr2_controller import run_simulation
from logger import log_result
from constants import CONFIG, RESULT_FILE


def main():
    output = run_simulation(CONFIG, use_ros=True)

    log_result(RESULT_FILE, output)

if __name__=="__main__":
    main()