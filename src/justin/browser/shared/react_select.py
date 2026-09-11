"""React-управляемый <select>: значение ставится через прототип, иначе React не заметит.

React подменяет сеттер value у самого элемента и держит состояние у себя, поэтому
прямое присваивание select.value он не видит, а selenium-овский Select тоже идёт
через него. Единственный путь, который React принимает за выбор пользователя, —
нативный сеттер из прототипа плюс событие change.
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
