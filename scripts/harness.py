# harness.py
# One iteration of the LLM optimization loop:
# build the prompt, ask the model, extract the code, synthesize it.

# Part 1: imports
import csv
import re
from pathlib import Path

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
    name = "llm_iter1"

    start = find_row(START_LABEL)
    if start is None:
        raise SystemExit(f"No row labeled {START_LABEL} in {RESULTS}")

    prompt = build_prompt(START_KERNEL.read_text(encoding="utf-8"), format_metrics(start))

    print("Asking model...")
    reply = ask(prompt)

    # Save the prompt and raw reply: you'll need these for the paper.
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"{name}_prompt.txt").write_text(prompt, encoding="utf-8")
    (LOG_DIR / f"{name}_reply.txt").write_text(reply, encoding="utf-8")

    code = extract_code(reply)
    if code is None:
        print("FAIL: no code block in reply")
        return

    print("Synthesizing...")
    row = run_variant(name, code)
    if row is None:
        print("FAIL: build failed (csim or csynth)")
        return

    print("OK:", row)


if __name__ == "__main__":
    main()