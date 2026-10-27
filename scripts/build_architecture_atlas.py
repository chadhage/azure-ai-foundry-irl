from __future__ import annotations

import argparse
import base64
import hashlib
import html
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
import textwrap
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile

from pydantic import BaseModel, ConfigDict, Field, model_validator


ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "data" / "architecture-atlas.json"
ASSETS = ROOT / "docs" / "assets"
VERIFICATION = ASSETS / "architecture-verification.json"
ICONS = ASSETS / "icons"
DIAGRAMS = ASSETS / "diagrams"
START = '<script id="architecture-data" type="application/json">'
END = "</script>"
PALETTE = {
    "bg": "#f7f4ef", "surface": "#ffffff", "border": "#919191",
    "text": "#242424", "text-muted": "#5c5c5c", "text-soft": "#6f6f6f", "accent": "#b11f4b",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(StrictModel):
    id: str
    title: str
    url: str
    terms: list[str] = Field(min_length=1)
    supports: str


class Package(StrictModel):
    id: str
    filename: str
    url: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    terms_source: str


class Icon(StrictModel):
    id: str
    package: str
    entry: str


class Node(StrictModel):
    id: str
    label: str
    detail: str
    box: tuple[float, float, float, float]
    icon: str | None = None


class Group(StrictModel):
    label: str
    box: tuple[float, float, float, float]


class Edge(StrictModel):
    points: list[tuple[float, float]] = Field(min_length=2)
    label: str
    label_at: tuple[float, float]
    dashed: bool = False


class Message(StrictModel):
    from_id: str
    to_id: str
    label: str
    dashed: bool = False


class Step(StrictModel):
    text: str
    sources: list[str] = Field(min_length=1)


class Diagram(StrictModel):
    id: str
    title: str
    kind: Literal["topology", "sequence", "ontology", "data-quality"]
    profile: str
    width: int = Field(ge=1000)
    height: int = Field(ge=600)
    summary: str
    boundary: str
    sources: list[str] = Field(min_length=1)
    groups: list[Group] = []
    nodes: list[Node] = Field(min_length=1)
    edges: list[Edge] = []
    messages: list[Message] = []
    steps: list[Step] = Field(min_length=1)
    decisions: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)


class Atlas(StrictModel):
    schema_version: Literal[1]
    notice: str
    sources: list[Source]
    packages: list[Package]
    icons: list[Icon]
    diagrams: list[Diagram]
    ontology_example: dict[str, object]

    @model_validator(mode="after")
    def validate_references(self) -> Atlas:
        for collection in (self.sources, self.packages, self.icons, self.diagrams):
            ids = [item.id for item in collection]
            if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", value) for value in ids):
                raise ValueError("Atlas identifiers must be unique and safe.")
        sources = {item.id for item in self.sources}
        packages = {item.id for item in self.packages}
        icons = {item.id for item in self.icons}
        for source in self.sources:
            if urlparse(source.url).hostname != "learn.microsoft.com":
                raise ValueError("Architecture citations must be public Microsoft Learn pages.")
        for package in self.packages:
            if package.terms_source not in sources:
                raise ValueError("Icon package has no verified terms source.")
        for icon in self.icons:
            if icon.package not in packages:
                raise ValueError("Icon package reference is missing.")
        for diagram in self.diagrams:
            if not set(diagram.sources) <= sources:
                raise ValueError("Diagram has an unknown citation.")
            node_ids = {node.id for node in diagram.nodes}
            if len(node_ids) != len(diagram.nodes):
                raise ValueError("Duplicate diagram node.")
            for step in diagram.steps:
                if not set(step.sources) <= set(diagram.sources):
                    raise ValueError("Step citations must belong to its diagram.")
            for node in diagram.nodes:
                x, y, width, height = node.box
                if min(x, y) < 0 or min(width, height) <= 0 or x + width > diagram.width or y + height > diagram.height - 70:
                    raise ValueError("Diagram node is outside its canvas.")
                if node.icon and node.icon not in icons:
                    raise ValueError("Diagram uses an unknown icon.")
            for message in diagram.messages:
                if message.from_id not in node_ids or message.to_id not in node_ids:
                    raise ValueError("Sequence participant reference is missing.")
        return self


