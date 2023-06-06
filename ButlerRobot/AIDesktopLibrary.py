import os
import re
import requests
import copy
from enum import Enum, auto
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from RPA.Desktop import Desktop
from .DataDesktopLibrary import DataDesktopLibrary
from .src.data_types import Step, Task, BBox
from .src.data_to_ai.data_example_builder import AIExampleBuilder
from .src.data_to_ai.data_types import PromptStep


class AIMode(Enum):
    """Enum that represents if the action is flexible, strict or critical"""
    flexible = auto()  # Don't check anything
    strict = auto()  # Only perform the action if the element has the text of the instruction
    critical = auto()  # Same as strict but fails
    

class IAToRFParser:
    def __init__(self, library: Desktop):
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
            return ('Desktop.Click At BBox', bbox)
        elif "input" in action_lower:
            # Input text in this format: 'action: Input Text "text"'
            text = action.split('"')[1].strip()
            return ('Desktop.Type text', text)
        elif "scroll" in action_lower:
            return ('Desktop.Scroll Down',)
        else:
            return (action_lower,)


class AIDesktopLibrary(DataDesktopLibrary):

    def __init__(
            self, 
            ai_url=None, 
            ocr_url=None,
            wait_for_browser=None,
            max_steps=5, 
            with_tasks=False,
            save_screenshots=False,
            *args, 
            **kwargs):
        # ia_url is nginx because the service mode
        self.ai_url = ai_url if ai_url else os.environ.get('AI_URL', 'http://ai.butlerhat.com/predict_rf')
        self.max_steps = max_steps
        self.with_tasks = with_tasks
        self.save_screenshots = save_screenshots
        self.wait_time = wait_for_browser

        # Ocr url
        self.ocr_url = ocr_url if ocr_url else os.environ.get('OCR_URL', 'http://ocr.butlerhat.com/fd/ppocrv3')
        
        # Hugging face API Token
        self.hf_token = os.environ.get('HF_TOKEN', None)

        # Init Desktop
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
        BuiltIn().run_keyword(*action_and_args)
        return
        # Do not check now. Support only flexible


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
            