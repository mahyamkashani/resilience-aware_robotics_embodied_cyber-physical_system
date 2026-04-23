import csv
import os

FILE_PATH = "results.csv"

def log_result(theta_crit, run_id, output):

    file_exists = os.path.isfile(FILE_PATH)

    with open(FILE_PATH, "a", newline="") as f:
        writer = csv.writer(f)

        # skriv header EN gång
        if not file_exists:
            writer.writerow([
                "theta_crit",
                "run",
                "delta",
                "gamma",
                "resilient",
                "result"
            ])

        writer.writerow([
            theta_crit,
            run_id,
            output["delta"],
            output["gamma"],
            output["resilient"],
            output["result"]
        ])