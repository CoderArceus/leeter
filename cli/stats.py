"""CLI stats/search commands – thin wrappers around leeter_core.analytics.

All data aggregation and search logic lives in leeter_core.analytics.
This module handles presentation only (print/renderer).
"""

import os
import json

from cli.output import renderer


def cmd_stats(args):
    from leeter_core.analytics import get_stats_summary

    summary = get_stats_summary()

    print("\n--- Leeter Statistics ---")
    print("📊 Solved / Total")
    print(f"  Easy:   {summary.easy.solved:3d} / {summary.easy.total:3d}")
    print(f"  Medium: {summary.medium.solved:3d} / {summary.medium.total:3d}")
    print(f"  Hard:   {summary.hard.solved:3d} / {summary.hard.total:3d}")
    print(
        f"  TOTAL:  {summary.total_solved:3d} / {summary.total_problems:3d}"
    )

    if summary.avg_benchmark_ns is not None:
        print(
            f"\n⚡ Average Solution Time: "
            f"{summary.avg_benchmark_ns / 1000.0:.2f} µs"
        )
    print()


def cmd_search(args):
    from leeter_core.analytics import search_problems

    query = args.query
    hits = search_problems(query)

    print(f"\n🔍 Searching for '{query}'...")

    if not hits:
        print("  No matches found.")
    else:
        for hit in hits:
            status = "✅" if hit.solved else "❌"
            print(
                f"  {status} [{hit.id}] {hit.title} ({hit.difficulty})"
            )
    print()