class PageText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.parts.extend(value for name, value in attrs if name == "href" and value)


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2) + "\n"


def svg_dimensions(content: bytes) -> tuple[float, float]:
    attributes = ET.fromstring(content).attrib
    if "viewBox" in attributes:
        _, _, width, height = (float(value) for value in re.split(r"[\s,]+", attributes["viewBox"].strip()))
    else:
        width, height = float(attributes["width"]), float(attributes["height"])
    if min(width, height) <= 0:
        raise ValueError("Official icon has invalid dimensions.")
    return width, height


def fetch_bytes(url: str) -> tuple[bytes, str, int]:
    request = Request(url, headers={"User-Agent": "AzureFoundryIRL-ArchitectureVerifier/1.0", "Accept": "text/html,application/zip"})
    with urlopen(request, timeout=40) as response:
        return response.read(), response.url, response.status


def verify_sources(atlas: Atlas) -> None:
    records: list[dict[str, object]] = []
    for source in atlas.sources:
        content, final_url, status = fetch_bytes(source.url)
        if status != 200 or urlparse(final_url).hostname != "learn.microsoft.com":
            raise ValueError(f"{source.id}: source is not an accessible Microsoft Learn page.")
        parser = PageText()
        parser.feed(content.decode("utf-8-sig"))
        normalized = " ".join(html.unescape(" ".join(parser.parts)).split()).casefold()
        missing = [term for term in source.terms if " ".join(term.split()).casefold() not in normalized]
        if missing:
            raise ValueError(f"{source.id}: expected evidence changed: {missing}")
        records.append({
            "id": source.id, "url": source.url, "resolved_url": final_url,
            "status": status, "sha256": hashlib.sha256(content).hexdigest(),
            "checked_terms": source.terms,
        })
        print(f"Verified {source.id}: {source.title}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    VERIFICATION.write_text(json_text({
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Public documentation HTTP accessibility and evidence-term checks, plus human source review. Not a cloud/runtime certification.",
        "sources": records,
    }), encoding="utf-8")


def import_icons(atlas: Atlas, cache: Path | None) -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    provenance: list[dict[str, str]] = []
    for package in atlas.packages:
        cached = cache / package.filename if cache else None
        payload = cached.read_bytes() if cached else fetch_bytes(package.url)[0]
        if hashlib.sha256(payload).hexdigest() != package.sha256:
            raise ValueError(f"Official archive digest changed: {package.id}. Review before importing.")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for icon in (item for item in atlas.icons if item.package == package.id):
                content = archive.read(icon.entry)
                root = ET.fromstring(content)
                if root.tag != "{http://www.w3.org/2000/svg}svg":
                    raise ValueError(f"Not an SVG icon: {icon.id}")
                if any(element.tag.rsplit("}", 1)[-1] in {"script", "foreignObject"} for element in root.iter()):
                    raise ValueError(f"Unexpected active SVG content: {icon.id}")
                filename = f"{icon.id}.svg"
                (ICONS / filename).write_bytes(content)
                provenance.append({
                    "id": icon.id, "file": filename, "package": package.id,
                    "archive_entry": icon.entry, "sha256": hashlib.sha256(content).hexdigest(),
                })
    (ICONS / "provenance.json").write_text(json_text({"icons": provenance}), encoding="utf-8")


