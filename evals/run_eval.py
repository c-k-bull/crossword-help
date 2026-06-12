"""
Evaluation script for the clue solver.

Loads ground truth clues from data/clues.csv, runs solve_clue on each,
and reports accuracy metrics.

Usage:
    python evals/run_eval.py
    python evals/run_eval.py --limit 10
    python evals/run_eval.py --save
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from crosshelp.clue import solve_clue


EVAL_DIR = Path(__file__).parent
DATA_PATH = EVAL_DIR / "data" / "clues.csv"
RESULTS_DIR = EVAL_DIR / "results"


def load_dataset(split=None):
    """Load ground truth clues from CSV, optionally filtered by split."""
    examples = []
    with open(DATA_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            if not normalized.get("clue"):
                continue
            if split and normalized.get("split", "").lower() != split.lower():
                continue
            examples.append({
                "clue": normalized["clue"],
                "pattern": normalized["pattern"],
                "answer": normalized["answer"].upper(),
                "source": normalized.get("source", "unknown"),
                "split": normalized.get("split", "unknown"),
            })
    return examples


def evaluate_one(example):
    """Run solve_clue on a single example and check correctness."""
    candidates = solve_clue(example["clue"], example["pattern"])
    is_correct_top1 = (
        len(candidates) > 0 and candidates[0] == example["answer"]
    )
    is_correct_topk = example["answer"] in candidates
    return {
        "clue": example["clue"],
        "pattern": example["pattern"],
        "expected": example["answer"],
        "candidates": candidates,
        "correct_top1": is_correct_top1,
        "correct_topk": is_correct_topk,
    }


def run_eval(limit=None, verbose=True, split=None):
    """Run evaluation over the dataset, return metrics."""
    examples = load_dataset(split=split)
    if limit:
        examples = examples[:limit]

    results = []
    for i, example in enumerate(examples, 1):
        if verbose:
            print(f"[{i}/{len(examples)}] {example['clue']!r} ({example['pattern']})...", end=" ")
        result = evaluate_one(example)
        results.append(result)
        if verbose:
            mark = "✓" if result["correct_top1"] else ("~" if result["correct_topk"] else "✗")
            top = result["candidates"][0] if result["candidates"] else "(none)"
            print(f"{mark}  got {top}, expected {result['expected']}")

    total = len(results)
    top1 = sum(1 for r in results if r["correct_top1"])
    topk = sum(1 for r in results if r["correct_topk"])

    metrics = {
        "total": total,
        "top1_correct": top1,
        "topk_correct": topk,
        "top1_accuracy": top1 / total if total else 0,
        "topk_accuracy": topk / total if total else 0,
    }

    if verbose:
        print("\n" + "=" * 50)
        print(f"Top-1 accuracy: {top1}/{total} = {metrics['top1_accuracy']:.1%}")
        print(f"Top-k accuracy: {topk}/{total} = {metrics['topk_accuracy']:.1%}")
        print("=" * 50)

    return metrics, results


def save_results(metrics, results):
    """Save eval results to a timestamped JSON file."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = RESULTS_DIR / f"eval-{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump({"metrics": metrics, "results": results}, f, indent=2)
    print(f"Saved results to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run clue solver eval.")
    parser.add_argument("--limit", type=int, help="Only run on first N examples")
    parser.add_argument("--save", action="store_true", help="Save results to JSON")
    parser.add_argument("--quiet", action="store_true", help="Less output")
    parser.add_argument("--split", choices=["train", "test"], help="Which split to evaluate")
    args = parser.parse_args()

    metrics, results = run_eval(
        limit=args.limit,
        verbose=not args.quiet,
        split=args.split,
    )
    if args.save:
        save_results(metrics, results)


if __name__ == "__main__":
    main()