import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.sources: list[str] = []
        self.lang: str | None = None
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.tags.append(tag)
        if tag == "html":
            self.lang = values.get("lang")
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if values.get("href"):
            self.hrefs.append(values["href"] or "")
        if values.get("src"):
            self.sources.append(values["src"] or "")


class StaticSiteTests(unittest.TestCase):
    routes = {
        "index.html": "en",
        "zh-TW/index.html": "zh-Hant",
        "privacy/index.html": "en",
        "terms/index.html": "en",
    }

    def parse(self, relative: str) -> tuple[str, SiteParser]:
        text = (SITE / relative).read_text(encoding="utf-8")
        parser = SiteParser()
        parser.feed(text)
        return text, parser

    def test_required_routes_are_semantic_and_local_first(self) -> None:
        for relative, expected_lang in self.routes.items():
            with self.subTest(route=relative):
                text, parser = self.parse(relative)
                self.assertEqual(expected_lang, parser.lang)
                self.assertIn("main", parser.tags)
                self.assertIn("nav", parser.tags)
                self.assertIn("footer", parser.tags)
                self.assertNotIn("script", parser.tags)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                self.assertFalse(parser.sources, "Site must not fetch script or media assets")
                self.assertNotRegex(text, r"(?i)googletag|segment\.com|plausible\.io")

    def test_homepages_contain_the_complete_product_contract(self) -> None:
        required_ids = {
            "product",
            "workflow",
            "modes",
            "skills",
            "obsidian",
            "install",
            "trust",
            "faq",
        }
        for relative in ("index.html", "zh-TW/index.html"):
            with self.subTest(route=relative):
                text, parser = self.parse(relative)
                self.assertTrue(required_ids.issubset(set(parser.ids)))
                for phrase in (
                    "Map",
                    "Cover",
                    "Deepen",
                    "Prove",
                    "ENGINE",
                    "SKILL_ONLY",
                    "Capability Map",
                    "Coverage Gate",
                    "Receipts",
                    "Obsidian",
                    "vgtree --version",
                ):
                    self.assertIn(phrase, text)
                self.assertEqual(6, len(re.findall(r'class="skill-card"', text)))

    def test_internal_links_resolve_within_site(self) -> None:
        for relative in self.routes:
            page = SITE / relative
            _, parser = self.parse(relative)
            for href in parser.hrefs:
                parsed = urlsplit(href)
                if parsed.scheme or href.startswith("mailto:") or href.startswith("#"):
                    continue
                target = (page.parent / parsed.path).resolve()
                if parsed.path.endswith("/") or target.is_dir():
                    target /= "index.html"
                self.assertTrue(target.is_file(), f"Broken link {href!r} in {relative}")

    def test_css_has_responsive_accessible_contract(self) -> None:
        css = (SITE / "assets/styles.css").read_text(encoding="utf-8")
        self.assertNotRegex(css, r"(?i)@import|https?://|url\(")
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertRegex(css, r"@media\s*\(min-width:\s*48rem\)")
        self.assertRegex(css, r"max-width:\s*72rem")
        self.assertRegex(css, r"min-height:\s*44px")

    def test_primary_palette_meets_wcag_aa_contrast(self) -> None:
        css = (SITE / "assets/styles.css").read_text(encoding="utf-8")
        colors = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6});", css))

        def luminance(value: str) -> float:
            channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def contrast(first: str, second: str) -> float:
            light, dark = sorted((luminance(first), luminance(second)), reverse=True)
            return (light + 0.05) / (dark + 0.05)

        for foreground, background in (
            ("ink", "canvas"),
            ("muted", "surface"),
            ("mint", "canvas"),
            ("lime", "canvas"),
        ):
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(contrast(colors[foreground], colors[background]), 4.5)

    def test_policy_pages_match_public_trust_boundary(self) -> None:
        privacy, _ = self.parse("privacy/index.html")
        terms, _ = self.parse("terms/index.html")
        for phrase in ("no telemetry", "no analytics", "no cookies", "Tool Receipts"):
            self.assertIn(phrase, privacy)
        for phrase in ("MIT License", "local-first", "no warranty", "OpenAI"):
            self.assertIn(phrase, terms)


if __name__ == "__main__":
    unittest.main()
