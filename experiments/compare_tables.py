"""Compare chaining and linear probing on the same deterministic workloads."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


CAPACITY = 1000
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
REPOSITORY_URL = "https://github.com/rbdms03-cyber/algorithms-hw2"
KEY_VALUES = random.Random(20261120).sample(range(2**32), int(CAPACITY * 0.9))
MISSING_VALUES = random.Random(20261121).sample(range(2**32), int(CAPACITY * 0.9))


def measure(load_factor: float) -> tuple[float, ...]:
    count = int(load_factor * CAPACITY)
    keys = [f"url-{value:08x}" for value in KEY_VALUES[:count]]
    missing_keys = [f"missing-{value:08x}" for value in MISSING_VALUES[:count]]
    chaining = HashTable(CAPACITY, max_load_factor=1.0)
    linear = LinearProbingHashTable(CAPACITY, max_load_factor=1.0)
    for key in keys:
        chaining.put(key, key)
        linear.put(key, key)

    chaining_success = sum(chaining.probe_count(key) for key in keys) / count
    chaining_failure = sum(chaining.probe_count(key) for key in missing_keys) / count
    linear_success = sum(linear.probe_count(key) for key in keys) / count
    linear_failure = sum(linear.probe_count(key) for key in missing_keys) / count
    actual_load = len(chaining) / chaining.capacity
    return (
        actual_load,
        chaining_success,
        1 + actual_load / 2,
        chaining_failure,
        actual_load,
        linear_success,
        0.5 * (1 + 1 / (1 - actual_load)),
        linear_failure,
        0.5 * (1 + 1 / (1 - actual_load) ** 2),
    )


def render_svg(rows: list[tuple[float, ...]]) -> str:
    width, height = 1000, 620
    panels = (
        ("Successful searches", 1, 2, 5, 6, 5.0),
        ("Unsuccessful searches", 3, 4, 7, 8, 52.0),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="24" text-anchor="middle" font-size="18">Hash-table search cost by load factor</text>',
    ]
    for title, chain_measured, chain_theory, linear_measured, linear_theory, max_cost in panels:
        panel_index = 0 if title.startswith("Successful") else 1
        left, top, plot_width, plot_height = 80 + panel_index * 470, 72, 390, 390
        parts.append(
            f'<text x="{left + plot_width / 2}" y="52" text-anchor="middle" font-size="14">{title}</text>'
        )
        parts.append(
            f'<path d="M {left} {top} V {top + plot_height} H {left + plot_width}" fill="none" stroke="#333"/>'
        )
        parts.append(
            f'<text x="{left + plot_width / 2}" y="{top + plot_height + 42}" text-anchor="middle" font-size="12">Load factor alpha</text>'
        )
        for tick in range(5):
            fraction = tick / 4
            y = top + plot_height * (1 - fraction)
            parts.append(
                f'<path d="M {left - 4} {y:.1f} H {left + plot_width}" stroke="#ddd"/>'
            )
            parts.append(
                f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="10">{max_cost * fraction:.0f}</text>'
            )
        for index, row in enumerate(rows):
            x = left + index * plot_width / (len(rows) - 1)
            parts.append(
                f'<text x="{x:.1f}" y="{top + plot_height + 18}" text-anchor="middle" font-size="9">{row[0]:.1f}</text>'
            )

        def line(column: int, color: str, dashed: bool = False) -> None:
            points = []
            for index, row in enumerate(rows):
                x = left + index * plot_width / (len(rows) - 1)
                y = top + plot_height * (1 - row[column] / max_cost)
                points.append(f"{x:.1f},{y:.1f}")
            dash = ' stroke-dasharray="7,5"' if dashed else ""
            parts.append(
                f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
                f'stroke-width="2"{dash}/>'
            )

        line(chain_measured, "#1769aa")
        line(chain_theory, "#1769aa", True)
        line(linear_measured, "#c62828")
        line(linear_theory, "#c62828", True)

    legend = (
        ("Chaining measured", "#1769aa", False),
        ("Chaining theory", "#1769aa", True),
        ("Linear measured", "#c62828", False),
        ("Linear theory", "#c62828", True),
    )
    for index, (label, color, dashed) in enumerate(legend):
        x = 170 + index * 190
        y = 560
        dash = ' stroke-dasharray="7,5"' if dashed else ""
        parts.append(f'<path d="M {x} {y} h 28" stroke="{color}" stroke-width="2"{dash}/>')
        parts.append(f'<text x="{x + 34}" y="{y + 4}" font-size="11">{label}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text(text: str, x: float, y: float, size: int = 10) -> str:
    return f"BT /F1 {size} Tf {x:.1f} {y:.1f} Td ({_pdf_escape(text)}) Tj ET\n"


def _pdf_chart(
    rows: list[tuple[float, ...]],
    chart_y: float,
    measured_columns: tuple[int, int],
    theory_columns: tuple[int, int],
) -> str:
    left, bottom, plot_width, plot_height = 70, chart_y + 28, 455, 135
    max_cost = max(
        row[column]
        for row in rows
        for column in measured_columns + theory_columns
    ) * 1.08
    commands = [
        "0.5 w 0.2 G\n",
        f"{left} {bottom} m {left} {bottom + plot_height} l {left + plot_width} {bottom + plot_height} l S\n",
    ]
    for tick in range(5):
        fraction = tick / 4
        y = bottom + plot_height * fraction
        commands.append(f"0.85 G {left} {y:.1f} m {left + plot_width} {y:.1f} l S\n")
        commands.append(_pdf_text(f"{max_cost * fraction:.1f}", 42, y - 3, 8))
    for index, row in enumerate(rows):
        x = left + index * plot_width / (len(rows) - 1)
        commands.append(_pdf_text(f"{row[0]:.1f}", x - 5, bottom - 14, 8))

    colors = ("0.09 0.41 0.67", "0.78 0.15 0.15")
    series = (
        (measured_columns[0], colors[0], False),
        (theory_columns[0], colors[0], True),
        (measured_columns[1], colors[1], False),
        (theory_columns[1], colors[1], True),
    )
    for column, color, dashed in series:
        commands.append(f"{color} RG 1.5 w {'[4 3] 0 d' if dashed else '[] 0 d'}\n")
        for index, row in enumerate(rows):
            x = left + index * plot_width / (len(rows) - 1)
            y = bottom + plot_height * row[column] / max_cost
            commands.append(f"{x:.1f} {y:.1f} {'m' if index == 0 else 'l'} ")
        commands.append("S\n")
    commands.append("[] 0 d 0 G\n")
    legend = (
        ("chain measured", colors[0], False),
        ("chain theory", colors[0], True),
        ("linear measured", colors[1], False),
        ("linear theory", colors[1], True),
    )
    for index, (label, color, dashed) in enumerate(legend):
        x = 68 + index * 125
        y = chart_y + 3
        commands.append(f"{color} RG 1.5 w {'[4 3] 0 d' if dashed else '[] 0 d'} {x} {y} m {x + 20} {y} l S\n")
        commands.append(_pdf_text(label, x + 24, y - 3, 8))
    commands.append("[] 0 d 0 G\n")
    return "".join(commands)


def _pdf_table(rows: list[tuple[float, ...]], page_y: float, start_column: int) -> str:
    x_positions = (62, 128, 232, 338, 442)
    headings = ("alpha", "chain obs", "chain theory", "linear obs", "linear theory")
    commands = [_pdf_text("   ".join(headings), 60, page_y, 9)]
    for index, row in enumerate(rows):
        y = page_y - 17 - index * 15
        values = (
            f"{row[0]:.1f}",
            f"{row[start_column]:.3f}",
            f"{row[start_column + 1]:.3f}",
            f"{row[start_column + 2]:.3f}",
            f"{row[start_column + 3]:.3f}",
        )
        for value, x in zip(values, x_positions):
            commands.append(_pdf_text(value, x, y, 9))
    return "".join(commands)


def _write_pdf(path: Path, rows: list[tuple[float, ...]]) -> None:
    pages = []
    successful = (
        _pdf_text(f"Repository: {REPOSITORY_URL}", 60, 824, 8)
        + _pdf_text("Hash table comparison: successful searches", 60, 800, 16)
        + _pdf_text("Methods: both use Horner h=(31*h+ord(c)) mod 1000.", 60, 780, 9)
        + _pdf_text("Chaining stores collisions in bucket lists; linear probes next slots with wrap-around.", 60, 765, 9)
        + _pdf_text("Setup: capacity 1000; alpha 0.1-0.9 by 0.1; keys seeded 20261120, misses 20261121.", 60, 750, 9)
        + _pdf_text("At each alpha, n=100-900 hits and n distinct misses; a visited node/slot is one probe.", 60, 735, 9)
        + _pdf_text("Theory: chaining 1 + alpha/2; linear probing 0.5 * (1 + 1/(1-alpha)).", 60, 720, 9)
        + _pdf_chart(rows, 550, (1, 5), (2, 6))
        + _pdf_table(rows, 530, 1)
        + _pdf_text("Measured and theoretical successful-search costs are plotted above.", 60, 368, 9)
        + _pdf_text("At alpha=0.9, success observed (chain/linear) is "
                    f"{rows[-1][1]:.3f}/{rows[-1][5]:.3f}; theory is "
                    f"{rows[-1][2]:.3f}/{rows[-1][6]:.3f}.", 60, 351, 9)
        + _pdf_text("Finite samples and key distribution explain small deviations from theory.", 60, 334, 9)
    )
    unsuccessful = (
        _pdf_text("Hash table comparison: unsuccessful searches", 60, 800, 16)
        + _pdf_text("Theory: chaining alpha; linear probing 0.5 * (1 + 1/(1-alpha)^2).", 60, 780, 9)
        + _pdf_text("A miss includes the empty slot that terminates the search.", 60, 765, 9)
        + _pdf_chart(rows, 575, (3, 7), (4, 8))
        + _pdf_table(rows, 555, 3)
        + _pdf_text("As alpha approaches 1, long runs of occupied slots form (primary clustering).", 60, 390, 9)
        + _pdf_text("A miss must cross a run and reach an empty slot; expected cost grows roughly as", 60, 373, 9)
        + _pdf_text("0.5/(1-alpha)^2, so the cost rises sharply as free slots disappear.", 60, 356, 9)
        + _pdf_text("At alpha=0.9, miss observed (chain/linear) is "
                    f"{rows[-1][3]:.3f}/{rows[-1][7]:.3f}; theory is "
                    f"{rows[-1][4]:.3f}/{rows[-1][8]:.3f}.", 60, 339, 9)
        + _pdf_text("Agent mistake: /table omitted visited slots; test_linear_table_shows_visited_slots caught it.", 60, 318, 8)
        + _pdf_text("The slot-path display was restored, then the full test suite passed.", 60, 303, 8)
        + _pdf_text("Reflection: comparing hits and misses showed how strongly load affects probing.", 60, 280, 9)
        + _pdf_text("The fixed seeds make this run repeatable, though other key sets may differ.", 60, 265, 9)
    )
    pages.extend((successful, unsuccessful))

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
    ]
    for page_number, content in enumerate(pages):
        page_id = 3 + page_number * 2
        content_id = page_id + 1
        stream = content.encode("ascii")
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 7 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"endstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(pdf)


def main() -> None:
    rows = [measure(load_factor) for load_factor in LOAD_FACTORS]
    output_dir = Path(__file__).resolve().parent
    csv_path = output_dir / "table_comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                "load_factor",
                "chaining_success_measured",
                "chaining_success_theory",
                "chaining_failure_measured",
                "chaining_failure_theory",
                "linear_success_measured",
                "linear_success_theory",
                "linear_failure_measured",
                "linear_failure_theory",
            )
        )
        writer.writerows(tuple(f"{value:.4f}" for value in row) for row in rows)

    svg_path = output_dir / "table_comparison.svg"
    svg_path.write_text(render_svg(rows), encoding="utf-8")
    pdf_path = output_dir / "table_comparison_report.pdf"
    _write_pdf(pdf_path, rows)

    print("alpha | chain success | chain miss | linear success | linear miss")
    for row in rows:
        print(f"{row[0]:.1f} | {row[1]:.3f} | {row[3]:.3f} | {row[5]:.3f} | {row[7]:.3f}")
    print(f"\nCSV: {csv_path}\nSVG: {svg_path}\nPDF (2 pages): {pdf_path}")


if __name__ == "__main__":
    main()
