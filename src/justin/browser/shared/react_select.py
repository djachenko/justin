"""A React-controlled <select>: the value goes in through the prototype setter.

React replaces the element's own value setter and keeps the state to itself, so a plain
select.value assignment goes unnoticed — and Selenium's Select goes through the same
setter. The only path React takes for a user's choice is the native prototype setter
plus a change event.
"""
from selenium.webdriver.chrome.webdriver import WebDriver

_SET_VALUE = """
    var select = document.querySelector('[name="' + arguments[0] + '"]');
    var setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;

    setter.call(select, arguments[1]);
    select.dispatchEvent(new Event('change', {bubbles: true}));
"""


def set_react_select(driver: WebDriver, name: str, value: str) -> None:
    driver.execute_script(_SET_VALUE, name, value)
