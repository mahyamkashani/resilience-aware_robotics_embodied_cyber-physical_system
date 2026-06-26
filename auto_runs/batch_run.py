#!/usr/bin/env python3
"""
Usage: python3 batch_run_exp13.py 20 15 120    # 20 runs, 15 s pause, 120 s timeout
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCRIPT         = HERE / "data_exp13.sh"
DEFAULT_N      = 10
DEFAULT_PAUSE  = 20  
DEFAULT_TIMEOUT = 120  
DEFAULT_CONFIG = "configs/experiment13.json"
DEFAULT_RESULT = "../results/framework_correctness/exp13-attackall.csv"


def run_once(config: str, result: str, timeout: int) -> bool:
    cmd = ["bash", str(SCRIPT), config, result]
    print(f"  cmd: {' '.join(cmd)}")
    
    proc = subprocess.Popen(cmd, start_new_session=True)
    try:
        proc.wait(timeout=timeout)
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"\n  TIMEOUT: run exceeded {timeout} s — killing Webots and moving on")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        subprocess.run(["pkill", "-9", "webots"], capture_output=True)
        proc.wait()
        return False


def pause(seconds: int) -> None:
    print(f"  Waiting {seconds} s for Webots to fully exit", end="", flush=True)
    for _ in range(seconds):
        time.sleep(1)
        print(".", end="", flush=True)
    print()


def main():
    n       = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_N
    delay   = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PAUSE
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_TIMEOUT
    config  = sys.argv[4]      if len(sys.argv) > 4 else DEFAULT_CONFIG
    result  = sys.argv[5]      if len(sys.argv) > 5 else DEFAULT_RESULT

    print(f"Batch run: {n} repetitions, {delay} s pause, {timeout} s timeout per run")
    print(f"  config : {config}")
    print(f"  result : {result}")
    print()

    ok = 0
    for i in range(1, n + 1):
        print(f"=== Run {i}/{n} ===")
        success = run_once(config, result, timeout)
        if success:
            ok += 1
        else:
            print(f"  WARNING: run {i} exited with non-zero status")
        if i < n:
            pause(delay)

    print(f"\nDone. {ok}/{n} runs succeeded. Results in: {result}")


if __name__ == "__main__":
    main()
