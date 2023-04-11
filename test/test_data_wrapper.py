"""
Keywords made in Python behave like a Task.
"""

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from ButlerRobot.DataBrowserLibrary import DataBrowserLibrary


try:
    lib: DataBrowserLibrary = BuiltIn().get_library_instance('Browser')
    lib.add_task_library('test_data_wrapper')
except:
    pass


@keyword(name="Search ${product_name} product")
def test(product_name):
    lib.type_text('//input[@name="field-keywords"]', product_name)
    lib.click('//input[@id="nav-search-submit-button"]')
