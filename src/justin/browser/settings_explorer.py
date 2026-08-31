import json
import time
from difflib import unified_diff
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class SettingsExplorer:
    def __init__(self, driver, event_id: int, out_dir: Path):
        self._driver = driver
        self._event_id = event_id
        self._out_dir = out_dir

    def run(self) -> None:
        self._out_dir.mkdir(parents=True, exist_ok=True)
        driver = self._driver

        driver.get(f"https://vk.com/event{self._event_id}/settings/sections")

        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='list_enabled']"))
        )
        time.sleep(0.5)

        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except Exception:
            pass

        items = self._collect_section_items()
        print(f"Found {len(items)} items: {[tid for tid, _ in items]}")

        results: dict[str, dict] = {}

        for i, (tid, el) in enumerate(items):
            print(f"\n[{i+1}/{len(items)}] {tid}")

            before_html = self._overlay_html()
            driver.execute_script("arguments[0].click()", el)
            time.sleep(1.5)

            after_html = self._overlay_html()
            info = self._overlay_info()
            results[tid] = {"tid": tid, "overlay": info}

            print(f"  testids : {info['testids']}")
            print(f"  buttons : {info['buttons']}")
            print(f"  text    : {info['text'][:100]}")

            (self._out_dir / f"{i:02d}_{tid}_overlay.html").write_text(after_html, encoding="utf-8")
            diff = self._diff(before_html, after_html)
            (self._out_dir / f"{i:02d}_{tid}_diff.txt").write_text("\n".join(diff), encoding="utf-8")
            print(f"  diff    : {len(diff)} lines")

            toggle_result = self._explore_toggle(tid, info["testids"])
            if toggle_result:
                results[tid]["toggle"] = toggle_result

            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)

        (self._out_dir / "results.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        self._generalize(results)

    def _explore_sub_clicks(self) -> list[dict]:
        driver = self._driver
        wrap = driver.find_elements(By.CSS_SELECTOR, "#box_layer_wrap")
        if not wrap:
            return []

        candidates = [
            ((el.get_attribute("aria-label") or el.text or "").strip()[:40], el)
            for el in wrap[0].find_elements(By.CSS_SELECTOR, "button, [role='button']")
            if el.is_displayed()
            and (el.get_attribute("aria-label") or el.text or "").strip()
            not in ("", "Cancel", "Save")
        ]

        results = []
        for label, el in candidates:
            print(f"    → sub-click: '{label}'")
            before = self._overlay_html()
            try:
                driver.execute_script("arguments[0].click()", el)
                time.sleep(0.8)
                after = self._overlay_html()
                diff = self._diff(before, after)
                results.append({
                    "label": label,
                    "diff_lines": len(diff),
                    "changed": after != before,
                })
                print(f"      diff: {len(diff)} lines, changed: {after != before}")
            except Exception as e:
                print(f"      error: {e}")
        return results

    def _explore_toggle(self, tid: str, current_testids: list[str]) -> dict | None:
        """Кликнуть тоггл секции, снапшот до/после, вернуть обратно."""
        driver = self._driver
        toggle_testid = next(
            (t for t in current_testids if "toggle" in t or "enabled" in t),
            None,
        )
        if not toggle_testid:
            return None

        print(f"  toggle  : {toggle_testid}")
        before_info = self._overlay_info()

        try:
            toggle_el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{toggle_testid}"]')
            was_checked = toggle_el.get_attribute("aria-checked")
            driver.execute_script("arguments[0].click()", toggle_el)
            time.sleep(0.8)

            after_info = self._overlay_info()
            disappeared = set(before_info["testids"]) - set(after_info["testids"])
            appeared = set(after_info["testids"]) - set(before_info["testids"])
            print(f"    was={was_checked} → disappeared: {sorted(disappeared)}, appeared: {sorted(appeared)}")

            # вернуть обратно
            toggle_el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{toggle_testid}"]')
            driver.execute_script("arguments[0].click()", toggle_el)
            time.sleep(0.5)

            return {
                "toggle_testid": toggle_testid,
                "was_checked": was_checked,
                "disappeared_when_off": sorted(disappeared),
                "appeared_when_off": sorted(appeared),
            }
        except Exception as e:
            print(f"    toggle error: {e}")
            return None

    def _collect_section_items(self) -> list[tuple[str, object]]:
        driver = self._driver
        skip = {"list_enabled", "list_disabled", "sections_toggle_reorder"}
        items = []
        seen = set()
        for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid='list_enabled'] [data-testid], [data-testid='list_disabled'] [data-testid]"):
            try:
                tid = el.get_attribute("data-testid")
                if tid not in skip and tid not in seen and el.is_displayed():
                    seen.add(tid)
                    items.append((tid, el))
            except Exception:
                pass
        return items

    def _overlay_html(self) -> str:
        els = self._driver.find_elements(By.CSS_SELECTOR, "#box_layer_wrap")
        if els and els[0].is_displayed():
            return els[0].get_attribute("outerHTML") or ""
        return ""

    def _overlay_info(self) -> dict:
        wrap = self._driver.find_elements(By.CSS_SELECTOR, "#box_layer_wrap")
        if not wrap or not wrap[0].is_displayed():
            return {"testids": [], "buttons": [], "text": ""}
        testids = [
            el.get_attribute("data-testid")
            for el in wrap[0].find_elements(By.CSS_SELECTOR, "[data-testid]")
            if el.get_attribute("data-testid")
        ]
        buttons = [
            (el.get_attribute("aria-label") or el.text or "").strip()[:60]
            for el in wrap[0].find_elements(By.CSS_SELECTOR, "button, [role='button']")
            if el.is_displayed()
        ]
        return {
            "testids": testids,
            "buttons": [b for b in buttons if b],
            "text": wrap[0].text.strip(),
        }

    @staticmethod
    def _diff(before: str, after: str) -> list[str]:
        return list(unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile="before", tofile="after", lineterm="",
        ))

    def _generalize(self, results: dict) -> None:
        print("\n\n══ GENERALIZATION ════════════════════════════")

        with_overlays = {tid: v for tid, v in results.items() if v.get("overlay", {}).get("testids")}
        if not with_overlays:
            print("No overlays captured.")
            return

        sets = [set(v["overlay"]["testids"]) for v in with_overlays.values()]
        common = set.intersection(*sets)
        print(f"\nCommon testids ({len(common)}): {sorted(common)}")

        print("\nUnique testids per section:")
        for tid, v in with_overlays.items():
            unique = set(v["overlay"]["testids"]) - common
            print(f"  {tid}: {sorted(unique)}")

        lines = [f"Common testids: {sorted(common)}\n"]
        for tid, v in with_overlays.items():
            unique = set(v["overlay"]["testids"]) - common
            lines += [
                f"{tid}:",
                f"  unique: {sorted(unique)}",
                f"  buttons: {v['overlay']['buttons']}",
                f"  text: {v['overlay']['text'][:120]}",
                "",
            ]

        (self._out_dir / "generalization.txt").write_text("\n".join(lines), encoding="utf-8")
        print(f"\nSaved: {self._out_dir.absolute()}")
