"""Explorer for https://vk.com/event{id}?act=edit — maps all editable fields."""
import json
import time
from pathlib import Path

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class EventEditExplorer:
    _PACE = 1.5
    _TIMEOUT = 30

    def __init__(self, driver, event_id: int, out_dir: Path):
        self._driver = driver
        self._event_id = event_id
        self._out_dir = out_dir
        self._wait = WebDriverWait(driver, self._TIMEOUT)

    def _wait_for_content(self) -> None:
        """Wait until page content has loaded."""
        def content_ready(d) -> bool:
            try:
                # skeletons gone = content loaded
                skeletons = d.find_elements(By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
                visible = [el for el in skeletons if el.is_displayed()]
                if not visible:
                    return True
                # or rightmenu appeared (settings page)
                rm = d.find_elements(By.CSS_SELECTOR, "[data-testid='rightmenu']")
                return bool(rm and rm[0].is_displayed())
            except StaleElementReferenceException:
                return False

        self._wait.until(content_ready)
        # scroll to bottom to trigger lazy sections (e.g. "Additional information")
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.0)
        self._driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(0.3)

    def run(self) -> None:
        self._out_dir.mkdir(parents=True, exist_ok=True)
        driver = self._driver

        driver.get(f"https://vk.com/event{self._event_id}?act=edit")
        self._wait_for_content()

        self._dismiss_overlays()

        # check if ?act=edit opened a modal/overlay
        overlays = [
            el for el in driver.find_elements(By.CSS_SELECTOR, "#box_layer_wrap, [role='dialog']")
            if el.is_displayed()
        ]
        if overlays:
            print(f"\n══ OVERLAY DETECTED ({len(overlays)}) — dumping overlay contents ══")
            for ov in overlays:
                ov_html = ov.get_attribute("outerHTML") or ""
                (self._out_dir / "overlay.html").write_text(ov_html, encoding="utf-8")
                print(f"  overlay id={ov.get_attribute('id')!r} text={ov.text[:120]!r}")
        else:
            print("  no overlay detected — edit is inline on the page")

        # dump top-level page structure
        print("\n══ PAGE STRUCTURE ══════════════════════════")
        self._dump_page_fields()

        # discover tabs / sub-navigation
        tabs = self._collect_tab_urls()
        if tabs:
            print(f"\n══ TABS ({len(tabs)}) ══════════════════════════")
            for label, href in tabs:
                print(f"  tab: {label!r}  href={href!r}")

            for label, href in tabs:
                print(f"\n── tab: {label!r} ──────────────")
                driver.get(href)
                self._wait_for_content()
                self._dismiss_overlays()
                fields = self._dump_page_fields(prefix=f"  [{label}] ")
                (self._out_dir / f"tab_{self._slugify(label)}.json").write_text(
                    json.dumps(fields, indent=2, ensure_ascii=False), encoding="utf-8"
                )

        # dump raw HTML for manual inspection
        html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML") or ""
        (self._out_dir / "page_body.html").write_text(html, encoding="utf-8")
        print(f"\nSaved HTML to {self._out_dir / 'page_body.html'}")

        # full testids inventory
        testids = self._all_testids()
        (self._out_dir / "testids.json").write_text(
            json.dumps(testids, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Saved testids ({len(testids)}) to {self._out_dir / 'testids.json'}")

    # ── field discovery ──────────────────────────────────────────

    _NAV_NOISE = {
        "top-logo-link", "header-notification-button", "desktop-header-button-counter",
        "TopAudioNote", "header-profile-menu-button", "header-profile-menu",
        "leftmenu", "leftmenuitem", "leftmenuitem-label", "leftmenuitem-text", "leftmenuitem-counter",
        "rightmenu", "rightmenu-in", "community_settings_return_to_group",
        "rightmenuitem-in", "right-menu-group-content",
        "search_top_input", "loading-skeleton",
    }

    def _dump_page_fields(self, prefix: str = "  ") -> list[dict]:
        driver = self._driver
        results = []

        # inputs, textareas, selects
        for sel, kind in [
            ("input:not([type='hidden'])", "input"),
            ("textarea", "textarea"),
            ("select", "select"),
        ]:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if not el.is_displayed():
                        continue
                    info = {
                        "kind": kind,
                        "name": el.get_attribute("name"),
                        "id": el.get_attribute("id"),
                        "testid": el.get_attribute("data-testid"),
                        "type": el.get_attribute("type"),
                        "placeholder": el.get_attribute("placeholder"),
                        "value": el.get_attribute("value"),
                        "aria_label": el.get_attribute("aria-label"),
                    }
                    info = {k: v for k, v in info.items() if v}
                    results.append(info)
                    print(f"{prefix}{kind}: {info}")
                except Exception:
                    pass

        # all elements with data-testid not in inputs above
        seen_testids = {r.get("testid") for r in results if r.get("testid")}
        for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid]"):
            try:
                tid = el.get_attribute("data-testid")
                if not tid or tid in seen_testids or not el.is_displayed():
                    continue
                if tid in self._NAV_NOISE or tid.startswith("cs_menu_item_") or tid.startswith("search_global_tab_"):
                    continue
                tag = el.tag_name
                if tag in ("input", "textarea", "select"):
                    continue
                role = el.get_attribute("role")
                aria_checked = el.get_attribute("aria-checked")
                text = el.text.strip()[:60]
                info: dict = {"kind": "testid-el", "tag": tag, "testid": tid}
                if role:
                    info["role"] = role
                if aria_checked is not None:
                    info["aria_checked"] = aria_checked
                if text:
                    info["text"] = text
                results.append(info)
                print(f"{prefix}[{tid}] tag={tag} role={role} aria-checked={aria_checked} text={text!r}")
            except Exception:
                pass

        return results

    # ── tab / nav discovery ──────────────────────────────────────

    def _collect_tab_urls(self) -> list[tuple[str, str]]:
        """Return (label, href) for settings nav links. No element references — stale-safe."""
        driver = self._driver
        result: list[tuple[str, str]] = []
        seen: set[str] = set()

        # right-side settings menu: cs_menu_item_* links
        for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='cs_menu_item_']"):
            try:
                if not el.is_displayed():
                    continue
                href = el.get_attribute("href") or ""
                label = el.text.strip()
                if href and label and href not in seen:
                    seen.add(href)
                    result.append((label, href))
            except Exception:
                pass

        # fallback: top tab bar (search_global_tab_*)
        if not result:
            for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='search_global_tab_']"):
                try:
                    if not el.is_displayed():
                        continue
                    href = el.get_attribute("href") or ""
                    label = el.text.strip()
                    if href and label and href not in seen:
                        seen.add(href)
                        result.append((label, href))
                except Exception:
                    pass

        return result

    # ── helpers ──────────────────────────────────────────────────

    def _dismiss_overlays(self) -> None:
        try:
            self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.3)
        except Exception:
            pass

    def _all_testids(self) -> list[dict]:
        driver = self._driver
        results = []
        seen: set[str] = set()
        for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid]"):
            try:
                tid = el.get_attribute("data-testid")
                if not tid or tid in seen:
                    continue
                seen.add(tid)
                results.append({
                    "testid": tid,
                    "tag": el.tag_name,
                    "role": el.get_attribute("role"),
                    "text": el.text.strip()[:80],
                    "visible": el.is_displayed(),
                })
            except Exception:
                pass
        return results

    @staticmethod
    def _slugify(s: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")
