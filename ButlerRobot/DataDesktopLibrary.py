import os
import base64
import pyautogui
from io import BytesIO
from typing import Optional, Union
from PIL import Image
from RPA.Desktop import Desktop
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from RPA.Desktop.keywords.screen import log_image, get_output_dir, _create_unique_path,  Path
from .DataWrapperLibrary import DataWrapperLibrary
from .src.data_types import BBox, Step


class DataDesktopLibrary(DataWrapperLibrary):

    # Capture args and kwargs for the DataBrowserLibrary
    def __init__(self, *args, **kwargs):
        """
        Implementation of the DataWrapperLibrary for the Browser library. 
        This library capture data from Browser tests to use later for training deep learning models.
        """

        super().__init__(Desktop(*args, **kwargs))
        # To filter recorded actions
        self._library: Desktop = self._library
        # Add tags to keywords in SeleniumLibrary.keywords.element
        self.action_tags = ['PageContent']
        self.exclude_tags = []
        self.keywords_to_record: list[str] = ['click', 'clickwithoffset', 'movemouse', 'presskeys', 'pressmousebutton', 'releasemousebutton', 'scrolldown', 'typetext', 'typetextinto']
        # Keyboard keywords and string argument position
        self.typing_kw_stringpos = {**self.typing_kw_stringpos, 'keyboardinput': 0, 'typetext': 0, 'typetextinto': 1, 'presskeys': 0}
    
    # ======= Overrides =======

    def _start_keyword(self, name: str, attrs) -> Optional[Step]:
        # Intercept keywords to add tags. There is no way to modify method.tags in runtime
        if any([keyword in name.lower().replace('_', '').replace(' ', '') for keyword in self.keywords_to_record]):
            attrs['tags'].append('PageContent')
        
        return super()._start_keyword(name, attrs)
    
    def _end_keyword(self, name, attrs):
        # Intercept keywords to add tags. There is no way to modify method.tags in runtime
        if any([keyword in name.lower().replace('_', '').replace(' ', '') for keyword in self.keywords_to_record]):
            attrs['tags'].append('PageContent')
        
        return super()._end_keyword(name, attrs)

    def run_keyword(self, name, args, kwargs=None):
        return_value = super().run_keyword(name, args, kwargs)
        if 'open_application' in name.lower():
            # Set window size and maximize if needed. Execute in console xrandr 1280x720
            os.system('xrandr -s 1280x720')
            BuiltIn().sleep(2)
            self._library.press_keys('f11')
        # Sleep after action
        if any([keyword in name.lower().replace('_', '').replace(' ', '') for keyword in self.keywords_to_record]):
            BuiltIn().sleep(1)
        return return_value
    
    def _get_screenshot(self, selector=None):
        if not selector:
            im_path = self.take_screenshot()
        else:
            raise NotImplementedError('Screenshot with selector not implemented in Desktop library')
        # Read im_path as a PIL image
        im = Image.open(im_path)

        # Convert to string
        buff = BytesIO()
        im.save(buff, format="PNG")
        img_str = base64.b64encode(buff.getvalue()).decode('ascii')
        return img_str
    
    def _is_browser_open(self):
        return True
    
    def _get_action_tags(self):
        return self.action_tags
    
    def _get_exclude_tags(self):
        return self.exclude_tags

    def _get_dom(self):
        return ''

    def _wait_for_browser(self):
        """
        Deprecated
        """
        BuiltIn().sleep(1)  # For safe recording
    
    def _run_scroll(self, selector: str) -> None:
        raise NotImplementedError('Scroll not implemented in Desktop library')

    def _scroll_to_top(self):
        """
        Not clear how to do this in Desktop library
        """
        for _ in range(10):
            self._library.press_keys('page_up')

    def _retrieve_bbox_and_pointer_from_page(self, selector) -> tuple[None, None] | tuple[BBox, tuple]:
        # Get the element location, but for this library, the location will be always a bbox.
        return None, None

    def _get_viewport(self) -> dict:
        viewport: dict = self._library.get_display_dimensions()
        return viewport

    # ======== Overrided Keywords =========
    @keyword(name='Scroll Down')
    def scroll_down(self) -> None:
        """
        Scroll down the page
        """
        self._library.press_keys('page_down')

    @keyword(name='Take Screenshot')
    def take_screenshot(
        self,
        path: Optional[str] = None,
        embed: bool = True,
    ) -> str:
        """Take a screenshot of the whole screen, or an element
        identified by the given locator.

        :param path: Path to screenshot. The string ``{index}`` will be replaced with
        an index number to avoid overwriting previous screenshots.
        :param embed: Embed screenshot into Robot Framework log
        """
        screenshot = pyautogui.screenshot()
         
        if path is None:
            dirname = get_output_dir(default=Path.cwd())
            path = dirname / "desktop" / "screenshots" / "desktop-screenshot-{index}.png"

        path: Path = _create_unique_path(path).with_suffix(".png")
        os.makedirs(path.parent, exist_ok=True)

        screenshot.save(path)
        BuiltIn().log(f"Saved screenshot to {path}")

        if embed:
            log_image(screenshot)

        return str(path)
    
    @keyword(name='Click At Bbox', tags=['action'])
    def click_at_bbox(self, selector_bbox: Union[BBox, str], wait_after_click: float = 2.0):
        """
        Record a click event with no xpath selector. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        if isinstance(selector_bbox, str):
            selector_bbox = BBox.from_rf_string(selector_bbox)
        # Get the middle of the bbox
        top_left = (selector_bbox.x, selector_bbox.y)
        w = selector_bbox.width
        h = selector_bbox.height
        middle_coordinates = (top_left[0] + w//2, top_left[1] + h//2)
        coordinates = f"coordinates:{middle_coordinates[0]},{middle_coordinates[1]}"
        
        self._library.move_mouse(coordinates)
        BuiltIn().sleep(0.5)
        self._library.click()


    @keyword(name='Keyboard Input', tags=['action'])
    def keyboard_input(self, text: str):
        """
        Record a keyboard input event. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        self._library.type_text(text)