import base64
import random
from io import BytesIO
from typing import Optional, Union
from PIL import Image
from SeleniumLibrary import SeleniumLibrary
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
from .DataWrapperLibrary import DataWrapperLibrary
from .src.data_types import BBox, SaveStatus, Step


class DataSeleniumLibrary(DataWrapperLibrary):

    # Capture args and kwargs for the DataBrowserLibrary
    def __init__(self, *args, **kwargs):
        """
        Implementation of the DataWrapperLibrary for the Browser library. 
        This library capture data from Browser tests to use later for training deep learning models.

        :param output_path: Path to save data. Default: RobotFramework output directory.
        :param all_json: Save all data in json format. This is use for debuggin purposes. Default: False.
        :param only_actions: Save only actions with tag PageAction. Default: True.
        """

        super().__init__(SeleniumLibrary(*args, **kwargs))
        # To filter recorded actions
        self._library: SeleniumLibrary = self._library
        # Add tags to keywords in SeleniumLibrary.keywords.element
        self.action_tags = ['PageContent', 'ActionWrapper']
        self.exclude_tags = ['Wait']
        self.keywords_to_record: list[str] = ['scrollelementintoview', 'clickelementatcoordinates', 'doubleclickelement', 'mousedown', 'mouseout', 'mouseover', 'mouseup', 'opencontextmenu', 'presskey', 'presskeys', 'submitform', 'unselectcheckbox', 'selectcheckbox', 'selectradiobutton', 'choosefile']
        # Keyboard keywords and string argument position
        self.typing_kw_stringpos = {'keyboardinput': 0,
                            'inputtext': 1,
                            'inputpassword': 1,
                            'inputsecret': 1,
                            'inputfile': 1,
                            'inputfilewithcontent': 1,
                            'inputfilewithcontentandencoding': 1}
    
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
        if 'open_browser' in name.lower():
            self._library.set_window_size(1280, 720, True)
        return return_value
    

    def _get_screenshot(self, selector=None):
        if not selector:
            im_path = self._library.capture_page_screenshot()
        else:
            im_path = self._library.capture_element_screenshot(selector)
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
        return self._library.get_source()

    def _wait_for_browser(self):
        BuiltIn().sleep(3)  # For safe recording
    
    def _run_scroll(self, selector: str) -> None:
        BuiltIn().run_keyword('Scroll Down', selector)

    def _scroll_to_top(self):
        self._library.execute_javascript('window.scrollTo(0, 0)')

    def _get_selector_pointer_and_bbox(self, selector):
        # Get web element position respect to the viewport
        try:
            web_element = self._library.get_webelement(selector)
            scroll = self._library.execute_javascript('return {x: window.scrollX, y: window.scrollY}')
            bbox = {
                'x': web_element.location['x'] - scroll['x'],
                'y': web_element.location['y'] - scroll['y'],
                'width': web_element.size['width'],
                'height': web_element.size['height']
            }
            return (
                (bbox['x'] + bbox['width'] / 2,  bbox['y'] + bbox['height'] / 2),
                BBox(**bbox)
            )
        except:
            return None, None

    def _get_viewport_loc(self) -> dict:
        viewport: dict = self._library.execute_javascript('return {width: window.innerWidth, height: window.innerHeight}')
        viewport.update(self._library.execute_javascript('return {x: window.scrollX, y: window.scrollY}'))
        return viewport
    
    # def _remove_action(self):
    #     """
    #     Replace a keyword with another.
    #     """
    #     assert not self.exec_stack.is_empty(), 'Trying to replace a keyword. The stack is empty'
    #     # Get bbox where to click
    #     assert isinstance(self.exec_stack.get_last_step(), PageAction), 'Trying to input text. The last step in the stack is not a PageAction'
    #     # Remove this action from the stack
    #     current_action: PageAction = self.exec_stack.pop()  # type: ignore

    #     return current_action
    
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

    def _replace_keyword_click(self, locator: str):
        """
        Override Click Element. Convert this keyword to a Click at BBox.
        Param locator: Selector of the element to click.
        """
        current_action = self.exec_stack.remove_action()

        # Replace with Click at BBox
        assert current_action.action_args.bbox, 'Trying to click element. The PageAction has no bbox'
        try:
            BuiltIn().run_keyword('Click At BBox', str(current_action.action_args.bbox))
        finally:
            # Push keyword to ignore in end_keyword
            current_action.status = SaveStatus.no_record
            self.exec_stack.push(current_action)

    # ======== Overrided Keywords =========
    @keyword(name='Input Text', tags=['action', 'PageContent'])
    def input_text(self, locator: str, text: str, clear: bool = True):
        if self.exec_stack:
            self._replace_keyboard_input(locator, text, clear)
        else:
            self._library.input_text(locator, text, clear)

    @keyword(name='Input Password', tags=['action', 'PageContent'])
    def input_password(self, locator: str, text: str, clear: bool = True):
        if self.exec_stack:
            self._replace_keyboard_input(locator, text, clear)
        else:
            self._library.input_password(locator, text, clear)

    @keyword(name='Select Checkbox', tags=['action', 'PageContent'])
    def select_checkbox(self, locator: str):
        """
        Override Select Checkbox. Convert this keyword to a Click at BBox.
        Param locator: Selector of the checkbox.
        """
        if self.exec_stack:
            self._replace_keyword_click(locator)
        else:
            self._library.select_checkbox(locator)

    @keyword(name='Unselect Checkbox', tags=['action', 'PageContent'])
    def unselect_checkbox(self, locator: str):
        """
        Override Unselect Checkbox. Convert this keyword to a Click at BBox.
        Param locator: Selector of the checkbox.
        """
        if self.exec_stack:
            self._replace_keyword_click(locator)
        else:
            self._library.unselect_checkbox(locator)

    @keyword(name='Click Element', tags=['action', 'PageContent'])
    def click_element(self, locator: str):
        """
        Override Click Element. Convert this keyword to a Click at BBox.
        Param locator: Selector of the element to click.
        """
        if self.exec_stack:
            self._replace_keyword_click(locator)
        else:
            self._library.click_element(locator)

    @keyword(name='Click Button', tags=['action', 'PageContent'])
    def click_button(self, locator: str):
        """
        Override Click Button. Convert this keyword to a Click at BBox.
        Param locator: Selector of the button.
        """
        if self.exec_stack:
            self._replace_keyword_click(locator)
        else:
            self._library.click_button(locator)

    @keyword(name='Click Link', tags=['action', 'PageContent'])
    def click_link(self, locator: str):
        """
        Override Click Link. Convert this keyword to a Click at BBox.
        Param locator: Selector of the link.
        """
        if self.exec_stack:
            self._replace_keyword_click(locator)
        else:
            self._library.click_link(locator)

    @keyword(name='Click Image', tags=['action', 'PageContent'])
    def click_image(self, locator: str):
        """
        Override Click Image. Convert this keyword to a Click at BBox.
        Param locator: Selector of the image.
        """
        if self.exec_stack:
            self._replace_keyword_click(locator)
        else:
            self._library.click_image(locator)


    # ======== Keywords =========
    @keyword(name='Click At BBox', tags=['action', 'PageContent'])
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
        
        # Click at middle coordinates. First get the element at the coordinates
        element = self._library.execute_javascript(f'return document.elementFromPoint({middle_coordinates[0]}, {middle_coordinates[1]})')
        if not element:
            BuiltIn().fail(f'Error clicking bbox. No element found at coordinates {middle_coordinates}')
        # Then click at the element
        self._library.click_element(element)
        
    
    @keyword(name='Keyboard Input', tags=['action', 'PageContent'])
    def keyboard_input(self, text: str):
        """
        Record a keyboard input event. Same keyword as Browser library.
        """
        self._library.press_keys(None, *text)
    
    @keyword(name='Scroll Down', tags=['action', 'PageContent'])
    def scroll_down(self, selector: str, seed: int = -1):
        """
        Scroll down the page.
        Param selector: Selector of the element to scroll to.
        Param seed: Seed for random number generator.
        """
        self._library.scroll_element_into_view(selector)
        # Scroll down a random number of pixels up to 100 with seed for replication
        if seed == -1:
            seed = BuiltIn().get_variable_value('${SEED}', random.randint(0, 100))
        random.seed(seed)
        # Scroll down a random number of pixels up to half the screen height
        height = self._library.execute_javascript('return window.innerHeight')
        pixels = random.randint(0, height//2)
        self._library.execute_javascript(f'window.scrollBy(0, {pixels})')


        
