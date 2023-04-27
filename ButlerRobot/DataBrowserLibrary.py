import base64
import datetime
import os
import random
from io import BytesIO
from enum import Enum, auto
from .src.utils.ocr import get_all_text
from collections import namedtuple
from typing import Optional, Union
from PIL import Image
from Browser import Browser, KeyboardModifier, MouseButton
from Browser.utils.data_types import MouseButtonAction, SupportedBrowsers, NewPageDetails
from Browser.utils.data_types import ScreenshotReturnType
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
import pkg_resources
from ButlerRobot.DataWrapperLibrary import DataWrapperLibrary
from ButlerRobot.src.data_types import BBox, PageAction, SaveStatus


class TextType(Enum):
    """Enum that represents if the action is flexible, strict or critical"""
    array = auto()
    string = auto()
        

class DataBrowserLibrary(DataWrapperLibrary):

    # Capture args and kwargs for the DataBrowserLibrary
    def __init__(self, *args, **kwargs):
        """
        Implementation of the DataWrapperLibrary for the Browser library. 
        This library capture data from Browser tests to use later for training deep learning models.

        :param output_path: Path to save data. Default: RobotFramework output directory.
        :param all_json: Save all data in json format. This is use for debuggin purposes. Default: False.
        :param only_actions: Save only actions with tag PageAction. Default: True.
        """
        # Arguments of the library are only evaluated in execution time. There are two ways to handle this:
        # 1. Add "ButlerRobot.DataBrowser" in "robot.libraries.libdoc.needsArgs" setting to add the arguments in the documentation.
        # 2. Set default variables in the __init__ function.
        # In this case, we ignore arguments in linting time to avoid to start playwright process.

        # Check if robotframework is running
        is_running = False
        try:
            BuiltIn()._get_context()
            is_running = True
        except:
            pass
        if is_running:
            keywords_file = pkg_resources.resource_filename('ButlerRobot', 'javascript/keywords.js')        
            # Add the jsextension to kwargs if file exists and not already in kwargs
            if os.path.isfile(keywords_file) and 'jsextension' not in kwargs:
                kwargs['jsextension'] = keywords_file  # This argument triggers the initialization of playwright

        # Get arguments to pass to the DataWrapperLibrary
        output_path = kwargs.pop('output_path', None)
        record = kwargs.pop('record', True)

        super().__init__(Browser(*args, **kwargs), output_path=output_path, record=record)
        self._library: Browser = self._library

        # To filter recorded actions
        self.action_tags = ['PageContent', 'ActionWrapper', 'AI']
        self.exclude_tags = ['Wait']

        self.typing_kw_stringpos = {**self.typing_kw_stringpos, 'keyboardinput': 1, 'typetext': 1, 'typesecret': 1, 'presskeys': ':1'}
        
        # ==== Added Keywords ====
        # To add functions to the library
        self.added_keywords.extend(['click_at_bbox'])
        
        self._click_at_bbox_rf = {
            'args': ['selector_bbox', ('wait_after_click', 2.0)],
            'types': [Union[BBox, str], float],
            'tags': ['ActionWrapper'],
            'doc': self.click_at_bbox.__doc__.strip() if self.click_at_bbox.__doc__ else '',
            'source': f'{self.click_at_bbox.__code__.co_filename}:{self.click_at_bbox.__code__.co_firstlineno}'
        }

    
    # ======= Overrides =======
    def _scroll_to_top(self):
        self._library.scroll_by(selector=None, vertical='-100%')

    def _get_viewport(self) -> dict:
        return self._library.get_viewport_size()

    def _run_scroll(self, selector: str) -> None:
        BuiltIn().run_keyword('Scroll Down', selector)
    
    def _get_screenshot(self, selector=None):
        if not selector:
            im_path = self._library.take_screenshot()
        else:
            im_path = self._library.take_screenshot(selector)
        # Read im_path as a PIL image
        im = Image.open(im_path)

        # Convert to string
        buff = BytesIO()
        im.save(buff, format="PNG")
        img_str = base64.b64encode(buff.getvalue()).decode('ascii')
        return img_str
    
    def _is_browser_open(self):
        return bool(self._library.get_browser_ids())
    
    def _get_action_tags(self):
        return self.action_tags
    
    def _get_exclude_tags(self):
        return self.exclude_tags

    def _get_dom(self):
        return self._library.get_page_source()

    def _wait_for_browser(self):
        BuiltIn().sleep(3)  # For safe recording

    def _get_element_bbox_from_pointer(self, x, y):
        bbox: dict = self._library.evaluate_javascript(None, f'document.elementFromPoint({x}, {y}).getBoundingClientRect()')
        return BBox(bbox['x'], bbox['y'], bbox['width'], bbox['height'])

    def _get_selector_pointer_and_bbox(self, selector):
        try:
            web_element = self._library.get_element(selector)
            bbox = self._library.get_boundingbox(web_element)
            return (
                (bbox['x'] + bbox['width'] / 2,  bbox['y'] + bbox['height'] / 2),
                BBox(**bbox)
            )
        except:
            return None, None
        
    def _replace_keyboard_input(self, locator: str, text: str, clear: bool):
        """
        Override Input text in a text field. Convert this keyword to a Click at BBox and Keyboard Input.
        Param locator: Selector of the text field. In this function is not used. Rely on bbox retrieved from run_keyword.
        Param text: Text to input.
        Param clear: Clear the text field before inputing the text. Ignoring for now.
        """
        current_action = self.exec_stack.remove_action()

        # Replace with Click at BBox
        assert current_action.action_args.bbox, 'Trying to input text. The PageAction has no bbox'
        try:
            BuiltIn().run_keyword('Click At BBox', str(current_action.action_args.bbox))
            # Add Keyboard Input
            BuiltIn().run_keyword('Keyboard Input', text)
        finally:
            # Push keyword to ignore in end_keyword
            current_action.status = SaveStatus.no_record
            self.exec_stack.push(current_action)

    def _replace_keyword_click(self):
        """
        Override Click Element. Convert this keyword to a Click at BBox.
        Param locator: Selector of the element to click.
        """
        current_action = self.exec_stack.remove_action()

        # Replace with Click at BBox
        assert current_action.action_args.bbox, 'Trying to click element. The PageAction has no bbox. Could be be a bad selector'
        try:
            BuiltIn().run_keyword('Click At BBox', str(current_action.action_args.bbox))
        finally:
            # Push keyword to ignore in end_keyword
            current_action.status = SaveStatus.no_record
            self.exec_stack.push(current_action)

    # ======== Keywords =========
    @keyword(name="Open Browser", tags=("Setter", "BrowserControl"))
    def open_browser(
        self,
        url: Optional[str] = None,
        browser: SupportedBrowsers = SupportedBrowsers.chromium,
        headless: bool = False,
        pause_on_failure: bool = True,
        bypassCSP=True,
    ):
        """
        Open a browser. This keyword is a wrapper for Playwright Open Browser keyword.
        Param url: Url to open. If not provided, will open an empty page.
        Param browser: Browser to use. Supported browsers: chromium, firefox, webkit.
        Param headless: Run browser in headless mode.
        Param pause_on_failure: Pause test execution if keyword fails.
        Param bypassCSP: Bypass CSP.
        """
        self._library.open_browser(url, browser, headless, pause_on_failure, bypassCSP)
        self._library.wait_until_network_is_idle()
        BuiltIn().sleep(1)

    @keyword(name="Wait New Page", tags=("Setter", "BrowserControl"))
    def wait_new_page(self, url: Optional[str] = None, wait: int = 3) -> NewPageDetails:
        """
        Open a new page. This keyword is a wrapper for Playwright New Page keyword.
        Param url: Url to open. If not provided, will open an empty page.
        """
        return_val = self._library.new_page(url)
        self._library.wait_until_network_is_idle()
        BuiltIn().sleep(wait)
        return return_val
        
    @keyword(name='Click', tags=['action', 'PageContent'])
    def click(self, selector: str, button: MouseButton = MouseButton.left, clickCount: int = 1, delay: Optional[datetime.timedelta] = None, position_x: Optional[float] = None, position_y: Optional[float] = None, force: bool = False, noWaitAfter: bool = False, *modifiers: KeyboardModifier):
        """
        Override Click Button. Convert this keyword to a Click at BBox.
        Param locator: Selector of the button.
        """
        if self.exec_stack:
            self._replace_keyword_click()
        else:
            self._library.click(selector, button, clickCount, delay, position_x, position_y, force, noWaitAfter, *modifiers)


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
        
        self._library.mouse_button(MouseButtonAction.click, middle_coordinates[0], middle_coordinates[1])

    @keyword(name="Scroll Down", tags=("action", "PageContent"))
    def scroll_down(self, pixels_selector: Union[int, str, None] = None, seed: int = -1):
        """
        Scroll down the page.
        Param pixels: Number of pixels to scroll down.
        """
        # Run Scroll with pixels. If is an int or starts with a number
        if isinstance(pixels_selector, int) or (isinstance(pixels_selector, str) and pixels_selector[0].isdigit()):
            self._library.scroll_by(vertical=pixels_selector)  # type: ignore
            return

        if seed == -1:
            seed = BuiltIn().get_variable_value('${SEED}', random.randint(0, 100))
        random.seed(seed)
        height = self._library.get_viewport_size()['height']

        # Try with locator
        if pixels_selector:
            bbox, _ = self._get_bbox_and_pointer(pixels_selector)
            viewport_height = self._library.get_viewport_size()['height']
            if bbox:
                pixels = (bbox.y + bbox.height) - viewport_height + random.randint(0, height//8)
                self.scroll_down(pixels)
                return
            else:
                BuiltIn().fail(f'Error at Scroll Down. Selector {pixels_selector} not found or does not have bbox.')

        # Scroll down a random number of pixels
        else:
            pixels = random.randint(0, height//2)
            self.scroll_down(pixels)
        
    @keyword(name='Scroll Down At BBox', tags=['action', 'ActionWrapper'])
    def scroll_at_bbox(self, selector_bbox: BBox | str, offset: int = 100):
        """
        Record a click event with no xpath selector. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox
       
        assert bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
        # Get the middle of the bbox
        top_left = (bbox.x, bbox.y)
        w = bbox.width
        h = bbox.height
        middle_coordinates = (top_left[0] + w//2, top_left[1] + h//2)

        self._library.mouse_move(middle_coordinates[0], middle_coordinates[1])
        self._library.mouse_wheel(0, offset)

    @keyword(name='Scroll Up At BBox', tags=['action', 'ActionWrapper'])
    def scroll_up_at_bbox(self, selector_bbox: BBox | str, offset: int = 100):
        """
        Record a click event with no xpath selector. This keyword go throught WrapperLibrary middleware as PageAction.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox
       
        assert bbox, 'Error at Scroll in BBox. Trying to scroll element. The PageAction has no bbox'
        # Get the middle of the bbox
        top_left = (bbox.x, bbox.y)
        w = bbox.width
        h = bbox.height
        middle_coordinates = (top_left[0] + w//2, top_left[1] + h//2)

        self._library.mouse_move(middle_coordinates[0], middle_coordinates[1])
        self._library.mouse_wheel(0, -offset)

    @keyword(name='Is Text Visible', tags=['tesk', 'no_record'])
    def is_text_visible(self, text: str, selector: str | None = None) -> bool:
        """
        Check if text is visible in the page.
        Param text: Text to search.
        Param selector: Selector to search in.
        """
        img = None
        if selector:
            bbox, _ = self._get_bbox_and_pointer(selector)
            if bbox:
                img = self._library.take_screenshot(crop=bbox.to_dict(), return_as=ScreenshotReturnType.base64)

        if not img:
            img = self._library.take_screenshot(return_as=ScreenshotReturnType.base64)

        element_txt = get_all_text(self.ocr_url, img)

        return text in element_txt if element_txt else False

    @keyword(name="Element BBox", tags=['action', 'PageContent'])
    def get_element_bbox(self, selector_bbox: BBox | str) -> BBox:
        """
        Get the bounding box of an element. Dummy instruction for the dataset.
        Param selector: Selector of the element.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error Getting element. Trying to get element bbox from stack. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox

        return bbox
    
    @keyword(name="Get Text From BBox", tags=['task', 'no_record'])
    def get_text_from_bbox(self, selector_bbox: BBox | str, return_type: TextType = TextType.string) -> str:
        """
        Get the text from a BBox.
        Param selector: Selector of the element.
        """
        bbox: BBox | None = None
        # Check if is a locator and convert to BBox
        if isinstance(selector_bbox, str) and not selector_bbox.startswith('BBox'):
            curr_step = self.exec_stack.get_last_step()
            assert isinstance(curr_step, PageAction)
            assert curr_step.action_args.bbox, 'Error Getting Text From BBox. Trying to get element bbox from stack. The PageAction has no bbox'
            bbox = curr_step.action_args.bbox
            # Update the locator to build the dataset
            curr_step.action_args.selector_dom = str(bbox)

        elif isinstance(selector_bbox, str):
            bbox = BBox.from_rf_string(selector_bbox)
        else:
            bbox = selector_bbox
        
        # Get the middle of the bbox
        bottom_right = (bbox.x + bbox.width, bbox.y + bbox.height)
        view_port = self._library.get_viewport_size()
        if bottom_right[0] > view_port.width or bottom_right[1] > view_port.height:
            BuiltIn().log(f'Error at Get Text From BBox. The bbox is out of the viewport. BBox: {bbox.to_dict()}', 'WARN', console=True)
            return ''
        text = self._library.getTextFromBboxWithJs(bbox.x, bbox.y, bottom_right[0], bottom_right[1])
        if not text:
            img = self._library.take_screenshot(crop=bbox.to_dict(), return_as=ScreenshotReturnType.base64)
            text = get_all_text(self.ocr_url, img)
        if not text:
            BuiltIn().log(f'Error at Get Text From BBox. No text found for locator {selector_bbox}', 'WARN', console=True)
            text = ''
        if return_type == TextType.string:
            text = '\n'.join(text)
            text.strip()
        return text

    @keyword(name='Record Click', tags=['task', 'only_substeps'])
    def record_click(self):
        """
        Record a click in the screen. This action only make sense in the interpreter.
        """
        bounding_rect: dict = self._library.getElementBboxHighlighted()  # type: ignore
        bbox: BBox = BBox(bounding_rect['left'], bounding_rect['top'], bounding_rect['width'], bounding_rect['height'])
        
        curr_val_fix_bbox = self.fix_bbox if hasattr(self, 'fix_bbox') else False
        self.fix_bbox = False
        try:
            BuiltIn().run_keyword('Click At BBox', bbox)
        finally:
            self.fix_bbox = curr_val_fix_bbox
        
        BuiltIn().log_to_console(f'Click at BBox  {str(bbox)}')

    @keyword(name='Record Scroll', tags=['task', 'only_substeps'])
    def record_scroll(self):
        """
        Record a scroll in the screen. This action only make sense in the interpreter.
        """
        bounding_rect: dict = self._library.getElementBboxHighlighted()
        bbox: BBox = BBox(bounding_rect['left'], bounding_rect['top'], bounding_rect['width'], bounding_rect['height'])

        curr_val_fix_bbox = self.fix_bbox if hasattr(self, 'fix_bbox') else False
        self.fix_bbox = False
        try:
            BuiltIn().run_keyword('Scroll At BBox', bbox)
        finally:
            self.fix_bbox = curr_val_fix_bbox

        BuiltIn().log_to_console(f'Scroll at BBox  {str(bbox)}')

    @keyword(name='Record BBox', tags=['action', 'no_record'])
    def record_bbox(self) -> BBox:
        """
        Record a BBox in the screen. This action only make sense in the interpreter.
        """
        bounding_rect: dict = self._library.getElementBboxHighlighted()
        bbox: BBox = BBox(bounding_rect['left'], bounding_rect['top'], bounding_rect['width'], bounding_rect['height'])
        return bbox
