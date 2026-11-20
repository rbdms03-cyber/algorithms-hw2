"""Measure separate-chaining lookup costs and compare them with simple theory."""

import csv
import random
from pathlib import Path
from typing import NamedTuple

from src.hash_table import HashTable


CAPACITY = 4093
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
MAX_ITEM_COUNT = int(CAPACITY * LOAD_FACTORS[-1])


class Result(NamedTuple):
    target_load_factor: float
    load_factor: float
    item_count: int
    successful_measured: float
    successful_theory: float
    unsuccessful_measured: float
    unsuccessful_theory: float


def random_urls(count: int, seed: int, host_prefix: str) -> tuple[str, ...]:
    generator = random.Random(seed)
    return tuple(
        f"https://{host_prefix}-{generator.getrandbits(32):08x}.example/"
        f"{index}/{generator.getrandbits(64):016x}"
        for index in range(count)
    )


URLS = random_urls(MAX_ITEM_COUNT, 2026, "url")
MISSING_URLS = random_urls(MAX_ITEM_COUNT, 2027, "missing")


def measure(target_load_factor: float) -> Result:
    count = int(target_load_factor * CAPACITY)
    # A threshold of 4 keeps the table at 4093 buckets through the final load.
    table = HashTable(initial_capacity=CAPACITY, max_load_factor=4.0)
    keys = URLS[:count]
    for key in keys:
        table.put(key, key)

    if table.capacity != CAPACITY:
        raise RuntimeError(f"table capacity changed to {table.capacity}")

    successful = sum(table.probe_count(key) for key in keys) / count
    missing_urls = MISSING_URLS[:count]
    unsuccessful = sum(table.probe_count(url) for url in missing_urls) / count
    actual_load_factor = table.load_factor
    return Result(
        target_load_factor,
        actual_load_factor,
        count,
        successful,
        1 + actual_load_factor / 2,
        unsuccessful,
        actual_load_factor,
    )


def render_svg(results: list[Result]) -> str:
    width, height = 760, 440
    left, top, plot_width, plot_height = 72, 32, 640, 320
    max_cost = max(
        max(
            result.successful_measured,
            result.successful_theory,
            result.unsuccessful_measured,
            result.unsuccessful_theory,
        )
        for result in results
    ) * 1.12

    minimum_load = results[0].load_factor
    maximum_load = results[-1].load_factor

    def point(result: Result, cost: float) -> str:
        load_position = (result.load_factor - minimum_load) / (
            maximum_load - minimum_load
        )
        x = left + load_position * plot_width
        y = top + plot_height * (1 - cost / max_cost)
        return f"{x:.1f},{y:.1f}"

    series = (
        ("성공 측정", "successful_measured", "#1769aa"),
        ("성공 이론", "successful_theory", "#79a9d1"),
        ("실패 측정", "unsuccessful_measured", "#c62828"),
        ("실패 이론", "unsuccessful_theory", "#e58b8b"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="380" y="22" text-anchor="middle" font-size="16">연결 리스트 해시 테이블 탐색 비용</text>',
        f'<path d="M {left} {top} V {top + plot_height} H {left + plot_width}" fill="none" stroke="#333"/>',
        f'<text x="20" y="{top + plot_height / 2}" transform="rotate(-90 20 {top + plot_height / 2})" text-anchor="middle" font-size="12">평균 비교 노드 수</text>',
        f'<text x="{left + plot_width / 2}" y="{top + plot_height + 42}" text-anchor="middle" font-size="12">적재율 α</text>',
    ]
    for tick in range(5):
        cost = max_cost * tick / 4
        y = top + plot_height * (1 - tick / 4)
        parts.append(f'<path d="M {left - 4} {y:.1f} H {left + plot_width}" stroke="#ddd"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="10">{cost:.1f}</text>')
    for index, result in enumerate(results):
        x = left + (result.load_factor - minimum_load) / (
            maximum_load - minimum_load
        ) * plot_width
        if index % 2 == 0 or index == len(results) - 1:
            parts.append(f'<text x="{x:.1f}" y="{top + plot_height + 18}" text-anchor="middle" font-size="10">{result.load_factor:.2f}</text>')
    for label, field, color in series:
        points = " ".join(
            point(result, getattr(result, field)) for result in results
        )
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
        legend_index = series.index((label, field, color))
        legend_x = left + (legend_index % 2) * 180
        legend_y = height - 34 + (legend_index // 2) * 16
        parts.append(f'<path d="M {legend_x} {legend_y} h 24" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x + 30}" y="{legend_y + 4}" font-size="11">{label}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    results = [measure(target_load) for target_load in LOAD_FACTORS]

    output_dir = Path(__file__).resolve().parent
    csv_path = output_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                "target_load_factor",
                "load_factor",
                "item_count",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result.target_load_factor:.2f}",
                    f"{result.load_factor:.4f}",
                    result.item_count,
                    f"{result.successful_measured:.4f}",
                    f"{result.successful_theory:.4f}",
                    f"{result.unsuccessful_measured:.4f}",
                    f"{result.unsuccessful_theory:.4f}",
                )
            )

    svg_path = output_dir / "results.svg"
    svg_path.write_text(render_svg(results), encoding="utf-8")
    print("목표 α  실제 α    항목 수  성공 측정  성공 이론  실패 측정  실패 이론")
    for result in results:
        print(
            f"{result.target_load_factor:5.2f}  {result.load_factor:6.3f}"
            f"  {result.item_count:7d}  {result.successful_measured:8.3f}"
            f"  {result.successful_theory:8.3f}"
            f"  {result.unsuccessful_measured:8.3f}"
            f"  {result.unsuccessful_theory:8.3f}"
        )
    print(f"\nCSV: {csv_path}")
    print(f"SVG: {svg_path}")


if __name__ == "__main__":
    main()
