#!/usr/bin/env python3
"""Generate a simple deterministic PDF from the Neurolabs guide markdown subset."""

from __future__ import annotations

import argparse
import math
import re
import unicodedata
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


def sanitize_text(value: str) -> str:
    normalized = (
        value.replace("•", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("…", "...")
        .replace("\u00a0", " ")
    )
    normalized = unicodedata.normalize("NFKD", normalized)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text


def pdf_escape(value: str) -> str:
    value = sanitize_text(value)
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_text(
    text: str,
    max_width: float,
    font_size: float,
    mono: bool = False,
    preserve_whitespace: bool = False,
) -> list[str]:
    text = sanitize_text(text)
    if not text:
        return [""]
    avg_width = font_size * (0.60 if mono else 0.53)
    max_chars = max(10, int(max_width / avg_width))
    if preserve_whitespace:
        text = text.replace("\t", "    ")
        if len(text) <= max_chars:
            return [text]
        lines: list[str] = []
        remaining = text
        while len(remaining) > max_chars:
            lines.append(remaining[:max_chars])
            remaining = remaining[max_chars:]
        lines.append(remaining)
        return lines
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


@dataclass
class RenderProfile:
    left: float = LEFT
    right: float = RIGHT
    top_start: float = TOP_START
    bottom_guard: float = BOTTOM_GUARD
    body_line_height: float = BODY_LINE_HEIGHT
    primary_orange: tuple[float, float, float] = PRIMARY_ORANGE
    title_font: str = "F2"
    title_size: float = 24.0
    subtitle_font: str = "F2"
    subtitle_size: float = 14.0
    heading_font: str = "F2"
    heading_size: float = 13.0
    body_font: str = "F1"
    body_size: float = 10.5
    code_font: str = "F3"
    code_size: float = 8.2
    footer_font: str = "F1"
    footer_size: float = 9.0
    footer_left_text: str = "Neurolabs - Confidential Partner Documentation"
    footer_right_prefix: str = "Neurolabs SDK - Page "
    bullet_glyph: str = "-"
    heading_height: float = 22.0
    heading_gap: float = 4.0
    paragraph_gap: float = 6.0
    bullet_gap: float = 4.0
    post_code_gap: float = 12.0
    post_code_heading_extra_gap: float = 12.0


def _font_token_from_name(name: str, fallback: str) -> str:
    lowered = name.lower()
    if "courier" in lowered:
        return "F3"
    if "bold" in lowered:
        return "F2"
    if "helvetica" in lowered:
        return "F1"
    return fallback


def _extract_float(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _extract_text(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def parse_rules_profile(rules_path: Path | None) -> RenderProfile:
    profile = RenderProfile()
    if rules_path is None or not rules_path.exists():
        return profile

    rules = rules_path.read_text()

    profile.left = _extract_float(rules, r"Left margin:\s*`([0-9.]+)`") or profile.left
    profile.right = _extract_float(rules, r"Right margin:\s*`([0-9.]+)`") or profile.right
    top_expr = _extract_text(rules, r"Top content start:\s*`([^`]+)`")
    if top_expr:
        expr = top_expr.strip()
        m = re.search(r"PAGE_HEIGHT\s*-\s*([0-9.]+)", expr, flags=re.IGNORECASE)
        if m:
            profile.top_start = PAGE_HEIGHT - float(m.group(1))
        else:
            numeric = _extract_float(expr, r"([0-9.]+)")
            if numeric is not None:
                profile.top_start = numeric
    profile.bottom_guard = _extract_float(rules, r"Bottom guard area:\s*`([0-9.]+)`") or profile.bottom_guard
    profile.body_line_height = _extract_float(rules, r"Body line height:\s*`([0-9.]+)`") or profile.body_line_height

    title_font_name = _extract_text(rules, r"Title font:\s*`([^`]+)`")
    subtitle_font_name = _extract_text(rules, r"Subtitle font:\s*`([^`]+)`")
    heading_font_name = _extract_text(rules, r"Section heading font.*:\s*`([^`]+)`")
    body_font_name = _extract_text(rules, r"Body font:\s*`([^`]+)`")
    code_font_name = _extract_text(rules, r"Code font:\s*`([^`]+)`")
    footer_font_name = _extract_text(rules, r"Footer font:\s*`([^`]+)`")

    if title_font_name:
        profile.title_font = _font_token_from_name(title_font_name, profile.title_font)
    if subtitle_font_name:
        profile.subtitle_font = _font_token_from_name(subtitle_font_name, profile.subtitle_font)
    if heading_font_name:
        profile.heading_font = _font_token_from_name(heading_font_name, profile.heading_font)
    if body_font_name:
        profile.body_font = _font_token_from_name(body_font_name, profile.body_font)
    if code_font_name:
        profile.code_font = _font_token_from_name(code_font_name, profile.code_font)
    if footer_font_name:
        profile.footer_font = _font_token_from_name(footer_font_name, profile.footer_font)

    profile.title_size = _extract_float(rules, r"Title font:.*size\s*`([0-9.]+)`") or profile.title_size
    profile.subtitle_size = _extract_float(rules, r"Subtitle font:.*size\s*`([0-9.]+)`") or profile.subtitle_size
    profile.heading_size = _extract_float(rules, r"Section heading font.*size\s*`([0-9.]+)`") or profile.heading_size
    profile.body_size = _extract_float(rules, r"Body font:.*size\s*`([0-9.]+)`") or profile.body_size
    profile.code_size = _extract_float(rules, r"Code font:.*size\s*`([0-9.]+)`") or profile.code_size
    profile.footer_size = _extract_float(rules, r"Footer font:.*size\s*`([0-9.]+)`") or profile.footer_size
    profile.post_code_gap = _extract_float(rules, r"Space after code block before next content:\s*`([0-9.]+)`") or profile.post_code_gap
    profile.post_code_heading_extra_gap = (
        _extract_float(rules, r"Extra space when code block is followed by heading:\s*`([0-9.]+)`")
        or profile.post_code_heading_extra_gap
    )

    rgb = re.search(r"RGB float:\s*`\(([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\)`", rules, flags=re.IGNORECASE)
    if rgb:
        profile.primary_orange = (float(rgb.group(1)), float(rgb.group(2)), float(rgb.group(3)))

    left_footer = _extract_text(rules, r"Left footer text:\s*`([^`]+)`")
    right_footer = _extract_text(rules, r"Right footer text:\s*`([^`]+)`")
    if left_footer:
        profile.footer_left_text = left_footer
    if right_footer:
        # Rules include a concrete placeholder like "... Page N"; convert to a prefix
        # without destroying legitimate "N" characters in words.
        cleaned = re.sub(r"\s*N\s*$", "", right_footer).rstrip()
        if not cleaned:
            cleaned = "Neurolabs SDK - Page"
        if not cleaned.endswith(" "):
            cleaned += " "
        profile.footer_right_prefix = cleaned
    return profile


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


def block_render_height(kind: str, payload: object, content_width: float, profile: RenderProfile) -> float:
    if kind == "heading":
        return profile.heading_height
    if kind == "paragraph":
        lines = wrap_text(str(payload), content_width, profile.body_size)
        return len(lines) * profile.body_line_height + profile.paragraph_gap
    if kind == "bullet":
        lines = wrap_text(str(payload), content_width - 14, profile.body_size)
        return len(lines) * profile.body_line_height + profile.bullet_gap
    if kind == "code":
        code = payload  # type: ignore[assignment]
        code_lines = code["lines"] or [""]
        wrapped: list[str] = []
        for line in code_lines:
            wrapped.extend(
                wrap_text(
                    line or " ",
                    content_width - 20,
                    profile.code_size,
                    mono=True,
                    preserve_whitespace=True,
                )
            )
        block_height = max(1, len(wrapped)) * 11 + 18
        return block_height + profile.post_code_gap
    return profile.body_line_height


def draw_footer(builder: PDFBuilder, page_number: int, profile: RenderProfile) -> None:
    builder.set_stroke(*profile.primary_orange)
    builder.line(profile.left, 43.93701, PAGE_WIDTH - profile.right, 43.93701)
    builder.text(profile.left, 28, profile.footer_left_text, profile.footer_font, profile.footer_size)
    page_prefix = profile.footer_right_prefix.rstrip()
    builder.text(
        PAGE_WIDTH - profile.right - 115,
        28,
        f"{page_prefix} {page_number}",
        profile.footer_font,
        profile.footer_size,
    )


def render(
    markdown_path: Path,
    output_path: Path,
    title: str,
    document_id: str,
    version: str,
    date: str,
    rules_path: Path | None = None,
) -> None:
    profile = parse_rules_profile(rules_path)
    builder = PDFBuilder()

    def start_page(page_number: int) -> float:
        draw_footer(builder, page_number, profile)
        builder.set_fill(0.0, 0.0, 0.0)
        return profile.top_start

    y = start_page(1)
    builder.set_fill(*profile.primary_orange)
    builder.text(profile.left, y, title, profile.title_font, profile.title_size)
    builder.set_fill(0.0, 0.0, 0.0)
    y -= 28
    builder.text(profile.left, y, "Technical Integration Specification", profile.subtitle_font, profile.subtitle_size)
    y -= 24
    for meta in [
        f"Document ID: {document_id}",
        f"Version: {version}",
        f"Date: {date}",
        "Status: Partner integration reference",
        "Owner: Neurolabs",
    ]:
        builder.text(profile.left, y, meta, profile.body_font, profile.body_size)
        y -= profile.body_line_height
    y -= 10

    page_number = 1
    blocks = parse_blocks(markdown_path.read_text())
    content_width = PAGE_WIDTH - profile.left - profile.right

    for index, (kind, payload) in enumerate(blocks):
        if kind == "heading":
            heading = str(payload)
            next_block_height = 0.0
            if index + 1 < len(blocks):
                next_kind, next_payload = blocks[index + 1]
                next_block_height = block_render_height(next_kind, next_payload, content_width, profile)
            # Keep headings with the beginning of the next block so headings are never
            # stranded as the last line on a page.
            needed = profile.heading_height + profile.heading_gap + next_block_height
            if y - needed < profile.bottom_guard:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            builder.text(profile.left, y, heading, profile.heading_font, profile.heading_size)
            y -= profile.heading_height
            continue

        if kind == "paragraph":
            lines = wrap_text(str(payload), content_width, profile.body_size)
            needed = len(lines) * profile.body_line_height + profile.paragraph_gap
            if y - needed < profile.bottom_guard:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            for line in lines:
                builder.text(profile.left, y, line, profile.body_font, profile.body_size)
                y -= profile.body_line_height
            y -= profile.paragraph_gap
            continue

        if kind == "bullet":
            text = str(payload)
            bullet_indent = 14
            lines = wrap_text(text, content_width - bullet_indent, profile.body_size)
            needed = len(lines) * profile.body_line_height + profile.bullet_gap
            if y - needed < profile.bottom_guard:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            builder.text(profile.left, y, profile.bullet_glyph, profile.body_font, profile.body_size)
            builder.text(profile.left + bullet_indent, y, lines[0], profile.body_font, profile.body_size)
            y -= profile.body_line_height
            for line in lines[1:]:
                builder.text(profile.left + bullet_indent, y, line, profile.body_font, profile.body_size)
                y -= profile.body_line_height
            y -= profile.bullet_gap
            continue

        if kind == "code":
            code = payload  # type: ignore[assignment]
            code_lines = code["lines"] or [""]
            wrapped: list[str] = []
            for line in code_lines:
                wrapped.extend(
                    wrap_text(
                        line or " ",
                        content_width - 20,
                        profile.code_size,
                        mono=True,
                        preserve_whitespace=True,
                    )
                )
            block_height = max(1, len(wrapped)) * 11 + 18
            if y - block_height < profile.bottom_guard:
                builder.new_page()
                page_number += 1
                y = start_page(page_number)
            box_y = y - block_height + 10
            builder.set_stroke(*profile.primary_orange)
            builder.rect(profile.left, box_y, content_width, block_height)
            inner_y = y - 12
            for line in wrapped:
                builder.text(profile.left + 10, inner_y, line, profile.code_font, profile.code_size)
                inner_y -= 11
            next_kind = blocks[index + 1][0] if index + 1 < len(blocks) else None
            extra_gap = profile.post_code_heading_extra_gap if next_kind == "heading" else 0.0
            y = box_y - profile.post_code_gap - extra_gap

    builder.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--rules", required=False)
    args = parser.parse_args()

    render(
        markdown_path=Path(args.source),
        output_path=Path(args.output),
        title=args.title,
        document_id=args.document_id,
        version=args.version,
        date=args.date,
        rules_path=Path(args.rules).resolve() if args.rules else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
