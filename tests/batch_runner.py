import sys
import os
import json
import glob
import requests

API_BASE = os.getenv("INCUBRIX_API_URL", "http://127.0.0.1:8000")

def run_batch(input_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    files = glob.glob(os.path.join(input_path, "*.json")) if os.path.isdir(input_path) else [input_path]
    summary = []

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        endpoint = payload.pop("_endpoint", "/api/v1/jobs")
        headers = payload.pop("_headers", {})
        resp = requests.post(f"{API_BASE}{endpoint}", json=payload, headers=headers, timeout=15)
        out_data = {"input_file": os.path.basename(fpath), "status_code": resp.status_code, "response": resp.json()}
        out_file = os.path.join(output_dir, f"result_{os.path.basename(fpath)}")
        with open(out_file, "w", encoding="utf-8") as out_f:
            json.dump(out_data, out_f, indent=2)
        summary.append(out_data)
        print(f"Processed {os.path.basename(fpath)} -> HTTP {resp.status_code}")

    with open(os.path.join(output_dir, "batch_summary.json"), "w", encoding="utf-8") as sf:
        json.dump(summary, sf, indent=2)

if __name__ == "__main__":
    in_arg = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_inputs"
    out_arg = sys.argv[2] if len(sys.argv) > 2 else "tests/batch_outputs"
    run_batch(in_arg, out_arg)