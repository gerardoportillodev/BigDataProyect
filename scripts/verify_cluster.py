"""Verify that the distributed cluster meets minimum requirements."""

from __future__ import annotations

import argparse
import json
import re
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Verify cluster health")
    p.add_argument("--hdfs-report", default=None, help="Path to hdfs dfsadmin -report output")
    p.add_argument("--spark-master-json", required=True, help="Path to Spark Master /json/ output")
    p.add_argument("--minimum-datanodes", type=int, default=2)
    p.add_argument("--minimum-workers", type=int, default=2)
    return p.parse_args()


def check_hdfs(report_path: str, minimum: int) -> int:
    with open(report_path) as fh:
        text = fh.read()
    match = re.search(r"Live datanodes\s*\((\d+)\)", text)
    live = int(match.group(1)) if match else 0
    print(f"[verify] HDFS DataNodes vivos: {live} (mínimo requerido: {minimum})")
    if live < minimum:
        print(f"[verify] ERROR: Se encontraron {live} DataNodes vivos, se requieren al menos {minimum}.")
        sys.exit(1)
    return live


def check_spark(json_path: str, minimum: int) -> int:
    with open(json_path) as fh:
        data = json.load(fh)
    workers = data.get("workers", [])
    alive = [w for w in workers if w.get("state") == "ALIVE"]
    print(f"[verify] Spark Workers ALIVE: {len(alive)} (mínimo requerido: {minimum})")
    for w in alive:
        print(f"  - {w.get('host','?')}:{w.get('port','?')}  cores={w.get('cores','?')}  memory={w.get('memory','?')}MB")
    if len(alive) < minimum:
        print(f"[verify] ERROR: Se encontraron {len(alive)} workers ALIVE, se requieren al menos {minimum}.")
        sys.exit(1)
    return len(alive)


def main():
    args = parse_args()

    errors = []

    if args.hdfs_report:
        try:
            check_hdfs(args.hdfs_report, args.minimum_datanodes)
        except SystemExit:
            errors.append("HDFS DataNodes insuficientes")

    try:
        check_spark(args.spark_master_json, args.minimum_workers)
    except SystemExit:
        errors.append("Spark Workers insuficientes")

    if errors:
        print(f"[verify] FALLÓ: {'; '.join(errors)}")
        sys.exit(1)

    print("[verify] Cluster OK — requisitos mínimos cumplidos.")


if __name__ == "__main__":
    main()
