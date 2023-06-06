
from typing import List, Union, Optional, Any
from RPA.Desktop.keywords.application import Application
from RPA.Desktop.keywords.clipboard import LocatorType
from RPA.Desktop.keywords.finder import Geometry
from RPA.Desktop.keywords.mouse import Point, Action
from RPA.Desktop.keywords.screen import Region
from robotlibcore import DynamicCore


class Desktop(DynamicCore):
    def _create_app(self, name: str, args: Union[List[str], str], shell: bool = False) -> Application:
        ...

    def open_application(self, name_or_path: str, *args: str) -> Application:
        ...

    def open_file(self, path: str) -> Application:
        ...

    def copy_to_clipboard(self, locator: LocatorType) -> str:
        ...

    def paste_from_clipboard(self, locator: LocatorType) -> None:
        ...

    def clear_clipboard(self) -> None:
        ...

    def get_clipboard_value(self) -> str:
        ...

    def set_clipboard_value(self, value: str) -> None:
        ...
    
    def find_elements(self, locator: LocatorType) -> List[Geometry]:
        ...
    
    def find_element(self, locator: LocatorType) -> Geometry:
        ...

    def wait_for_element(
        self,
        locator: LocatorType,
        timeout: Optional[float] = None,
        interval: float = 0.5,
    ) -> Geometry:
        ...

    def set_default_timeout(self, timeout: float = 3.0):
        ...

    def set_default_confidence(self, confidence: float = None):
        ...

    def type_text(self, text: str, *modifiers: str, enter: bool = False) -> None:
        ...

    def press_keys(self, *keys: str) -> None:
        ...
    
    def type_text_into(
        self, locator: LocatorType, text: str, clear: bool = False, enter: bool = False
    ) -> None:
        ...

    def click(
        self,
        locator: Optional[LocatorType] = None,
        action: Action = Action.click,
    ) -> None:
        ...

    def click_with_offset(
        self,
        locator: Optional[LocatorType] = None,
        x: int = 0,
        y: int = 0,
        action: Action = Action.click,
    ) -> None:
        ...

    def get_mouse_position(self) -> Point:
        ...
    
    def move_mouse(self, locator: LocatorType) -> None:
        ...

    def press_mouse_button(self, button: Any = "left") -> None:
        ...

    def release_mouse_button(self, button: Any = "left") -> None:
        ...
    
    def drag_and_drop(
        self,
        source: LocatorType,
        destination: LocatorType,
        start_delay: float = 2.0,
        end_delay: float = 0.5,
    ) -> None:
        ...

    def take_screenshot(
        self,
        path: Optional[str] = None,
        locator: Optional[LocatorType] = None,
        embed: bool = True,
    ) -> str:
        ...

    def get_display_dimensions(self) -> Region:
        ...

    def highlight_elements(self, locator: LocatorType):
        ...

    def define_region(self, left: int, top: int, right: int, bottom: int) -> Region:
        ...

    def move_region(self, region: Region, left: int, top: int) -> Region:
        ...

    def resize_region(
        self,
        region: Region,
        left: int = 0,
        top: int = 0,
        right: int = 0,
        bottom: int = 0,
    ) -> Region:
        ...

    def read_text(self, locator: Optional[str] = None, invert: bool = False):
        ...

    