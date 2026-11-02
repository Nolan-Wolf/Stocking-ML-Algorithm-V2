"""One-command Coffee Bros V2 run. Local only, synthetic data only.
Generates data, runs backtest, snapshot, proposals, dashboard, and charts.
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, ".venv", "bin", "python") if os.path.exists(os.path.join(HERE, ".venv", "bin", "python")) else sys.executable

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    run([PY, os.path.join(HERE, "src", "data_gen.py")])
    run([PY, os.path.join(HERE, "src", "pipeline.py")])
    run([PY, os.path.join(HERE, "src", "dashboard.py")])
    run([PY, os.path.join(HERE, "src", "charts.py")])
    run([PY, os.path.join(HERE, "tests", "test_v2.py")])
    print("Done. Open predictions/dashboard.html and read RESULTS_SUMMARY.md after pipeline writes it.")
