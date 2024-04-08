import os
import re
import requests
import copy
import base64
import io
import time
from dataclasses import asdict
from PIL import Image
from enum import Enum, auto
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from Browser import Browser
from Browser.utils.data_types import ScreenshotReturnType, BoundingBox
from .DataBrowserLibrary import DataBrowserLibrary
from .src.data_types import PageAction, Step, Task, BBox
from .src.data_to_ai.data_example_builder import AIExampleBuilder
from .src.data_to_ai.data_types import PromptStep
from .src.utils.ocr import get_all_text


class AIMode(Enum):
    """Enum that represents if the action is flexible, strict or critical"""
    flexible = auto()  # Don't check anything
    strict = auto()  # Only perform the action if the element has the text of the instruction
    critical = auto()  # Same as strict but fails
    

class IAToRFParser:
    def __init__(self, library: Browser):
        self._library = library
        pass

    def parse(self, action: str):
        """
        Parse the action from the AI to a Robot Framework instruction
        """
        action_lower = action.strip().lower()
        if "click" in action_lower:
            # Click in this format: 'action: Click At Bbox (x1=87, y1=146, x2=197, y2=175)'
            bbox: BBox = BBox.from_rf_string(action_lower)
            # BBox is in format (x1, y1, x2, y2) but Robot Framework needs (x, y, width, height)
            bbox.width = bbox.width - bbox.x
            bbox.height = bbox.height - bbox.y
            return ('Browser.Click At BBox', bbox)
        elif "input" in action_lower:
            # Input text in this format: 'action: Input Text "text"'
            text = action.split('"')[1].strip()
            return ('Browser.Keyboard Input', 'type', text)
        elif "scroll" in action_lower:
            _, height = self._library.get_client_size().values()
            scroll_gap = height // 2
            return ('Browser.Scroll Down', scroll_gap)
        elif "key" in action_lower:
            keys = action.split('"')[1].strip()
            # Replace Ctrl with Control, case insensitive
            keys = keys.replace('ctrl', 'Control').replace('Ctrl', 'Control')
            return ('Browser.Keyboard Key', keys)
        else:
            return (action_lower,)


