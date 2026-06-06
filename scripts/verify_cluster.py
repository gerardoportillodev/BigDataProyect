from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Spark standalone worker registration.")
    parser.add_argument("--spark-master-json", type=Path, required=True)
    parser.add_argument("--minimum-workers", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.spark_master_json.read_text(encoding="utf-8"))
    workers = payload.get("workers", [])
    alive = [worker for worker in workers if worker.get("state") == "ALIVE"]

    print(f"Workers registrados: {len(workers)}")
    print(f"Workers ALIVE: {len(alive)}")

    for worker in alive:
        print(
            "worker=", worker.get("host"),
            "cores=", worker.get("cores"),
            "cores_used=", worker.get("coresused"),
            "memory=", worker.get("memory"),
            "memory_used=", worker.get("memoryused"),
        )

    if len(alive) < args.minimum_workers:
        raise SystemExit(
            f"Clúster inválido: se requieren al menos {args.minimum_workers} workers ALIVE y solo hay {len(alive)}."
        )


if __name__ == "__main__":
    main()
