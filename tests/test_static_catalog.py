import json
from html.parser import HTMLParser

from foundry_showcase.models import Catalog
from foundry_showcase.settings import DEFAULT_CATALOG_PATH, REPOSITORY_ROOT


class MicrositeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.catalog_parts: list[str] = []
        self.external_assets: list[str] = []
        self.in_catalog = False
        self.architecture_parts: list[str] = []
        self.in_architecture = False
        self.title_parts: list[str] = []
        self.in_title = False
        self.elements: dict[str, tuple[str, dict[str, str | None]]] = {}
        self.header_links: list[str | None] = []
        self.drawer_links: list[str | None] = []
        self.in_header = False
        self.in_drawer = False
        self.in_drawer_nav = False
        self.theme_in_drawer = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.elements[element_id] = (tag, attributes)
        if tag == "header":
            self.in_header = True
        if tag == "dialog":
            self.in_drawer = element_id == "navigation-drawer"
        if tag == "nav":
            self.in_drawer_nav = self.in_drawer
        if tag == "a":
            if self.in_header:
                self.header_links.append(attributes.get("href"))
            if self.in_drawer_nav:
                self.drawer_links.append(attributes.get("href"))
        if element_id == "theme-toggle":
            self.theme_in_drawer = self.in_drawer
        if tag == "script":
            self.in_catalog = attributes.get("id") == "catalog-data"
            self.in_architecture = attributes.get("id") == "architecture-data"
        if tag == "title":
            self.in_title = True
        if tag in {"script", "img", "iframe", "audio", "video", "source"}:
            source = attributes.get("src")
            if source:
                self.external_assets.append(source)
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.external_assets.append(attributes.get("href") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.in_catalog = False
            self.in_architecture = False
        if tag == "title":
            self.in_title = False
        if tag == "header":
            self.in_header = False
        if tag == "dialog":
            self.in_drawer = False
        if tag == "nav":
            self.in_drawer_nav = False

    def handle_data(self, data: str) -> None:
        if self.in_catalog:
            self.catalog_parts.append(data)
        if self.in_architecture:
            self.architecture_parts.append(data)
        if self.in_title:
            self.title_parts.append(data)


def test_self_contained_snapshot_matches_the_canonical_registry() -> None:
    parser = MicrositeParser()
    parser.feed((REPOSITORY_ROOT / "docs" / "index.html").read_text(encoding="utf-8"))
    snapshot = "".join(parser.catalog_parts)
    assert json.loads(snapshot) == json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
    assert Catalog.model_validate_json(snapshot).live_demos_enabled is False
    assert parser.external_assets == []


def test_navigation_is_contained_in_an_accessible_modal_drawer() -> None:
    parser = MicrositeParser()
    parser.feed((REPOSITORY_ROOT / "docs" / "index.html").read_text(encoding="utf-8"))

    toggle_tag, toggle = parser.elements["navigation-toggle"]
    assert toggle_tag == "button"
    assert toggle["type"] == "button"
    assert toggle["aria-label"] == "Open navigation"
    assert toggle["aria-haspopup"] == "dialog"
    assert toggle["aria-controls"] == "navigation-drawer"
    assert toggle["aria-expanded"] == "false"

    drawer_tag, drawer = parser.elements["navigation-drawer"]
    assert drawer_tag == "dialog"
    assert "open" not in drawer
    assert drawer["aria-labelledby"] == "navigation-title"
    assert parser.elements["navigation-title"][0] == "h2"
    assert "autofocus" in parser.elements["close-navigation"][1]
    assert parser.header_links == ["#main"]
    assert parser.drawer_links == ["#main", "#journeys", "#architecture", "#catalog", "#brief", "#boundaries"]
    assert parser.theme_in_drawer is True
    for destination in parser.drawer_links:
        assert destination is not None
        assert parser.elements[destination.removeprefix("#")][1]["tabindex"] == "-1"


def test_requested_site_title_and_verified_atlas_snapshot() -> None:
    parser = MicrositeParser()
    parser.feed((REPOSITORY_ROOT / "docs" / "index.html").read_text(encoding="utf-8"))
    assert "".join(parser.title_parts) == "Azure Foundry IRL"
    assert json.loads("".join(parser.catalog_parts))["title"].startswith("Azure Foundry IRL")
    atlas = json.loads("".join(parser.architecture_parts))
    canonical = json.loads((REPOSITORY_ROOT / "data" / "architecture-atlas.json").read_text(encoding="utf-8"))
    assert atlas["schema_version"] == 1
    assert atlas["sources"] == canonical["sources"]
    assert len(atlas["diagrams"]) == 6
    assert {diagram["id"] for diagram in atlas["diagrams"]} == {diagram["id"] for diagram in canonical["diagrams"]}
    assert atlas["checked_date"]
    assert parser.elements["architecture-dialog"][0] == "dialog"
    for diagram in atlas["diagrams"]:
        assert diagram["svg"].startswith("<svg")
        for field in ("svg_path", "editable_path"):
            assert (REPOSITORY_ROOT / "docs" / diagram[field]).is_file()