class Drawing:
    def __init__(self, diagram: Diagram, icons: dict[str, bytes]) -> None:
        self.diagram = diagram
        self.icons = icons
        self.svg_parts: list[str] = []
        self.elements: list[dict[str, object]] = []
        self.files: dict[str, dict[str, object]] = {}

    def item(self, kind: str, x: float, y: float, width: float, height: float, **fields: object) -> None:
        index = len(self.elements) + 1
        self.elements.append({
            "id": f"{self.diagram.id}-{index}", "type": kind, "x": x, "y": y,
            "width": width, "height": height, "angle": 0, "strokeColor": PALETTE["border"],
            "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 1,
            "strokeStyle": "solid", "roughness": 0, "opacity": 100, "groupIds": [],
            "frameId": None, "seed": index, "version": 1, "versionNonce": 0,
            "isDeleted": False, "boundElements": None, "updated": 0, "link": None,
            "locked": False, **fields,
        })

    def text(self, value: str, x: float, y: float, width: float, size: int = 18, muted: bool = False, centered: bool = False) -> int:
        lines: list[str] = []
        columns = max(8, int(width / (size * 0.58)))
        for paragraph in value.split("\n"):
            lines.extend(textwrap.wrap(paragraph, columns, break_long_words=False) or [""])
        color = "text-soft" if muted else "text"
        anchor = ' text-anchor="middle"' if centered else ""
        svg_x = x + width / 2 if centered else x
        spans = "".join(f'<tspan x="{svg_x:g}" dy="{0 if index == 0 else size * 1.35:g}">{html.escape(line)}</tspan>' for index, line in enumerate(lines))
        self.svg_parts.append(f'<text x="{svg_x:g}" y="{y + size:g}" font-size="{size}" fill="var(--cp-{color})"{anchor}>{spans}</text>')
        self.item("text", x, y, width, size * 2.5 * len(lines), text="\n".join(lines),
                  originalText="\n".join(lines), fontSize=size, fontFamily=2,
                  textAlign="center" if centered else "left", verticalAlign="top",
                  strokeColor="#000000", containerId=None, autoResize=False, lineHeight=1.35)
        return len(lines)

    def rect(self, box: tuple[float, float, float, float], group: bool = False) -> None:
        x, y, width, height = box
        fill = "none" if group else "var(--cp-surface)"
        dash = ' stroke-dasharray="7 5"' if group else ""
        self.svg_parts.append(f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="10" fill="{fill}" stroke="var(--cp-border)"{dash}/>')
        self.item("rectangle", x, y, width, height, roundness={"type": 3},
                  backgroundColor="transparent" if group else PALETTE["surface"],
                  strokeStyle="dashed" if group else "solid")

    def icon(self, icon_id: str, x: float, y: float, size: float = 44) -> None:
        content = self.icons[icon_id]
        original_width, original_height = svg_dimensions(content)
        scale = size / max(original_width, original_height)
        width, height = original_width * scale, original_height * scale
        x, y = x + (size - width) / 2, y + (size - height) / 2
        data_url = "data:image/svg+xml;base64," + base64.b64encode(content).decode("ascii")
        self.svg_parts.append(f'<image x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" preserveAspectRatio="xMidYMid meet" href="{data_url}"/>')
        file_id = hashlib.sha256(content).hexdigest()[:32]
        self.files[file_id] = {"id": file_id, "mimeType": "image/svg+xml", "dataURL": data_url, "created": 0}
        self.item("image", x, y, width, height, fileId=file_id, status="saved", scale=[1, 1], crop=None)

    def edge_label(self, edge: Edge) -> None:
        lines = textwrap.wrap(edge.label, int(240 / (14 * 0.58)), break_long_words=False)
        width = min(240, max(len(line) for line in lines) * 14 * 0.58 + 16)
        height = 14 * (1 + 1.35 * (len(lines) - 1)) + 8
        x, y = edge.label_at[0] - width / 2, edge.label_at[1] - 9
        self.svg_parts.append(f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="4" fill="var(--cp-bg)"/>')
        self.item("rectangle", x, y, width, height, backgroundColor=PALETTE["bg"], strokeColor=PALETTE["bg"])
        self.text(edge.label, edge.label_at[0] - 120, edge.label_at[1] - 8, 240, 14, muted=True, centered=True)

    def line(self, points: list[tuple[float, float]], dashed: bool = False, arrow: bool = True) -> None:
        svg_points = " ".join(f"{x:g},{y:g}" for x, y in points)
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        marker = f' marker-end="url(#{self.diagram.id}-arrow)"' if arrow else ""
        self.svg_parts.append(f'<polyline points="{svg_points}" fill="none" stroke="var(--cp-accent)" stroke-width="2"{dash}{marker}/>')
        start_x, start_y = points[0]
        relative = [[x - start_x, y - start_y] for x, y in points]
        self.item("arrow" if arrow else "line", start_x, start_y,
                  max(x for x, _ in points) - min(x for x, _ in points),
                  max(y for _, y in points) - min(y for _, y in points),
                  points=relative, strokeColor=PALETTE["accent"], strokeWidth=2,
                  strokeStyle="dashed" if dashed else "solid", startArrowhead=None,
                  endArrowhead="arrow" if arrow else None, startBinding=None, endBinding=None)

    def render(self) -> None:
        diagram = self.diagram
        self.text(diagram.title, 32, 24, diagram.width - 64, 28)
        self.text(diagram.profile + " | REFERENCE DESIGN - NOT DEPLOYED", 32, 72, diagram.width - 64, 16, muted=True)
        for group in diagram.groups:
            self.rect(group.box, group=True)
            self.text(group.label, group.box[0] + 16, group.box[1] + 14, group.box[2] - 32, 17, muted=True)
        if diagram.kind == "sequence":
            for node in diagram.nodes:
                center = node.box[0] + node.box[2] / 2
                self.line([(center, node.box[1] + node.box[3]), (center, diagram.height - 88)], dashed=True, arrow=False)
            centers = {node.id: node.box[0] + node.box[2] / 2 for node in diagram.nodes}
            for index, message in enumerate(diagram.messages):
                start, end = centers[message.from_id], centers[message.to_id]
                y = 302 + index * 56
                self.line([(start, y), (end, y)], dashed=message.dashed)
                self.text(message.label, min(start, end) + 10, y - 44, abs(end - start) - 20, 15, centered=True)
        else:
            for edge in diagram.edges:
                self.line(edge.points, dashed=edge.dashed)
            for edge in diagram.edges:
                self.edge_label(edge)
        for node in diagram.nodes:
            self.svg_parts.append(f'<g data-node-id="{node.id}">')
            self.rect(node.box)
            x, y, width, height = node.box
            offset = 16
            if node.icon:
                self.icon(node.icon, x + 16, y + 18, 40)
                offset = 72
            title_size = 16 if width < 260 else 18
            title_lines = self.text(node.label, x + offset, y + 14, width - offset - 12, title_size)
            detail_y = max(68 if node.icon else 50, 14 + title_lines * title_size * 1.35 + 10)
            detail_size = 14 if width < 260 else 15
            detail_lines = self.text(node.detail, x + 16, y + detail_y, width - 32, detail_size, muted=True)
            if detail_y + detail_size * (1 + 1.35 * (detail_lines - 1)) > height - 6:
                raise ValueError(f"Node text exceeds its box: {diagram.id}/{node.id}")
            self.svg_parts.append("</g>")
        self.text("Solid: primary flow / semantic relationship    Dashed: supporting evidence, control or return", 32, diagram.height - 60, diagram.width - 64, 15, muted=True)
        self.text("Public Microsoft sources: " + ", ".join(diagram.sources) + " | See companion documentation for scope and exclusions.", 32, diagram.height - 34, diagram.width - 64, 14, muted=True)

    def svg(self, standalone: bool = False) -> str:
        diagram = self.diagram
        style = ""
        if standalone:
            variables = ";".join(f"--cp-{key}:{value}" for key, value in PALETTE.items())
            dark = "--cp-bg:#3d3b3a;--cp-surface:#292929;--cp-border:#919191;--cp-text:#dedede;--cp-text-muted:#b0b0b0;--cp-text-soft:#b0b0b0;--cp-accent:#fd8ea1"
            style = f"<style>:root{{{variables}}}@media(prefers-color-scheme:dark){{:root{{{dark}}}}}</style>"
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {diagram.width} {diagram.height}" '
            f'role="img" aria-labelledby="{diagram.id}-title {diagram.id}-description" '
            'style="font-family:Segoe UI,Aptos,Calibri,sans-serif">'
            f'<title id="{diagram.id}-title">{html.escape(diagram.title)}</title>'
            f'<desc id="{diagram.id}-description">{html.escape(diagram.summary + " " + diagram.boundary)}</desc>{style}'
            f'<defs><marker id="{diagram.id}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="var(--cp-accent)"/></marker></defs>'
            f'<rect width="{diagram.width}" height="{diagram.height}" fill="var(--cp-bg)"/>'
            + "".join(self.svg_parts) + "</svg>"
        )

    def excalidraw(self) -> str:
        return json_text({
            "type": "excalidraw", "version": 2, "source": "Azure Foundry IRL",
            "elements": self.elements, "files": self.files,
            "appState": {"viewBackgroundColor": PALETTE["bg"], "gridSize": None},
        })


def build_outputs(atlas: Atlas) -> dict[Path, str]:
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    verified = {item["id"] for item in verification["sources"] if item["status"] == 200}
    if verified != {source.id for source in atlas.sources}:
        raise ValueError("Source evidence is missing. Run --verify-sources.")
    evidence = {item["id"]: item for item in verification["sources"]}
    if any(evidence[source.id]["url"] != source.url or evidence[source.id]["checked_terms"] != source.terms for source in atlas.sources):
        raise ValueError("Source definitions changed. Run --verify-sources.")
    provenance = json.loads((ICONS / "provenance.json").read_text(encoding="utf-8"))
    icon_hashes = {item["id"]: item["sha256"] for item in provenance["icons"]}
    icons = {icon.id: (ICONS / f"{icon.id}.svg").read_bytes() for icon in atlas.icons}
    for icon_id, content in icons.items():
        if hashlib.sha256(content).hexdigest() != icon_hashes.get(icon_id):
            raise ValueError(f"Official icon changed: {icon_id}")
    checked = str(verification["checked_utc"])[:10]
    sources = {source.id: source for source in atlas.sources}
    payload: dict[str, object] = {
        "schema_version": 1, "notice": atlas.notice, "checked_date": checked,
        "sources": [source.model_dump() for source in atlas.sources], "diagrams": [],
    }
    rendered: list[dict[str, object]] = []
    outputs: dict[Path, str] = {}
    docs = [
        "# Azure Foundry IRL: reference architecture atlas", "",
        atlas.notice, "", f"Source review and automated public-page checks: **{checked}**.", "",
        "These are original adaptations, not Microsoft-endorsed diagrams. Official Microsoft artwork is used only to label its products; generic business/application nodes have no Microsoft logo.",
        "", "## Reading the diagrams", "",
        "Solid arrows show primary flow or a semantic relationship. Dashed arrows show supporting evidence, control, returns or sequence lifelines. Frames are logical boundaries, not claims about physical resource placement.",
        "", "Each SVG is self-contained, and each editable Excalidraw source embeds the same unmodified icon bytes. The microsite embeds its diagrams so viewing never requires a CDN, remote renderer or Azure credentials.",
        "",
    ]
    for diagram in atlas.diagrams:
        drawing = Drawing(diagram, icons)
        drawing.render()
        outputs[DIAGRAMS / f"{diagram.id}.svg"] = drawing.svg(standalone=True) + "\n"
        outputs[DIAGRAMS / f"{diagram.id}.excalidraw"] = drawing.excalidraw()
        entry = diagram.model_dump(exclude={"groups", "nodes", "edges", "messages", "width", "height"})
        entry.update({"svg": drawing.svg(), "svg_path": f"assets/diagrams/{diagram.id}.svg", "editable_path": f"assets/diagrams/{diagram.id}.excalidraw"})
        rendered.append(entry)
        docs.extend([
            f"## {diagram.title}", "", f"**Profile:** {diagram.profile}. **Deployment:** not deployed.", "",
            diagram.summary, "", f"![{diagram.title}](assets/diagrams/{diagram.id}.svg)", "",
            f"[SVG](assets/diagrams/{diagram.id}.svg) | [Editable Excalidraw](assets/diagrams/{diagram.id}.excalidraw)", "",
            f"**Boundary:** {diagram.boundary}", "", "### Flow and source mapping", "",
        ])
        for index, step in enumerate(diagram.steps, 1):
            citations = ", ".join(f"[{source_id}]({sources[source_id].url})" for source_id in step.sources)
            docs.append(f"{index}. {step.text} ({citations})")
        docs.extend(["", "### Design decisions", ""] + [f"- {value}" for value in diagram.decisions])
        docs.extend(["", "### Limitations and activation gates", ""] + [f"- {value}" for value in diagram.limitations] + [""])
    payload["diagrams"] = rendered
    outputs[ROOT / "docs" / "reference-architectures.md"] = "\n".join(docs).rstrip() + "\n"
    outputs[ASSETS / "ontology-example.json"] = json_text(atlas.ontology_example)
    source_docs = [
        "# Architecture source and verification register", "", atlas.notice, "",
        f"Last successful public-source verification: **{verification['checked_utc']}**.", "",
        "Verification means public HTTP 200 responses, expected evidence terms, manual review of the cited claims, and checked icon provenance. It does not mean implementation, deployment, regional entitlement or Microsoft certification.",
        "", "A page may change after this review. Re-run the online verifier before relying on an activation-sensitive claim. Content hashes describe the fetched page at review time, not an immutable documentation release.",
        "", "| ID | Official public source | Claim boundary |", "|---|---|---|",
    ]
    source_docs.extend(f"| {source.id} | [{source.title}]({source.url}) | {source.supports} |" for source in atlas.sources)
    source_docs.extend(["", "## Reproduce", "", "```powershell", r".\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --verify-sources",
                        r".\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --check", "```", "",
                        "The first command performs public HTTP requests and rebuilds artifacts only after all checks pass. The second is deterministic and offline. Review source meaning manually after product changes; term matching is not a substitute for architectural review.",
                        "", "See [icon terms and provenance](assets/icons/NOTICE.md) and [machine-readable verification](assets/architecture-verification.json).", ""])
    outputs[ROOT / "docs" / "architecture-sources.md"] = "\n".join(source_docs)
    page_path = ROOT / "docs" / "index.html"
    page = page_path.read_text(encoding="utf-8")
    if page.count(START) != 1:
        raise ValueError("Microsite must contain one architecture-data block.")
    start = page.index(START) + len(START)
    end = page.index(END, start)
    snapshot = json_text(payload).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    outputs[page_path] = page[:start] + "\n" + snapshot + "  " + page[end:]
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the source-grounded, offline architecture atlas.")
    parser.add_argument("--verify-sources", action="store_true", help="Refresh public Microsoft source evidence before building.")
    parser.add_argument("--import-icons", action="store_true", help="Import only selected, digest-checked official icon bytes.")
    parser.add_argument("--icon-cache", type=Path, help="Directory holding the two approved source ZIP files.")
    parser.add_argument("--check", action="store_true", help="Check deterministic output without writing or network requests.")
    args = parser.parse_args()
    if args.check and (args.verify_sources or args.import_icons):
        parser.error("--check cannot refresh sources or import icons.")
    atlas = Atlas.model_validate_json(DEFINITION.read_text(encoding="utf-8"))
    if args.import_icons:
        import_icons(atlas, args.icon_cache)
    if args.verify_sources:
        verify_sources(atlas)
    outputs = build_outputs(atlas)
    mismatches = [path for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.check:
        for path in mismatches:
            print(f"Out of date: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1 if mismatches else 0
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Built {len(atlas.diagrams)} diagrams, editable sources and documentation; no Azure resources or AI calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
