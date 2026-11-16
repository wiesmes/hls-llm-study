# harness.py
# The LLM optimization loop: build the prompt, ask the model, extract the code,
# skip duplicates, synthesize, and keep the best valid kernel.
# Usage: py scripts/harness.py [full | metrics_only]

# Part 1: imports
import csv
import re
import sys
from pathlib import Path
from datetime import datetime


from llm_client import ask, save_counts
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

def normalize(code):
    """Strip comments and whitespace so kernels that differ only cosmetically count as the same."""
    code = re.sub(r"//.*", "", code)                         # remove // comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)   # remove /* */ comments
    return re.sub(r"\s+", "", code)                          # remove all whitespace

def get_change(code):
    """Return the model's one-line description of its change, from a '// CHANGE:' comment."""
    match = re.search(r"//\s*CHANGE:\s*(.*)", code)
    return match.group(1).strip()[:120] if match else "no description given"

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
        if "mismatches" in line:
            return line.strip()[:300]
        if "error:" in line:
            return line.split("/")[-1][:300]

    return "No error found in csim log."

def failure_type(name):
    """Say why a kernel produced no CSV row: tool_error, wrong_result, compile_error, or synth_fail."""
    log_path = ROOT/"build"/f"gemm_gemm_{name}"/"hls"/"csim"/"report"/"gemm_csim.log"
    if not log_path.exists():
        return "tool_error"      # csim never ran: a setup problem, not the model
    log = log_path.read_text(encoding="utf-8", errors="ignore")
    if "mismatches" in log:      # checked first: a wrong-result log also has ERROR lines
        return "wrong_result"
    if "error:" in log:
        return "compile_error"
    return "synth_fail"          # csim passed, so synthesis must have failed

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
    print("Start warnings length:", len(current_warnings))  # 0 means get_warnings can't find hls.log (Fix 2)
    history = []
    seen = {normalize(current_code): "the starting kernel"}

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
        save_counts(LOG_DIR / f"{name}_counts.json")

        code = extract_code(reply)
        if code is None:
            row, status = None, "no_code"
        elif normalize(code) in seen:
            row, status = None, "duplicate"
        else:
            print("Synthesizing...")
            row = run_variant(name, code)
            status = classify(row)
            if status == "build_fail":
                status = failure_type(name)
                if status == "tool_error":
                    raise SystemExit(f"{name}: csim never ran. Fix the setup, then rerun.")

        # One-line summary for history and the screen
        change = get_change(code) if code else "no code"
        if status == "duplicate":
            summary = f'iter{i}: "{change}" -> duplicate of {seen[normalize(code)]}, not synthesized'
        elif row is None:
            if status in ("wrong_result", "compile_error", "synth_fail"):
                summary = f'iter{i}: "{change}" -> {status}: {get_failure_reason(name)}'
            else:
                summary = f'iter{i}: "{change}" -> {status}'
        else:
            summary = (f'iter{i}: "{change}" -> {status}, latency {row["latency_max"]}, '
                       f'DSP {row["dsp"]}, LUT {row["lut"]}, '
                       f'est. clock {row["estimated_period_ns"]} ns')
        history.append(summary)
        print(summary)

        # Remember this kernel so a repeat is caught next time
        if code and status != "duplicate":
            seen[normalize(code)] = f"iter{i} ({status})"

        # Greedy: accept only a valid improvement
        if status == "ok" and float(row["latency_max"]) < float(current_row["latency_max"]):
            current_code = code
            current_row = row
            current_warnings = get_warnings(name)
            print("Accepted as new current kernel.")

    print("\nBest result:", format_metrics(current_row))

if __name__ == "__main__":
    main()
