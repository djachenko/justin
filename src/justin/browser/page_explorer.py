import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def _log(msg: str) -> None:
    print(f"[EXPLORE] {msg}", flush=True)


def _dump(driver, prefix: str = "") -> None:
    """Дамп текущего видимого состояния: дропдауны, оверлеи с testids."""
    dropdown_items = [
        el for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid='dropdownactionsheet-item']")
        if el.is_displayed()
    ]
    if dropdown_items:
        _log(f"{prefix}dropdown: {[el.text.strip() for el in dropdown_items]}")

    for sel in ("[id^='box_layer']", "[role='dialog']"):
        for el in driver.find_elements(By.CSS_SELECTOR, sel):
            try:
                if not el.is_displayed() or not el.text.strip():
                    continue
                el_id = el.get_attribute("id") or "no-id"
                testids = [
                    e.get_attribute("data-testid")
                    for e in el.find_elements(By.CSS_SELECTOR, "[data-testid]")
                    if e.get_attribute("data-testid")
                ]
                _log(f"{prefix}overlay [{el_id}]: {el.text.strip()[:120]!r}")
                if testids:
                    _log(f"{prefix}  testids: {testids}")
            except Exception:
                pass


def _visible_clickables(driver) -> list[tuple[str, object]]:
    """Кликабельные элементы в текущем открытом контексте (дропдаун или модал)."""
    # Сначала дропдаун
    items = [
        el for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid='dropdownactionsheet-item']")
        if el.is_displayed()
    ]
    if items:
        return [(el.text.strip() or f"item_{i}", el) for i, el in enumerate(items)]

    # Иначе — кнопки внутри открытого модала
    for sel in ("[id='box_layer_wrap']", "[role='dialog']"):
        wraps = [el for el in driver.find_elements(By.CSS_SELECTOR, sel) if el.is_displayed()]
        if not wraps:
            continue
        wrap = wraps[0]
        result = []
        for el in wrap.find_elements(By.CSS_SELECTOR, "button, [role='button'], [data-testid]"):
            try:
                if not el.is_displayed():
                    continue
                label = (
                    el.get_attribute("aria-label")
                    or el.get_attribute("data-testid")
                    or el.text.strip()[:50]
                )
                if label:
                    result.append((label, el))
            except Exception:
                pass
        return result

    return []


class PageExplorer:
    def __init__(self, driver):
        self._driver = driver

    def explore(self) -> None:
        driver = self._driver
        _log(f"── timeout @ {driver.current_url}")
        _dump(driver, prefix="  ")

        candidates = _visible_clickables(driver)
        if not candidates:
            _log("  no clickable context found")
            return

        _log(f"  clickables: {[label for label, _ in candidates]}")

        for label, el in candidates:
            try:
                _log(f"  → click '{label}'")
                driver.execute_script("arguments[0].click()", el)
                time.sleep(0.5)
                _dump(driver, prefix="    ")
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.3)
            except Exception as e:
                _log(f"    error: {e}")
