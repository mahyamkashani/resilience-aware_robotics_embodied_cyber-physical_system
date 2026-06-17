import sys
from pathlib import Path

PR2_DIR = Path(__file__).resolve().parent / "pr2_controller"
sys.path.insert(0, str(PR2_DIR))

from pr2_controller import run_simulation
from logger import log_result
from constants import CONFIG, RESULT_FILE


def main():
    #   python3 manual_run.py [config_path] [result_path]
    # Falls back to the defaults in constants.py when no args are given.
    config_arg = sys.argv[1] if len(sys.argv) > 1 else CONFIG
    result_arg = sys.argv[2] if len(sys.argv) > 2 else RESULT_FILE

    config_path = Path(config_arg)
    if not config_path.is_absolute():
        config_path = PR2_DIR / config_arg

    result_path = Path(result_arg)
    if not result_path.is_absolute():
        result_path = PR2_DIR / result_arg

    output = run_simulation(str(config_path), use_ros=True)
    log_result(str(result_path), output)


if __name__ == "__main__":
    main()
