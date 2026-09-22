import subprocess, csv, pathlib
 # declare a function
def run_variant(name: str, source: str) -> dict | None:
    # write source to kernels/gemm/gemm_{name}.cpp
    kernel_path = pathlib.Path("kernels/gemm")
    (kernel_path / f"gemm_{name}.cpp").write_text(source)   

    results = subprocess.run(f"make bench KERNEL=gemm VARIANT={name}", 
                             shell=True, capture_output=True, text=True
                             )

    if results.returncode != 0:
        print(f"Error running variant {name}: {results.stderr}")
        return None
    
    with open("results/results.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["label"] == f"gemm_{name}"]
    return rows[-1] if rows else None


if __name__ == "__main__":
    src = pathlib.Path("kernels/gemm/gemm_opt2.cpp").read_text()
    print(run_variant("test", src))