import base64
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from pydantic import ValidationError
import pytest

from scripts.build_architecture_atlas import (
    ASSETS,
    Atlas,
    DEFINITION,
    DIAGRAMS,
    ICONS,
    PageText,
    ROOT,
    VERIFICATION,
    build_outputs,
    svg_dimensions,
)


def load_atlas() -> Atlas:
    return Atlas.model_validate_json(DEFINITION.read_text(encoding="utf-8"))


def test_source_reader_verifies_download_link_destinations() -> None:
    parser = PageText()
    parser.feed('<p>Microsoft permits the use</p><a href="https://github.com/microsoft/fabric-samples/Icons.zip">Download icons</a>')
    evidence = " ".join(parser.parts)
    assert "Microsoft permits the use" in evidence
    assert "Icons.zip" in evidence
    assert "Download icons" in evidence


def test_generated_architecture_artifacts_are_current() -> None:
    for path, content in build_outputs(load_atlas()).items():
        assert path.read_text(encoding="utf-8") == content, f"Regenerate {path.relative_to(ROOT)}"


def test_source_evidence_matches_the_exact_current_citations() -> None:
    atlas = load_atlas()
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    evidence = {entry["id"]: entry for entry in verification["sources"]}
    assert set(evidence) == {source.id for source in atlas.sources}
    for source in atlas.sources:
        entry = evidence[source.id]
        assert entry["status"] == 200
        assert entry["url"] == source.url
        assert entry["checked_terms"] == source.terms
        assert re.fullmatch(r"[a-f0-9]{64}", entry["sha256"])
    assert "Not a cloud/runtime certification" in verification["scope"]


def test_official_icon_files_match_the_provenance_manifest() -> None:
    atlas = load_atlas()
    provenance = json.loads((ICONS / "provenance.json").read_text(encoding="utf-8"))
    records = {record["id"]: record for record in provenance["icons"]}
    assert set(records) == {icon.id for icon in atlas.icons}
    for icon in atlas.icons:
        record = records[icon.id]
        content = (ICONS / record["file"]).read_bytes()
        assert record["archive_entry"] == icon.entry
        assert record["package"] == icon.package
        assert hashlib.sha256(content).hexdigest() == record["sha256"]
        assert ET.fromstring(content).tag == "{http://www.w3.org/2000/svg}svg"


def test_diagram_svg_and_editable_sources_preserve_original_artwork() -> None:
    atlas = load_atlas()
    original = {(ICONS / f"{icon.id}.svg").read_bytes() for icon in atlas.icons}
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for diagram in atlas.diagrams:
        root = ET.parse(DIAGRAMS / f"{diagram.id}.svg").getroot()
        assert root.attrib["role"] == "img"
        assert root.find("svg:title", namespace) is not None
        assert root.find("svg:desc", namespace) is not None
        assert "NOT DEPLOYED" in "".join(root.itertext())
        assert not root.findall(".//svg:script", namespace)
        for image in root.findall(".//svg:image", namespace):
            assert image.attrib["preserveAspectRatio"] == "xMidYMid meet"
            assert image.attrib["href"].startswith("data:image/svg+xml;base64,")
            assert base64.b64decode(image.attrib["href"].split(",", 1)[1]) in original
        editable = json.loads((DIAGRAMS / f"{diagram.id}.excalidraw").read_text(encoding="utf-8"))
        assert editable["type"] == "excalidraw"
        assert editable["version"] == 2
        elements = editable["elements"]
        assert len({element["id"] for element in elements}) == len(elements)
        for element in elements:
            if element["type"] == "text":
                assert element["width"] > 0
                assert element["height"] >= element["fontSize"] * 2.5
                assert element["strokeColor"] == "#000000"
            if element["type"] == "rectangle" and element["strokeStyle"] == "dashed":
                assert element["backgroundColor"] == "transparent"
            if element["type"] == "image":
                image = editable["files"][element["fileId"]]
                assert image["mimeType"] == "image/svg+xml"
                content = base64.b64decode(image["dataURL"].split(",", 1)[1])
                assert content in original
                width, height = svg_dimensions(content)
                assert element["width"] / element["height"] == pytest.approx(width / height)


@pytest.mark.parametrize("change", ["unknown-source", "unknown-icon", "out-of-bounds"])
def test_invalid_diagram_contracts_fail_explicitly(change: str) -> None:
    payload = load_atlas().model_dump()
    diagram = payload["diagrams"][0]
    if change == "unknown-source":
        diagram["sources"].append("UNVERIFIED")
    elif change == "unknown-icon":
        diagram["nodes"][0]["icon"] = "invented-product-icon"
    else:
        diagram["nodes"][0]["box"] = [-1, 0, 100, 100]
    with pytest.raises(ValidationError):
        Atlas.model_validate(payload)


def test_documentation_local_links_and_synthetic_model() -> None:
    paths = [
        ROOT / "docs" / "reference-architectures.md",
        ROOT / "docs" / "architecture-sources.md",
        ROOT / "docs" / "ontology-and-data-quality.md",
        ICONS / "NOTICE.md",
    ]
    for path in paths:
        for destination in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" not in destination and not destination.startswith("#"):
                assert (path.parent / Path(destination)).is_file(), f"{path}: {destination}"
    example = json.loads((ASSETS / "ontology-example.json").read_text(encoding="utf-8"))
    assert example["namespace"] == "demo.commerce"
    assert "not a Fabric import/API schema" in example["format_notice"]
    assert len(example["entities"]) == 4
    assert len(example["relationships"]) == 3
