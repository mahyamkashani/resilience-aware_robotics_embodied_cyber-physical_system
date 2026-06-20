import csv
import os

#FILE_PATH = "results.csv"


def log_psi(file_path, time, psi):
    print(f"[t={time:>6.2f}s] psi={psi:.3f}")
    log_event(file_path, {"time": time, "psi": round(psi, 3)})


def log_delta(file_path, time, delta, operation="NORMAL"):
    log_event(file_path, {"time": time, "delta": delta, "operation": operation})


def log_event(file_path, row):
    file_exists = os.path.isfile(file_path)
    with open(file_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def log_result(file_path, output):

    file_exists = os.path.isfile(file_path)

    detection_rate = 1 - output["kappa_crit"]
    #degradation_percent = round(output["degradation"] * 100, 1)
    #time = round(output["time"],1)

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)

        # skriv header EN gång
        if not file_exists:
            writer.writerow([
                "detection_rate",
                "delta",
                "gamma",
                "resilient",
                "result",
                #"time",
                #"degradation",
                "theta_base",
                "theta_crit",
                "alpha_base",
                #"alpha_crit",
                "psi"

            ])

        writer.writerow([
            detection_rate,
            output["delta"],
            output["gamma"],
            output["resilient"],
            output["result"],
            #time,
            #degradation_percent,
            output["theta_base"],
            output["theta_crit"],
            output["alpha_base"],
            #output["alpha_crit"],
            output["psi"]
        ])