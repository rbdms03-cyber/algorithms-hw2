"""Measure separate-chaining lookup costs and compare them with simple theory."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable


CAPACITY = 1000
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
KEY_VALUES = random.Random(2026).sample(range(2**32), CAPACITY * 4)
MISSING_VALUES = random.Random(2027).sample(range(2**32), CAPACITY * 4)


def measure(load_factor: float) -> tuple[float, float, float, float]:
    count = int(load_factor * CAPACITY)
    table = HashTable(initial_capacity=CAPACITY, max_load_factor=4.0)
    keys = [f"url-{value:08x}" for value in KEY_VALUES[:count]]
    for key in keys:
        table.put(key, key)

    successful = sum(table.probe_count(key) for key in keys) / count
    missing_keys = [f"missing-{value:08x}" for value in MISSING_VALUES[:count]]
    unsuccessful = sum(table.probe_count(key) for key in missing_keys) / count
    return table.load_factor, successful, 1 + table.load_factor / 2, unsuccessful


def render_svg(results: list[tuple[float, float, float, float, float]]) -> str:
    width, height = 760, 440
    left, top, plot_width, plot_height = 72, 32, 640, 320
    max_cost = max(max(row[1:]) for row in results) * 1.12

    def point(index: int, cost: float) -> str:
        x = left + index * plot_width / (len(results) - 1)
        y = top + plot_height * (1 - cost / max_cost)
        return f"{x:.1f},{y:.1f}"

    series = (
        ("성공 측정", 1, "#1769aa"),
        ("성공 이론", 2, "#79a9d1"),
        ("실패 측정", 3, "#c62828"),
        ("실패 이론", 4, "#e58b8b"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="380" y="22" text-anchor="middle" font-size="16">연결 리스트 해시 테이블 탐색 비용</text>',
        f'<path d="M {left} {top} V {top + plot_height} H {left + plot_width}" fill="none" stroke="#333"/>',
        f'<text x="20" y="{top + plot_height / 2}" transform="rotate(-90 20 {top + plot_height / 2})" text-anchor="middle" font-size="12">평균 방문 노드 수</text>',
        f'<text x="{left + plot_width / 2}" y="{top + plot_height + 42}" text-anchor="middle" font-size="12">적재율 α</text>',
    ]
    for tick in range(5):
        cost = max_cost * tick / 4
        y = top + plot_height * (1 - tick / 4)
        parts.append(f'<path d="M {left - 4} {y:.1f} H {left + plot_width}" stroke="#ddd"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="10">{cost:.1f}</text>')
    for index, row in enumerate(results):
        x = left + index * plot_width / (len(results) - 1)
        if index % 2 == 0:
            parts.append(f'<text x="{x:.1f}" y="{top + plot_height + 18}" text-anchor="middle" font-size="10">{row[0]:.2f}</text>')
    for label, column, color in series:
        points = " ".join(point(index, row[column]) for index, row in enumerate(results))
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
        legend_index = series.index((label, column, color))
        legend_x = left + (legend_index % 2) * 180
        legend_y = height - 34 + (legend_index // 2) * 16
        parts.append(f'<path d="M {legend_x} {legend_y} h 24" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x + 30}" y="{legend_y + 4}" font-size="11">{label}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    results = []
    for target_load in LOAD_FACTORS:
        actual_load, successful, successful_theory, unsuccessful = measure(target_load)
        results.append((actual_load, successful, successful_theory, unsuccessful, actual_load))

    output_dir = Path(__file__).resolve().parent
    csv_path = output_dir / "probe_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                "load_factor",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        for load, successful, successful_theory, unsuccessful, _ in results:
            writer.writerow(
                (
                    f"{load:.2f}",
                    f"{successful:.4f}",
                    f"{successful_theory:.4f}",
                    f"{unsuccessful:.4f}",
                    f"{load:.4f}",
                )
            )

    svg_path = output_dir / "probe_experiment.svg"
    svg_path.write_text(render_svg(results), encoding="utf-8")
    print(" α     성공 측정  성공 이론  실패 측정  실패 이론")
    for load, successful, successful_theory, unsuccessful, _ in results:
        print(
            f"{load:4.2f}  {successful:8.3f}  {successful_theory:8.3f}"
            f"  {unsuccessful:8.3f}  {load:8.3f}"
        )
    print(f"\nCSV: {csv_path}")
    print(f"SVG: {svg_path}")


if __name__ == "__main__":
    main()
