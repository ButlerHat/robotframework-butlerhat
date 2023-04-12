import os
import requests
import copy
import base64
import io
import time
from PIL import Image
from enum import Enum, auto
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from Browser import Browser
from Browser.utils.data_types import ScreenshotReturnType
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
            return ('Click At BBox', bbox)
        elif "input" in action_lower:
            # Input text in this format: 'action: Input Text "text"'
            text = action.split('"')[1].strip()
            return ('Keyboard Input', 'type', text)
        elif "scroll" in action_lower:
            _, height = self._library.get_client_size().values()
            scroll_gap = height // 2
            return ('Browser.Scroll Down', scroll_gap)
        else:
            return (action_lower,)


class AIBrowserLibrary(DataBrowserLibrary):

    def __init__(
            self, 
            ai_url='http://nginx_udop:5000/predict_rf', 
            ocr_url="http://nginx_udop:80/fd/ppocrv3",
            max_steps=5, 
            with_tasks=False, 
            fix_bbox=False,
            save_screenshots=False,
            *args, 
            **kwargs):
        # ia_url is nginx because the service mode
        super().__init__(*args, **kwargs)
        self.ai_url = ai_url
        self.max_steps = max_steps
        self.with_tasks = with_tasks
        self.fix_bbox = fix_bbox
        self.save_screenshots = save_screenshots

        # Ocr url
        self.ocr_url = ocr_url
        
        # Hugging face API Token
        self.hf_token = os.environ.get('HF_TOKEN', None)

    # Overwrites
    def _get_dom(self):
        return ''
    
    def _wait_for_browser(self):
        pass
        BuiltIn().sleep(1)  # Less than recording

    def _get_bbox_and_pointer(self, selector: str | BBox) -> tuple[None, None] | tuple[BBox, tuple]:
            """
            This method gets the BBox and pointer of a selector.
            """
            # When is a BBox selector
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
                    return (bbox, (bbox.x + bbox.width/2, bbox.y + bbox.height/2))
                else:
                    raise ValueError(f"Invalid BBox selector: {selector}")
            # When is a xpath (or any) selector
            elif isinstance(selector, str):
                str_selector: str = str(selector)
                return self._get_selector_pointer_and_bbox(str_selector)
            else:
                return None, None
    
    def _get_selector_pointer_and_bbox(self, selector: str) -> tuple[None, None] | tuple[BBox, tuple[float, float]]:
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
                Instruction: {instruction}. 

                Selected element OCR: {ocr_element}

                Answer with "yes" or "no". Is the selected element the correct for the instruction?
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
    def _set_mode(mode: str) -> AIMode:
        if 'flexible' in mode.lower():
            return AIMode.flexible
        elif 'strict' in mode.lower():
            return AIMode.strict
        elif 'critical' in mode.lower():
            return AIMode.critical
        else:
            return AIMode.strict
        
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
            fixed_bbox: BBox = self._get_element_bbox_from_pointer(*pointer_xy)
            bbox: BBox = fixed_bbox if fixed_bbox else bbox
            elemnt_img_str = self._library.take_screenshot(crop=bbox.to_dict(), return_as=ScreenshotReturnType.base64)
            # Save the image with pillow
            if self.save_screenshots:
                img = Image.open(io.BytesIO(base64.b64decode(elemnt_img_str)))
                img.save(f'{self._library.outputdir}/{time.time()}.png')

            element_txt = get_all_text(self.ocr_url, elemnt_img_str)
            if not element_txt:
                error, error_msg = True, f'{error_msg} No text found in the element. The action is: {action_and_args}'
            
            assert element_txt is not None, 'Element_txt must be not None at this point'
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
            last_action = ai_task.steps[-1]
            task_history: list[PromptStep] = AIExampleBuilder(root_task, self.with_tasks).build_history(last_action)
        else:
            msg = f'AI reached the max number of steps: {self.max_steps}'
            if kw_mode == AIMode.critical:
                BuiltIn().fail(msg)
            BuiltIn().log(msg, level='WARN', console=True)
            # Go to the top of the page
            self._scroll_to_top()
            