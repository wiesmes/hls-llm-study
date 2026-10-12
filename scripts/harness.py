# harness.py
# One iteration of the LLM optimization loop:
# build the prompt, ask the model, extract the code, synthesize it.

# Part 1: imports
import csv
import re
import sys
from pathlib import Path
from datetime import datetime


from llm_client import ask
from run_variant import run_variant



# Part 2: file paths
ROOT = Path(__file__).resolve().parent.parent # repo root
HEADER = ROOT / "kernels" / "gemm" / "gemm.h"

START_KERNEL = ROOT/"kernels/gemm/gemm.cpp"
PROMPT = ROOT/"prompts/gemm_optimize.txt"
RESULTS = ROOT/"results" / "results.csv"
LOG_DIR = ROOT/"logs/llm_logs"
START_LABEL = "gemm_unopt"
MAX_DSP = 220
MAX_BRAM = 280      # BRAM_18K units, as reported by HLS
MAX_LUT = 53200
MAX_FF = 106400
MAX_PERIOD_NS = 10.0
N_ITERS = 10

# Part 3: extract_code(reply) -> code string or None
def extract_code(reply):
    """Return the code inside the first ```cpp block, or None if there isn't one."""
    match = re.search(r"```(?:cpp|c\+\+)?[ \t]*\n(.*?)```", reply, re.DOTALL)
    return match.group(1).strip() if match else None

# Part 4: find_row(label) -> the results.csv row with that label
def find_row(label):
    """Return the most recent results.csv row whose label matches, as a dict."""
    with open(RESULTS, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if label in r.values()]
    return rows[-1] if rows else None

def format_metrics(row):
    return "\n".join(f"{key}: {value}" for key, value in row.items())

def get_warnings(name):
    """Return the useful lines from this run's HLS log, or "" if there's no log."""
    log_path = ROOT/"build"/f"gemm_gemm_{name}"/"hls"/"hls.log"
    if not log_path.exists():
        return ""
    kept =[]
    for line in log_path.read_text(encoding = "utf-8", errors = "ignore").splitlines():
        if "WARNING" in line or "ERROR" in line or "Pipelining result" in line or "Loop Constraint Status" in line:
            kept.append(line[:300])
    return "\n".join(kept)

def get_failure_reason(name):
    """Return the first compiler error from this run's csim log, cleaned of the file path."""
    log_path = ROOT/"build"/f"gemm_gemm_{name}"/"hls"/"csim"/"report"/"gemm_csim.log"
    if not log_path.exists():
        return "No csim log found."
    for line in log_path.read_text(encoding = "utf-8", errors = "ignore").splitlines():
        if "error:" in line:
            return line.split("/")[-1][:300]

    return "No error found in csim log."

def classify(row):
    """Return 'build_fail', 'over_limit', 'timing_fail', or 'ok' for a run_variant result."""
    if row is None:
        return "build_fail"
    if float(row["dsp"]) > MAX_DSP or float(row["bram"]) > MAX_BRAM or float(row["lut"]) > MAX_LUT or float(row["ff"]) > MAX_FF:
        return "over_limit"
    if float(row["estimated_period_ns"]) > MAX_PERIOD_NS:
        return "timing_fail"
    return "ok"

# Part 5: build_prompt(kernel, metrics) -> the filled-in prompt

def build_prompt(kernel, metrics, warnings="", history=""):
    text = PROMPT.read_text(encoding="utf-8")
    text = text.replace("{header}", HEADER.read_text(encoding="utf-8"))
    text = text.replace("{kernel}", kernel)
    text = text.replace("{metrics}", metrics)
    text = text.replace("{warnings}", warnings)
    text = text.replace("{history}", history)
    return text

# Part 6: main() -> run one iteration
def main():
    condition = sys.argv[1] if len(sys.argv) > 1 else "full"
    if condition not in ("full", "metrics_only"):
        raise SystemExit(f"Unknown condition: {condition}")

    run_id = datetime.now().strftime("%Y%m%d_%H%M") + "_" + condition
    print("Run ID:", run_id)

    # Starting state
    current_row = find_row(START_LABEL)

    if current_row is None:
        raise SystemExit(f"No row labeled {START_LABEL} in {RESULTS}")
    
    current_code = START_KERNEL.read_text(encoding="utf-8")
    current_warnings = get_warnings("unopt")
    history = []

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for i in range(1, N_ITERS + 1):
        name = f"{run_id}_iter{i}"
        print(f"\n=== {name} ===")

        if condition == "full":
            warnings_text = current_warnings
            history_text = "\n".join(history)
        else:
            warnings_text = ""
            history_text = ""

        prompt = build_prompt(current_code, format_metrics(current_row),
                              warnings_text, history_text)
        
        print("Asking model...")
        reply = ask(prompt)
        (LOG_DIR / f"{name}_prompt.txt").write_text(prompt, encoding="utf-8")
        (LOG_DIR / f"{name}_reply.txt").write_text(reply, encoding="utf-8")

        code = extract_code(reply)
        if code is None:
            row, status = None, "no_code"
        else:
            print("Synthesizing...")
            row = run_variant(name, code)
            status = classify(row)

        # One-line summary for history and the screen
        if row is None:
            if status == "build_fail":
                summary = f"iter{i}: {status}: {get_failure_reason(name)}"
            else:
                summary = f"iter{i}: {status}"
        else:
            summary = (f"iter{i}: {status}, latency {row['latency_max']}, "
                       f"DSP {row['dsp']}, LUT {row['lut']}, "
                       f"est. clock {row['estimated_period_ns']} ns")
        history.append(summary)
        print(summary)

        # Greedy: accept only a valid improvement
        if status == "ok" and float(row["latency_max"])<float(current_row["latency_max"]):
            current_code = code
            current_row = row
            current_warnings = get_warnings(name)
            print("Accepted as new current kernel.")

    print("\nBest result:", format_metrics(current_row))

if __name__ == "__main__":
    main()