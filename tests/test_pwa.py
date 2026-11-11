import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PwaManifestTests(unittest.TestCase):
    def test_manifest_declares_installable_rtl_app_and_required_icons(self):
        manifest_path = ROOT / "manifest.webmanifest"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["dir"], "rtl")
        self.assertEqual(manifest["lang"], "ar-DZ")
        self.assertEqual(manifest["start_url"], "./index.html")
        self.assertEqual(manifest["scope"], "./")

        icons = {icon["sizes"]: icon for icon in manifest["icons"]}
        self.assertIn("192x192", icons)
        self.assertIn("512x512", icons)
        self.assertIn("maskable", icons["512x512"]["purpose"])
        for icon in icons.values():
            self.assertTrue((ROOT / icon["src"].removeprefix("./")).is_file())


class PwaPageIntegrationTests(unittest.TestCase):
    def test_every_page_links_manifest_theme_color_and_bootstrap(self):
        for page in ("index.html", "main.html", "maintenance.html", "store.html"):
            with self.subTest(page=page):
                html = (ROOT / page).read_text(encoding="utf-8")
                self.assertRegex(html, r'<link[^>]+rel=["\']manifest["\'][^>]+href=["\']\./manifest\.webmanifest')
                self.assertRegex(html, r'<meta[^>]+name=["\']theme-color["\']')
                self.assertRegex(html, r'<script[^>]+src=["\']\./pwa\.js["\']')

    def test_bootstrap_registers_service_worker_and_install_prompt(self):
        script = (ROOT / "pwa.js").read_text(encoding="utf-8")
        self.assertIn("navigator.serviceWorker.register('./service-worker.js', { scope: './' })", script)
        self.assertIn("beforeinstallprompt", script)
        self.assertIn("appinstalled", script)


class OfflineSupportTests(unittest.TestCase):
    def test_service_worker_caches_app_shell_and_offline_navigation(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        for event in ("install", "activate", "fetch"):
            self.assertIn(f"addEventListener('{event}'", worker)
        self.assertIn("offline.html", worker)

        for path in (
            "index.html", "main.html", "maintenance.html", "store.html",
            "offline.html", "manifest.webmanifest", "pwa.js",
            "icons/icon-192.png", "icons/icon-512.png", "icons/icon-512-maskable.png",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_icons_are_valid_pngs_with_expected_dimensions(self):
        for filename, expected in (("icon-192.png", 192), ("icon-512.png", 512), ("icon-512-maskable.png", 512)):
            with self.subTest(icon=filename):
                data = (ROOT / "icons" / filename).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual((width, height), (expected, expected))


if __name__ == "__main__":
    unittest.main()