class AIBrowserLibrary(DataBrowserLibrary):

    def __init__(
            self, 
            ai_url=None, 
            ocr_url=None,
            wait_for_browser=None,
            max_steps=5, 
            with_tasks=False, 
            fix_bbox=True,
            save_screenshots=False,
            presentation_mode=False,
            *args, 
            **kwargs):
        # ia_url is nginx because the service mode
        self.ai_url = ai_url if ai_url else os.environ.get('AI_URL', 'http://ai.butlerhat.com/predict_rf')
        self.max_steps = max_steps
        self.with_tasks = with_tasks
        self.fix_bbox = fix_bbox
        self.save_screenshots = save_screenshots
        self.wait_time = wait_for_browser
        self.presentation_mode = presentation_mode
        self.is_bbox_printed = False

        # Ocr url
        self.ocr_url = ocr_url if ocr_url else os.environ.get('OCR_URL', 'http://ocr.butlerhat.com/fd/ppocrv3')
        
        # Hugging face API Token
        self.hf_token = os.environ.get('HF_TOKEN', None)

        # Init Browser
        super().__init__(*args, **kwargs)

    @property
    def _wait(self):
        if self.wait_time is None:
            self.wait_time = BuiltIn().get_variable_value('${ROBOT_BROWSER_WAIT}', 2)
        return self.wait_time

    # Overwrites    
    def _get_dom(self):
        return ''
    
    def _wait_for_browser(self):
        pass
        BuiltIn().sleep(self._wait)  # Less than recording

    def _start_suite(self, name, attrs):
        # Check if can access to the AI
        try:
            response = requests.get(self.ai_url.split('.com')[0] + '.com/auth')  # Temporary fix
        except requests.exceptions.ConnectionError:
            raise Exception(f"Can't connect to the AI URL. Contact with the administrator.")
        if response.status_code != 200:
            raise Exception(f"Can't access to the AI URL. Contact with the administrator.")
        # Check if in the json response is {"auth": True}
        if not response.json().get('auth', False):
            raise Exception(f"The use of the framework is not authorized. Contact with the administrator.")
        
        return super()._start_suite(name, attrs)

    def _pre_run_keyword(self) -> None:
        """
        Remove element with id=highlightDivBH
        """
        # Remove highlightDivBH. This only happens when is not recording
        if self.presentation_mode and self.is_bbox_printed:
            assert not self.record, f"This should not happen when recording. Flag of is_bbox_printed: {self.is_bbox_printed}, Flag of record: {self.record}"
            BuiltIn().sleep(0.2)
            self._library.evaluate_javascript(None, "document.getElementById('highlightDivBH').remove();")
            self.is_bbox_printed = False
        super()._pre_run_keyword()

    def _get_bbox_and_pointer(self, selector: str | BBox) -> tuple[None, None] | tuple[BBox, tuple]:
            """
            This method gets the BBox and pointer of a selector.
            """
            # When is a BBox selector. When is this case, let's assume that there is no need to scroll
            if isinstance(selector, str) and selector.startswith("BBox") or isinstance(selector, BBox):
                bbox: BBox = BBox.from_rf_string(selector) if isinstance(selector, str) else selector
                pointer_xy = (int(bbox.x + bbox.width/2), int(bbox.y + bbox.height/2))

                # Correct BBox if is recording
                if self.fix_bbox:
                    bbox_corrected: BBox | None = self._get_element_bbox_from_pointer(*pointer_xy)
                    if bbox_corrected:
                        bbox = bbox_corrected
                        pointer_xy = (bbox.x + bbox.width/2, bbox.y + bbox.height/2)
                
                if bbox is not None:
                    r_bbox, r_pointer_xy = (bbox, (bbox.x + bbox.width/2, bbox.y + bbox.height/2))
                else:
                    raise ValueError(f"Invalid BBox selector: {selector}")
            # When is a xpath (or any) selector
            elif isinstance(selector, str):
                str_selector: str = str(selector)
                r_bbox, r_pointer_xy = super()._retrieve_bbox_and_pointer_from_page(str_selector)
            # It is not a string, so it is a browser type like KeyAction
            else:
                return None, None
            
            if not r_bbox:
                assert r_pointer_xy is None, f'r_pointer_xy must be None if r_bbox is None. r_pointer_xy: {r_pointer_xy}'
                return r_bbox, r_pointer_xy
            
            # Show bbox in the page
            if self.presentation_mode:
                self._library.printBoundingBox(r_bbox.x, r_bbox.y, r_bbox.width, r_bbox.height)
                # If is recording remove the bbox to don't affect observation
                if self.record:
                    BuiltIn().sleep(0.2)
                    self._library.evaluate_javascript(None, "document.getElementById('highlightDivBH').remove();")
                else:
                    self.is_bbox_printed = True
            return r_bbox, r_pointer_xy  # type: ignore
    
    def _retrieve_bbox_and_pointer_from_page(self, selector: str) -> tuple[None, None] | tuple[BBox, tuple[float, float]]:
        # If not is a control of the selector, this function takes too much time
        if not selector or selector.lower() in ['type']:
            # Skip Keyboard Input  type  text
            return None, None
        try:
            web_element = self._library.get_element(selector)
            bbox = self._library.get_boundingbox(web_element)
            return (
                BBox(**bbox),
                (bbox['x'] + bbox['width'] / 2,  bbox['y'] + bbox['height'] / 2)
            )
        except:
            if self.fix_bbox:
                BuiltIn().log(f'Element not found: {selector}', level='DEBUG')
            return None, None
        
    def _add_scroll_when_recording(self, step: PageAction):
        # Check if step.name starts with 'AI'
        if not step.name.startswith('AI'):
            return super()._add_scroll_when_recording(step)
        else:
            # For time saving
            raise NotImplementedError('Not is a recorder library')

    def _is_correct_element(self, instruction: str, ocr_element: str) -> bool:
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        headers = {"Authorization": f"Bearer {self.hf_token}"}

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
        
        BuiltIn().log(f"Waiting for T5 response. Checking element: {ocr_element}, Instruction: {instruction}", level='DEBUG', console=self.console)
        output = query({
            "inputs": f"""
                Answer with "yes" or "no". Is the selected element the correct for the instruction?

                Example:
                Instruction: Click on accept. 
                Selected element OCR: aceptar.
                Answer: yes

                Instruction: Click on cookies policy. 
                Selected element OCR: accept cooki.
                Answer: no

                Instruction: Click on "informes" in the top menu 
                Selected element OCR: Informacion genera.
                Answer: no

                Instruction: Go to inventario. 
                Selected element OCR: Inventaric.
                Answer: yes

                Instruction: {instruction}. 
                Selected element OCR: {ocr_element}.
                Answer:
            """,
            "options": {
                "wait_for_model": True
            }
        })
        if isinstance(output, list):
            output = output[0]
        if 'generated_text' not in output:
            BuiltIn().log(f"Error in T5 response: {output}", level='WARN', console=self.console)
            return False
        BuiltIn().log(f"T5 response for element check: {output['generated_text'].strip()}, Instruction: {instruction}, Ocr element: {ocr_element}", level='DEBUG', console=self.console)
        return "yes" in output['generated_text'].strip().lower()


    @staticmethod
    def _set_mode(mode_in_prompt: str) -> AIMode:
        if not 'flexible' in mode_in_prompt.lower() and not 'strict' in mode_in_prompt.lower() and not 'critical' in mode_in_prompt.lower():
            mode_in_prompt = BuiltIn().get_variable_value('${DEFAULT_AI_MODE}', 'flexible')
        
        if 'flexible' in mode_in_prompt.lower():
            return AIMode.flexible
        elif 'strict' in mode_in_prompt.lower():
            return AIMode.strict
        elif 'critical' in mode_in_prompt.lower():
            return AIMode.critical
        else:
            BuiltIn().fail(f"Invalid mode: {mode_in_prompt}. Using default mode: strict")
            assert False, "Invalid mode"  # For type checking

    def _sleep_before_execution(self, mode_in_prompt: str):
        if 'wait' in mode_in_prompt.lower():
            # Get with regex the number after wait
            sleep_time = re.findall(r'wait\s*(\d+)', mode_in_prompt.lower())
            # Sleep 1 seconds by default
            sleep_time = int(sleep_time[0]) if sleep_time else 1
            BuiltIn().run_keyword('Sleep', sleep_time)

        
    def _run_action(self, instruction: str, action_and_args: tuple, mode: AIMode):
        # If the action is flexible don't check
        if mode == AIMode.flexible:
            BuiltIn().run_keyword(*action_and_args)
            return
        
        # If the acition is strict or critical check if is a click
        if 'click' not in action_and_args[0].lower():
            BuiltIn().run_keyword(*action_and_args)
            return

        # Check the text of the selected element.
        error, error_msg = False, f"Doing nothing. Mode Strict:" if mode == AIMode.strict else f"Failing. Mode Critical:" 
        if len(action_and_args) <= 1:
            error, error_msg = True, f'{error_msg} The click must have at least 1 arguments. The action is: {action_and_args}'
            
        # Check if the element is the correct with the text
        if not error:
            # Fix bbox to fit the element
            bbox: BBox = BBox.from_rf_string(action_and_args[1]) if isinstance(action_and_args[1], str) else action_and_args[1]
            pointer_xy = (int(bbox.x + bbox.width/2), int(bbox.y + bbox.height/2))
            fixed_bbox: BBox | None = self._get_element_bbox_from_pointer(*pointer_xy)
            bbox: BBox = fixed_bbox if fixed_bbox else bbox
            elemnt_img_str = self._library.take_screenshot(crop=BoundingBox(**asdict(bbox)), return_as=ScreenshotReturnType.base64)
            # Save the image with pillow
            if self.save_screenshots:
                img = Image.open(io.BytesIO(base64.b64decode(elemnt_img_str)))
                img.save(f'{self._library.outputdir}/{time.time()}.png')

            # Check the text of the element to know if is the correct
            element_txt = get_all_text(self.ocr_url, elemnt_img_str)
            if not element_txt:
                error, error_msg = True, f'{error_msg} No text found in the element. The action is: {action_and_args}'
            
            assert not error and element_txt is not None, f'Element_txt must be not None at this point. Error: {error}, element_txt: {element_txt}'
            if not error and self._is_correct_element(instruction, element_txt):
                BuiltIn().run_keyword(*action_and_args)
                return
            else:
                error, error_msg = True, f'{error_msg} The text of the element ({element_txt}) is not correct. The action is: {action_and_args}'
        
        if mode == AIMode.strict:
            BuiltIn().log(error_msg, level='WARN', console=True)
        else:
            BuiltIn().fail(error_msg)
        

    @keyword('AI${mode}.${task}', tags=['task'])  # Tag for recording in data
    def ai_task(self, mode: str, task: str):
        """
        Run the task on the AI
        """
        kw_mode: AIMode = self._set_mode(mode)
        self._sleep_before_execution(mode)

        root_: Step = self.exec_stack.get_root()
        ai_task_: Step = self.exec_stack.get_last_step()
        assert isinstance(root_, Task), 'The first task must be a Task'
        assert isinstance(ai_task_, Task), 'This keyword must be a Task'
        # Use deepcopy to avoid change the original task
        root_task: Task = copy.deepcopy(root_)
        ai_task: Task = ai_task_
        root_task.steps.append(ai_task)
        # Change name of ai_task
        ai_task.name = task
        task_history: list[PromptStep] =  AIExampleBuilder(root_task, self.with_tasks).build_history(ai_task)
        image: str = self.last_observation.screenshot  # Image in base64

        for _ in range(self.max_steps):
            # Send the request to the AI in a POST request.
            list_tasks = [step.to_dict() for step in task_history]
            response = requests.post(self.ai_url, json={'image': image, 'instruction_history': list_tasks})
            response.raise_for_status()
            response = response.json()

            # Parse the response
            parser = IAToRFParser(self._library)
            action_and_args = parser.parse(response['action'])
            if action_and_args is None:
                BuiltIn().fail(f'AI returned an invalid action: {response["action"]}')
            if 'end' in action_and_args[0].lower():
                return
            
            # Run the action
            self._run_action(ai_task.name, action_and_args, kw_mode)

            # Update the image
            image = self.last_observation.screenshot
            # Update the task history
            if ai_task.steps:
                last_action = ai_task.steps[-1]
            else:
                # Could be no action if is strict so last_action is ai_task
                last_action = ai_task
            task_history: list[PromptStep] = AIExampleBuilder(root_task, self.with_tasks).build_history(last_action)
        else:
            msg = f'AI reached the max number of steps: {self.max_steps}'
            if kw_mode == AIMode.critical:
                BuiltIn().fail(msg)
            BuiltIn().log(msg, level='WARN', console=True)
            # Go to the top of the page
            self._scroll_to_top()
            