#!/usr/bin/env python3
"""Generate a simple deterministic PDF from the Neurolabs guide markdown subset."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path


PAGE_WIDTH = 595.2756
PAGE_HEIGHT = 841.8898
LEFT = 56.69291
RIGHT = 56.69291
TOP_START = PAGE_HEIGHT - 70
BOTTOM_GUARD = 62
BODY_LINE_HEIGHT = 14
PRIMARY_ORANGE = (0.929412, 0.333333, 0.0)


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_text(text: str, max_width: float, font_size: float, mono: bool = False) -> list[str]:
    if not text:
        return [""]
    avg_width = font_size * (0.60 if mono else 0.53)
    max_chars = max(10, int(max_width / avg_width))
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


@dataclass
class Page:
    commands: list[str]


class PDFBuilder:
    def __init__(self) -> None:
        self.pages: list[Page] = []
        self.current = Page(commands=[])
        self.pages.append(self.current)

    def new_page(self) -> None:
        self.current = Page(commands=[])
        self.pages.append(self.current)

    def set_stroke(self, r: float, g: float, b: float) -> None:
        self.current.commands.append(f"{r:.6f} {g:.6f} {b:.6f} RG")

    def set_fill(self, r: float, g: float, b: float) -> None:
        self.current.commands.append(f"{r:.6f} {g:.6f} {b:.6f} rg")

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.current.commands.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def rect(self, x: float, y: float, w: float, h: float) -> None:
        self.current.commands.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re S")

    def text(self, x: float, y: float, text: str, font: str, size: float) -> None:
        self.current.commands.append(
            f"BT /{font} {size:.2f} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({pdf_escape(text)}) Tj ET"
        )

    def save(self, output_path: Path) -> None:
        font_objects = {
            "F1": "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            "F2": "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
            "F3": "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        }
        objects: list[str] = [""]  # 1-indexed
        font_ids: dict[str, int] = {}
        for name, obj in font_objects.items():
            font_ids[name] = len(objects)
            objects.append(obj)

        page_ids: list[int] = []
        content_ids: list[int] = []
        pages_root_id = len(objects) + (2 * len(self.pages))
        catalog_id = pages_root_id + 1

        for page in self.pages:
            stream = "\n".join(page.commands).encode("latin-1", errors="replace")
            content_id = len(objects)
            objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream")
            content_ids.append(content_id)
            page_id = len(objects)
            objects.append(
                "<< /Type /Page /Parent {parent} 0 R /MediaBox [0 0 {w:.2f} {h:.2f}] "
                "/Resources << /Font << /F1 {f1} 0 R /F2 {f2} 0 R /F3 {f3} 0 R >> >> "
                "/Contents {content} 0 R >>".format(
                    parent=pages_root_id,
                    w=PAGE_WIDTH,
                    h=PAGE_HEIGHT,
                    f1=font_ids["F1"],
                    f2=font_ids["F2"],
                    f3=font_ids["F3"],
                    content=content_id,
                )
            )
            page_ids.append(page_id)

        objects.append(
            "<< /Type /Pages /Kids [{kids}] /Count {count} >>".format(
                kids=" ".join(f"{page_id} 0 R" for page_id in page_ids),
                count=len(page_ids),
            )
        )
        objects.append(f"<< /Type /Catalog /Pages {pages_root_id} 0 R >>")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as handle:
            handle.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            offsets = [0]
            for index in range(1, len(objects)):
                offsets.append(handle.tell())
                body = f"{index} 0 obj\n{objects[index]}\nendobj\n".encode("latin-1")
                handle.write(body)
            xref_offset = handle.tell()
            handle.write(f"xref\n0 {len(objects)}\n".encode("ascii"))
            handle.write(b"0000000000 65535 f \n")
            for offset in offsets[1:]:
                handle.write(f"{offset:010d} 00000 n \n".encode("ascii"))
            handle.write(
                (
                    f"trailer\n<< /Size {len(objects)} /Root {catalog_id} 0 R >>\n"
                    f"startxref\n{xref_offset}\n%%EOF\n"
                ).encode("ascii")
            )


def parse_blocks(markdown: str) -> list[tuple[str, object]]:
    blocks: list[tuple[str, object]] = []
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if stripped.startswith("```"):
            fence_lang = stripped[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].rstrip().startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            blocks.append(("code", {"lang": fence_lang, "lines": code_lines}))
        elif stripped.startswith("# "):
            pass
        elif stripped.startswith("## "):
            blocks.append(("heading", stripped[3:].strip()))
        elif stripped.startswith("- "):
            blocks.append(("bullet", stripped[2:].strip()))
        elif stripped.strip():
            paragraph = [stripped.strip()]
            i += 1
            while i < len(lines):
                next_line = lines[i].rstrip()
                if not next_line.strip() or next_line.startswith("#") or next_line.startswith("- ") or next_line.startswith("```"):
                    i -= 1
                    break
                paragraph.append(next_line.strip())
                i += 1
            blocks.append(("paragraph", " ".join(paragraph)))
        i += 1
    return blocks


def draw_footer(builder: PDFBuilder, page_number: int) -> None:
    builder.set_stroke(*PRIMARY_ORANGE)
    builder.line(LEFT, 43.93701, PAGE_WIDTH - RIGHT, 43.93701)
    builder.text(LEFT, 28, "Neurolabs • Confidential Partner Documentation", "F1", 9)
    builder.text(PAGE_WIDTH - RIGHT - 115, 28, f"Neurolabs SDK • Page {page_number}", "F1", 9)


def render(markdown_path: Path, output_path: Path, title: str, document_id: str, version: str, date: str) -> None:
    builder = PDFBuilder()

    def start_page(page_number: int) -> float:
        draw_footer(builder, page_number)
        return TOP_START

    y = start_page(1)
    builder.text(LEFT, y, title, "F2", 24)
    y -= 28
    builder.text(LEFT, y, "Technical Integration Specification", "F2", 14)
    y -= 24
    for meta in [
        f"Document ID: {document_id}",
        f"Version: {version}",
        f"Date: {date}",
        "Status: Partner integration reference",
        "Owner: Neurolabs",
    ]:
        builder.text(LEFT, y, meta, "F1", 10.5)
        y -= BODY_LINE_HEIGHT
    y -= 10

    page_number = 1
    blocks = parse_blocks(markdown_path.read_text())
    content_width = PAGE_WIDTH - LEFT - RIGHT

    for kind, payload in blocks:
        if kind == "heading":
            heading = str(payload)
            needed = 22 + BODY_LINE_HEIGHT
            if y - needed < BOTTOM_GUARD:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            builder.text(LEFT, y, heading, "F2", 13)
            y -= 22
            continue

        if kind == "paragraph":
            lines = wrap_text(str(payload), content_width, 10.5)
            needed = len(lines) * BODY_LINE_HEIGHT + 6
            if y - needed < BOTTOM_GUARD:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            for line in lines:
                builder.text(LEFT, y, line, "F1", 10.5)
                y -= BODY_LINE_HEIGHT
            y -= 6
            continue

        if kind == "bullet":
            text = str(payload)
            bullet_indent = 14
            lines = wrap_text(text, content_width - bullet_indent, 10.5)
            needed = len(lines) * BODY_LINE_HEIGHT + 4
            if y - needed < BOTTOM_GUARD:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            builder.text(LEFT, y, "•", "F1", 10.5)
            builder.text(LEFT + bullet_indent, y, lines[0], "F1", 10.5)
            y -= BODY_LINE_HEIGHT
            for line in lines[1:]:
                builder.text(LEFT + bullet_indent, y, line, "F1", 10.5)
                y -= BODY_LINE_HEIGHT
            y -= 4
            continue

        if kind == "code":
            code = payload  # type: ignore[assignment]
            code_lines = code["lines"] or [""]
            wrapped: list[str] = []
            for line in code_lines:
                wrapped.extend(wrap_text(line or " ", content_width - 20, 8.2, mono=True))
            block_height = max(1, len(wrapped)) * 11 + 18
            if y - block_height < BOTTOM_GUARD:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            box_y = y - block_height + 10
            builder.set_stroke(*PRIMARY_ORANGE)
            builder.rect(LEFT, box_y, content_width, block_height)
            inner_y = y - 12
            for line in wrapped:
                builder.text(LEFT + 10, inner_y, line, "F3", 8.2)
                inner_y -= 11
            y = box_y - 8

    builder.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    render(
        markdown_path=Path(args.source),
        output_path=Path(args.output),
        title=args.title,
        document_id=args.document_id,
        version=args.version,
        date=args.date,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
