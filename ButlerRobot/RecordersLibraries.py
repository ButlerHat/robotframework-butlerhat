import os
import ButlerRobot
import cv2
import random
import imagehash
from .src.utils import ocr
from typing import Optional
from PIL import Image
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
from Browser.utils.data_types import KeyboardInputAction, KeyAction
from Browser import Browser
from .src.data_types import BBox


class DataRecorderInterface:
    """
    Interface to implement for the recorders. 
    
    The recorders starts from a page and interactuates with elements defined by the xpath list. To do this, the recorder
    calls keywords and let the DataBrowserLibrary capture all the observations and actions.

    :param library_instance: Browser instance
    :param elements_xpath: List of xpath to find the elements to interactuate.
    :param wait_to_go: Time to wait for the page to load when restored.
    """


    ROBOT_AUTO_KEYWORDS = False
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, library_instance: Browser, elements_xpath: list, wait_to_go: int = 2, max_scroll: int = 5, max_elements: int = -2, lang_instructions: str="en"):
        # Browser instance
        self.library: Browser = library_instance
        # Elemnents xpath
        self.elements_xpath: list = elements_xpath
        # timeout to wait for the page to load
        self.wait_to_go: int = wait_to_go
        # Max scroll to do
        self.max_scroll: int = max_scroll
        # Max number of elements to scroll. -1 for no limit. -2 for half of not scrollable elements.
        self.max_elements: int = max_elements
        # Lang
        self.lang_instructions: str = lang_instructions

        # ====== Utils ======
        # OCR
        ocr_url = BuiltIn().get_variable_value("${OCR_URL}")
        self.ocr_url: str = ocr_url if ocr_url else "http://nginx_alfred/fd/ppocrv3"
        lang = BuiltIn().get_variable_value("${OCR_LANG}")
        self.lang: str = lang if lang else "en"

        # Temp dir to store the screenshots
        out_dir = BuiltIn().get_variable_value("${OUTPUTDIR}")
        self.tmp_dir = os.path.join(out_dir, 'tmp_screenshots')
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def _action(self, instruction: Optional[str], img_element: cv2.Mat, el_margin: tuple[int, int], *args) -> None:
        """
        Action to perform on the element.
        """
        raise NotImplementedError

    def _predict_instruction(self, screenshot_path: Optional[str], element_path: str, action_bbox: BBox, *action_args):
        """
        Predict the instruction to perform.
        """
        raise NotImplementedError

    def _is_good_element(self, element_screenshot: str) -> bool:
        """
        Check if the element is good to perform the action.
        """
        raise NotImplementedError

    def record(self):
        """
        Record the actions on the page. Need to be in two steps because the action could
        modify all the locators of the page. 
        Visual template matching is found the most reliable way to confirm the element
        validated is the selected in the record step.
        """

        elements = self._get_elements_to_record()
        self._record_elements(elements)

    def _get_elements_to_record(self, expand_bbox: bool = False):
        """
        Get all the interactuable elements in the page in the form of a list of screenshot elements.
        :param expand_bbox: Expand the bbox of the element to include the label. Not necessary for buttons.
        :param max_scroll_elements: Max number of elements to scroll. -1 for no limit. -2 for half of not scrollable elements.
        """
        def is_valid(page_size, view_port_size, bbox_element, max_scroll_elements):
            """
            Filter the element to check if it is good to perform the action.
            Valid elements are those that are inside the page.
            """
            # Check if element has sufficient size
            if bbox_element['width'] < 1 or bbox_element['height'] < 1:
                return False
            # Check if element is inside the page
            if bbox_element['x'] < 0 or bbox_element['y'] < 0: 
                return False
            if (bbox_element['x'] + bbox_element['width']) > page_size['width']:
                return False
            if (bbox_element['y'] + bbox_element['height']) > page_size['height']:
                return False
            # Check if element there are too many elements to scroll
            if (bbox_element['y'] + bbox_element['height']) > view_port_size['height']:
                is_valid.scroll_count = 1 if not hasattr(is_valid, "scroll_count") else is_valid.scroll_count + 1
                if not max_scroll_elements == -1 and is_valid.scroll_count > max_scroll_elements:
                    return False
            return True

        def expand(view_port: dict, bbox: dict) -> tuple[dict, tuple[int, int]]:
            """
            Expand the bbox of the element to make more easy to do template matching.
            """
            # Choose between the element margin and 25 pixels
            assert bbox['x'] >= 0
            assert bbox['y'] >= 0
            assert bbox['x'] + bbox['width'] <= view_port['width']
            assert bbox['y'] + bbox['height'] <= view_port['height']    

            x_left_margin = min(bbox['x'], 25)
            x_right_margin = min(abs(view_port['width'] - (bbox['x'] + bbox['width'])), 25)
            x_margin = min(x_left_margin, x_right_margin)

            y_top_margin = min(abs(0 - (bbox['y'])), 25)
            y_bottom_margin = min(abs(view_port['height'] - (bbox['y'] + bbox['height'])), 25)
            y_margin = min(y_top_margin, y_bottom_margin)

            bbox['x'] -= x_margin
            bbox['y'] -= y_margin
            bbox['width'] += 2 * x_margin
            bbox['height'] += 2 * y_margin

            return bbox, (x_margin, y_margin)

        filename_screenshot = os.path.join(self.tmp_dir, f"page_screenshot.png")
        # Wait to load
        BuiltIn().sleep(5)
        page_screenshot = self.library.take_screenshot(filename_screenshot, fullPage=True)
        page_size = self.library.get_scroll_size()
        view_port_size = self.library.get_viewport_size()
        el_screenshots = []

        count = 0
        for element_xpath in self.elements_xpath:
            # Find elements with the xpath
            old_timeout = self.library.set_browser_timeout(1)  # type: ignore (is timedelta from rf)
            web_elements = self.library.get_elements(element_xpath)
            old_timeout = self.library.set_browser_timeout(old_timeout)
            max_scroll_elements = len(web_elements) // 2 if self.max_elements == -2 else self.max_elements
            # Shuffle web elements to avoid being on top of the page
            random.shuffle(web_elements)
            for element in web_elements:
                # Get button location
                try:
                    bbox_element = self.library.get_boundingbox(element)
                    bbox_element = {k: int(v) for k, v in bbox_element.items()}  # Convert all elements in bbox_element into int
                    # Look like the bbox is lightly shifted to the left. Add width to compensate
                    bbox_element['x'] += 4
                    bbox_element['width'] += 8

                    # Only elements inside page. If max_scroll_elements is -2, half of the elements are not scrollable
                    if not is_valid(page_size, view_port_size, bbox_element, max_scroll_elements):
                        continue

                    margin_xy = (0, 0)
                    if expand_bbox:
                        try:
                            bbox_element, margin_xy = expand(page_size, bbox_element)
                        except AssertionError:
                            BuiltIn().log(f"Trying to expand. Invalid bbox: {bbox_element} in viewport {page_size}. Not expanding element for template matching", 
                                level='WARN', console=True)

                    filename = self._crop_and_save(self.tmp_dir, page_screenshot, bbox_element, count, margin_xy)

                    # Not recording if is not good element
                    if not filename or not self._is_good_element(filename):
                        continue
                except Exception:
                    continue
                
                count += 1
                el_screenshots.append(filename)
        
        return el_screenshots

    def _record_elements(self, el_screenshots: list[str]):
        """
        Crawl all the elements in the page
        """
        page = Page(self.library)
        current_context = page.get_active_context()

        finish = False
        for el_screenshot in el_screenshots:
            try:
                self._seek_element_perform_action(el_screenshot)
            except Exception as e:
                BuiltIn().log(f"Error while recording action: {e}", level='WARN', console=True)
                continue
            page.restore_page(current_context)
            if finish is True:
                break

    def _seek_element_perform_action(self, element_screenshot: str, *action_args):
        """
        Performs the action on the matched element with the screenshot.
        Action must be implemented in the child class. The arguments of the action must be passed to the function.
        """
        def get_instruction(img_page: cv2.Mat, el_bbox: BBox) -> str:
            margin = 50
            x = max(0, (el_bbox.x - margin))
            y = max(0, (el_bbox.y - margin))
            width = min(img_page.shape[1], (el_bbox.x + el_bbox.width + margin)) - x
            height = min(img_page.shape[0], (el_bbox.y + el_bbox.height + margin)) - y
            bbox_page = {"x": x, "y": y, "width": width, "height": height}
            crop_page = self._crop_and_save(self.tmp_dir, page_screenshot, bbox_page, 0, (0, 0))
            return self._predict_instruction(crop_page, element_screenshot, el_bbox, *action_args)

        # Load images
        page_screenshot = self.library.take_screenshot(os.path.join(self.tmp_dir, f"page_screenshot.png"), fullPage=True)
        img_page = cv2.imread(page_screenshot)
        img_element = cv2.imread(element_screenshot)
        margin = self._get_margin_from_filename(element_screenshot)

        # Check if the element is in the page
        el_bbox = self._get_element_bbox(img_page, img_element, margin)
        if el_bbox is None:
            # Element not found
            BuiltIn().log('Element not found')
            return

        instruction = get_instruction(img_page, el_bbox)
        # Perform action
        self._action(instruction, img_element, margin, *action_args)

    def _get_text(self, element_screenshot: str) -> str:
        """
        Get all text input in the page and the label of the text input
        """
        lang = BuiltIn().get_variable_value("${LANG}", default="en")
        # Element screenshot to pillow image
        img_element = Image.open(element_screenshot)
        text = ocr.get_all_text(self.ocr_url, img_element, conf_threshold=0.8, lang=lang)
        if text is None:
            BuiltIn().log(f"Error while getting text from {element_screenshot}", level='WARN', console=True)
            return ""
        return text

    
    def _get_margin_from_filename(self, filename: str) -> tuple[int, int]:
        """
        Get the margin from the filename
        """
        if "mX_" in filename:
            filename_ext = "." + filename.split(".")[-1]
            mX = int(filename.split("mX_")[1].split("-mY_")[0])
            mY = int(filename.split("mY_")[1].split(filename_ext)[0])
            return (mX, mY)
        return (0, 0)

    @staticmethod
    def _crop_and_save(save_dir, page_screenshot, bbox_element, count, margin_xy) -> str | None:
            """
            Crop the element and save it in the tmp_dir.
            """
             # Crop bounding box in filename_screenshot
            img = cv2.imread(page_screenshot)
            bbox_element = {k: int(v) for k, v in bbox_element.items()}  # Convert all elements in bbox_element into int
            crop_img = img[bbox_element['y']:bbox_element['y']+bbox_element['height'], bbox_element['x']:bbox_element['x']+bbox_element['width']]
            # Save the cropped image
            filename = os.path.join(save_dir, f"{count}-mX_{margin_xy[0]}-mY_{margin_xy[1]}.png")
            try:
                cv2.imwrite(filename, crop_img)
            except Exception as e:
                print(e)
                return None
            return filename

    @staticmethod
    def _get_element_bbox(img_page: cv2.Mat, img_element: cv2.Mat, margin: tuple[int, int]) -> Optional[BBox]:
        def remove_margin_from_bbox(bbox: BBox, margin_x: int, margin_y: int) -> BBox:
            """
            Remove the margin from the bbox.
            """
            bbox.x += margin_x
            bbox.y += margin_y
            bbox.width -= 2 * margin_x
            bbox.height -= 2 * margin_y
            return bbox

        # Opencv template matching
        res = cv2.matchTemplate(img_page, img_element, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        # Define a threshold
        threshold = 0.8
        # Check if there is a match
        if max_val < threshold:
            return None
        # Get the BBox
        el_bbox = BBox(x=max_loc[0], y=max_loc[1], width=img_element.shape[1], height=img_element.shape[0])
        # Check if in the element_screenshot name there is the extended margin
        el_bbox = remove_margin_from_bbox(el_bbox, margin[0], margin[1])
        return el_bbox

class Page:
    """
    Class to manage the page restoration.
    """
    def __init__(self, library_instance: Browser):
        self.library = library_instance
        self.wait_to_go = 2

    def restore_page(self, context_to_restore: dict):
        new_context = self.get_active_context()
        # Check if the page has changed
        if len(new_context['pages']) != len(context_to_restore['pages']):
            # Close page
            self._close_last_opened_page(new_context)

        # Go to the previous page
        page_to_restore = self._get_active_page(context_to_restore)
        self.library.go_to(page_to_restore['url'])
        self.library.wait_until_network_is_idle()
        BuiltIn().sleep(self.wait_to_go)

    def get_active_context(self):
        # Get the active browser
        active_browser = [browser for browser in self.library.get_browser_catalog() if browser['activeBrowser']][0]
        # Get the active context
        active_context = [context for context in active_browser['contexts'] 
            if context['id'] == active_browser['activeContext']][0]

        return active_context

    def _get_active_page(self, context: dict):
        # Get the active page
        active_page = [page for page in context['pages']
            if page['id'] == context['activePage']][0]

        return active_page

    def _close_last_opened_page(self, context: dict):
        # Get the last opened page
        timestamp = 0
        last_opened_page = None
        for page in context['pages']:
            if page['timestamp'] > timestamp:
                timestamp = page['timestamp']
                last_opened_page = page
        if last_opened_page:
            self.library.close_page(last_opened_page['id'])

    def render_webpage(self, dom: str):
        """
        Not working, at least in serious pages.
        """
        self.library.evaluate_javascript(None, 'var newHTML = document.open("text/html", "replace");')
        self.library.evaluate_javascript(None, "newHTML.write('{}');".format(dom))
        self.library.evaluate_javascript(None, 'newHTML.close();')


# ============== RECORDERS ==============
class SingleClickRecorder(DataRecorderInterface):
    """
    Given a page, record all the single click events that are feasible in that page. After that,
    reset the page to its original state.
    """
    def __init__(self, library_instance: Browser, wait_go_to=2, max_scroll: int = 5, max_elements: int = -2, lang_instructions: str="en"):
        # Clicable elements
        button_xpath = ['//a', '//button']

        super().__init__(library_instance, button_xpath, wait_to_go=wait_go_to, max_scroll=max_scroll, max_elements=max_elements, lang_instructions=lang_instructions)
        self.wait_go_to = wait_go_to

    def _is_good_element(self, element_screenshot: str):
        """
        Check if the element is clickable
        """
        # Check with ocr if the element contains text
        text = self._get_text(element_screenshot)
        if not text:
            return False
        return True

    def _predict_instruction(self, screenshot_path: Optional[str], element_path: str, action_bbox: BBox):
        # Read the text of the element
        text = self._get_text(element_path)
        if self.lang_instructions == "es":
            click_str = ["Clica en", "Ir a", "Pulsa", "Accede a", ""]
        else:
            click_str = ["Click on", "Go to", "Press", "Access to", ""]
        return f"{random.choice(click_str)} {text}"
    
    def _action(self, predicted_instruction: str, img_element: cv2.Mat, el_margin: tuple[int, int]):

        # Calculate the scroll gap.
        # The scroll is done by half of the screen.
        _, height = self.library.get_client_size().values()
        scroll_gap = height // 2

        SingleClickRecorder.vars = {}
        SingleClickRecorder.vars['img_element'] = img_element
        SingleClickRecorder.vars['el_margin'] = el_margin
        SingleClickRecorder.vars['scroll_gap'] = scroll_gap

        # To run a keyword like a Task, the library must be imported.
        # Due to import library does not accept kwargs, all args must be passed
        args = (
            self.library,
            self.wait_go_to,
            self.max_scroll,
            self.max_elements,
            self.lang_instructions
        )

        # The library must be imported with the name of the library to custom the name of the Task
        BuiltIn().import_library("ButlerRobot.RecordersLibraries.SingleClickRecorder", *args, 'WITH NAME', 'SingleClickRecorder')
        passed = BuiltIn().run_keyword_and_return_status(f"SingleClickRecorder.{predicted_instruction}")
        if not passed:
            BuiltIn().run_keyword('Browser.Remove Last Task')  # self.library is Browser, but the Browser in RF is DataBrowserLibrary

    @keyword('${task_reader}')
    def rec_type_text(self, task_reader: str):	
        """
        This keyword is to unify the click and type text action. Also to rename the Task.
        """
        scroll_gap = SingleClickRecorder.vars['scroll_gap']
        img_element = SingleClickRecorder.vars['img_element']
        el_margin = SingleClickRecorder.vars['el_margin']

        bbox = None
        for _ in range(self.max_scroll):
            page_screenshot = self.library.take_screenshot()
            img_screenshot = cv2.imread(page_screenshot)
            bbox = self._get_element_bbox(img_screenshot, img_element, el_margin)
            # Search element
            if bbox:
                break
            # Scroll if not present
            BuiltIn().run_keyword("Browser.Scroll Down", scroll_gap)
        else:
            bbox = None

        if not bbox:
            BuiltIn().fail(f"Element not found in the page. Fail at: {task_reader}")
        BuiltIn().run_keyword("Browser.Click At BBox", bbox)


class TypeTextRecorder(DataRecorderInterface):
    """
    Given a page, record all the single click events that are feasible in that page. After that,
    reset the page to its original state.
    """
    def __init__(self, library_instance: Browser, num_words_per_input = 5, wait_to_go: int = 2, max_scroll: int = 5, max_elements: int = -2, lang_instructions: str="en"):
        # Text elements
        text_xpath = ['//input[@type="text"]', '//input[@type="password"]', '//input[@type="email"]', '//input[@type="number"]', '//input[@type="tel"]', '//input[@type="url"]', '//input[@type="search"]', '//textarea']
        
        super().__init__(library_instance, text_xpath, wait_to_go=wait_to_go, max_scroll=max_scroll, max_elements=max_elements, lang_instructions=lang_instructions)
        self.num_words_per_input = num_words_per_input

        # Vocabulary
        self.seed_words = ButlerRobot.vocabulary.get_vocabulary()

    # ============== Override ==============
    def record(self):
        """
        Override record method to expand the bounding box of the text element. 
        This is because the input text element is usually a white box.
        """
        elements = self._get_elements_to_record(expand_bbox=True)
        self._record_elements(elements)
    
    def _is_good_element(self, element_screenshot: str):
        return True  # All text elements are good

    def _record_elements(self, el_screenshots: list[str]):
        """
        Record all input text with multiple random words
        """
        page = Page(self.library)
        current_context = page.get_active_context()

        for el_screenshot in el_screenshots:
            # Type text in the same element with random vocabulary
            inputs = [' '.join(random.sample(self.seed_words, random.randint(1, 3))) for _ in range(self.num_words_per_input)]
            for input in inputs:
                self._seek_element_perform_action(el_screenshot, input)
                # Restore page
                page.restore_page(current_context)

    def _predict_instruction(self, screenshot_path: Optional[str], element_path: str, action_bbox: BBox, string: str):
        """
        Find the closest text to the action_bbox.
        """
        def get_texts_and_bboxes(screenshot_path: str) -> list[tuple[str, BBox]]:
            # Get text and bbox
            lang = BuiltIn().get_variable_value("${LANG}", default="en")
            img_screen = Image.open(screenshot_path)
            text_and_bboxes = ocr.get_text_and_bbox(self.ocr_url, img_screen, conf_threshold=0.8, lang=lang)
            if not text_and_bboxes:
                BuiltIn().log(f"Error while getting text from {screenshot_path}", level='WARN', console=True)
                return []
            # Return list(text, bbox) from text_and_bboxes of type tuple[list[str], list[BBox]]
            return list(zip(*text_and_bboxes))
        if self.lang_instructions == "es":
            type_str = ["Introduce el texto", "Escribe", "Pon", "Busca", "Introduce", "Escribe el texto", "Busca", "Introduce el texto"]
        else:
            type_str = ["Type text", "Write", "Put", "Search", "Type", "Write text", "Search", "Type text"]
        instruction = f"{random.choice(type_str)} {string}"
        # instruction = "Type text {0}".format(string)
        if not screenshot_path:
            return instruction

        # Only read the text one time
        image = Image.open(screenshot_path)
        img_hash = imagehash.average_hash(image)
        if not hasattr(self, 'screenshot_hash') or self.screenshot_hash != img_hash:
            self.screenshot_hash = img_hash
            self.text_bboxes = get_texts_and_bboxes(screenshot_path)

        # Find the closest text to the action_bbox
        if len(self.text_bboxes) > 0:
            # Filter text boxes that are not at top and left of the action_bbox
            candidate_text_boxes = [text_bbox for text_bbox in self.text_bboxes 
                if text_bbox[1].is_left_to(action_bbox) and text_bbox[1].is_above_of(action_bbox)]
                # Find the closest text
            if len(candidate_text_boxes) > 0:
                closest_text = min(candidate_text_boxes, key=lambda text_bbox: action_bbox.distance(text_bbox[1]))
                if self.lang_instructions == "es":
                    instruction += f" en {closest_text[0]}"
                else:
                    instruction += f" in {closest_text[0]}"

        return instruction
    
    def _action(self, predicted_instruction: str, img_element: cv2.Mat, el_margin: tuple[int, int], string: str):
        
        # Calculate the scroll gap.
        # The scroll is done by half of the screen.
        _, height = self.library.get_client_size().values()
        scroll_gap = height // 2

        # Store in class the parameters
        TypeTextRecorder.vars = {}
        TypeTextRecorder.vars['img_element'] = img_element
        TypeTextRecorder.vars['el_margin'] = el_margin
        TypeTextRecorder.vars['scroll_gap'] = scroll_gap
        TypeTextRecorder.vars['string'] = string

        # To run a keyword like a Task, the library must be imported.
        # Due to import_library doesn't accept kwargs all args must be passed in order
        # library_instance: Browser, num_words_per_input = 5, wait_to_go: int = 2, max_scroll: int = 5, max_elements: int = -2, lang_instructions: str="en"
        args = (            
            self.library,
            self.num_words_per_input,
            self.wait_to_go,
            self.max_scroll,
            self.max_elements,
            self.lang_instructions
        )

        BuiltIn().import_library("ButlerRobot.RecordersLibraries.TypeTextRecorder", *args, 'WITH NAME', 'TypeTextRecorder')
        passed = BuiltIn().run_keyword_and_return_status(f"TypeTextRecorder.{predicted_instruction}")  # Arguments are passed with a static variable in the class
        # Remove text
        self.library.keyboard_key(KeyAction.down, 'Shift')
        self.library.keyboard_key(KeyAction.press, 'Home')
        self.library.keyboard_key(KeyAction.press, 'Delete')
        self.library.keyboard_key(KeyAction.up, 'Shift')
        
        if not passed:
            BuiltIn().run_keyword('Browser.Remove Last Task')  # self.library is Browser, but the Browser in RF is DataBrowserLibrary
    
    @keyword('${task_reader}')
    def rec_type_text(self, task_reader: str):	
        """
        This keyword is to unify the click and type text action. Also to rename the Task.
        """
        scroll_gap = TypeTextRecorder.vars['scroll_gap']
        img_element = TypeTextRecorder.vars['img_element']
        el_margin = TypeTextRecorder.vars['el_margin']

        bbox = None
        for _ in range(self.max_scroll):
            page_screenshot = self.library.take_screenshot()
            img_screenshot = cv2.imread(page_screenshot)
            bbox = self._get_element_bbox(img_screenshot, img_element, el_margin)
            # Search element
            if bbox:
                break
            # Scroll if not present
            BuiltIn().run_keyword("Browser.Scroll Down", scroll_gap)
        else:
            bbox = None

        if not bbox:
            BuiltIn().fail(f"Element not found in the page. Fail at: {task_reader}")
        # Click element
        BuiltIn().run_keyword("Browser.Click At BBox", bbox)
        # Type text
        BuiltIn().run_keyword("Browser.Keyboard Input", KeyboardInputAction.type, TypeTextRecorder.vars['string'])

