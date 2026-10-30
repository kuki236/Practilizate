import json
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
POWERBI = REPO_ROOT / "powerbi"
REPORT = POWERBI / "practilizate.Report"
MODEL = POWERBI / "practilizate.SemanticModel"


def test_powerbi_project_is_complete() -> None:
    assert (POWERBI / "practilizate.pbip").is_file()
    assert (REPORT / "definition.pbir").is_file()
    assert (REPORT / "definition" / "report.json").is_file()
    assert (MODEL / "definition.pbism").is_file()
    assert (MODEL / "definition" / "model.tmdl").is_file()
    assert (MODEL / "definition" / "tables" / "Ofertas.tmdl").is_file()
    assert (MODEL / "definition" / "tables" / "Calidad.tmdl").is_file()

    binding = json.loads((REPORT / "definition.pbir").read_text(encoding="utf-8"))
    assert binding["datasetReference"]["byPath"]["path"] == "../practilizate.SemanticModel"

    pages = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))
    assert len(pages["pageOrder"]) == 6
    assert pages["activePageName"] == pages["pageOrder"][0]

    for page_id in pages["pageOrder"]:
        page_dir = REPORT / "definition" / "pages" / page_id
        page = json.loads((page_dir / "page.json").read_text(encoding="utf-8"))
        assert page["displayName"]
        visuals = list((page_dir / "visuals").glob("*/visual.json"))
        assert visuals, page["displayName"]
        for visual_path in visuals:
            visual = json.loads(visual_path.read_text(encoding="utf-8"))
            container = visual.get("visual", {}).get("visualContainerObjects", {})
            general = container.get("general", [])
            assert any("altText" in item.get("properties", {}) for item in general), visual_path

    report = json.loads((REPORT / "definition" / "report.json").read_text(encoding="utf-8"))
    theme_name = report["themeCollection"]["customTheme"]["name"]
    assert theme_name.endswith(".json")
    theme_path = REPORT / "StaticResources" / "RegisteredResources" / theme_name
    assert theme_path.is_file()
    registered = {
        item["name"]: item["path"]
        for package in report["resourcePackages"]
        for item in package["items"]
    }
    assert registered[theme_name] == theme_name

    for screenshot in ("dashboard-es.png", "dashboard-en.png"):
        path = REPO_ROOT / "docs" / "assets" / screenshot
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == (1148, 646)
            assert image.format == "PNG"

    review = (REPO_ROOT / "docs" / "heuristics-review.md").read_text(encoding="utf-8")
    assert "Pass with notes" in review
    assert "Pending" not in review
