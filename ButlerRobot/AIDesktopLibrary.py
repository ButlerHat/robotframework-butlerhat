import os
import re
import requests
import copy
from typing import Optional
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
    def __init__(self, library: Desktop, offset: int = 0, direction: str = 'none'):
        self._library = library
        self.offset = offset
        self.direction = direction

    def parse(self, action: str):
        """
        Parse the action from the AI to a Robot Framework instruction
        """
        action_lower = action.strip().lower()
        bbox: Optional[BBox] = None
        if 'bbox' in action_lower:
            bbox = BBox.from_rf_string(action_lower)
            # BBox is in format (x1, y1, x2, y2) but Robot Framework needs (x, y, width, height)
            bbox.width = bbox.width - bbox.x
            bbox.height = bbox.height - bbox.y
            if self.offset != 0:
                if self.direction == 'arriba':
                    bbox.y = bbox.y - self.offset
                elif self.direction == 'abajo':
                    bbox.y = bbox.y + self.offset
                elif self.direction == 'izquierda':
                    bbox.x = bbox.x - self.offset
                elif self.direction == 'derecha':
                    bbox.x = bbox.x + self.offset

        if "click" in action_lower:
            assert bbox is not None, f'Click action needs a bbox: {action}'
            return ('Desktop.Click At BBox', bbox)
        elif "input" in action_lower:
            # Input text in this format: 'action: Input Text "text"'
            text = action.split('"')[1].strip()
            return ('Desktop.Keyboard Input', text)
        elif "key" in action_lower:
            # Key in this format: 'action: Keyboard Key "key"'
            key = action_lower.split('"')[1].strip()
            keys = key.split('+')
            # Convert control to ctrl in the same position
            if 'control' in keys:
                keys[keys.index('control')] = 'ctrl'
            return ('Desktop.Press Keys', *keys)
        elif "scroll" in action_lower and "up" in action_lower and "bbox" in action_lower:
            assert bbox is not None, f'Scroll up action needs a bbox: {action}'	
            return ('Desktop.Scroll Up At BBox', bbox)
        elif "scroll" in action_lower and "down" in action_lower and "bbox" in action_lower:
            assert bbox is not None, f'Scroll down action needs a bbox: {action}'	
            return ('Desktop.Scroll Down At BBox', bbox)
        elif "scroll" in action_lower and "up" in action_lower:
            return ('Desktop.Scroll Up',)
        elif "scroll" in action_lower and "down" in action_lower:
            return ('Desktop.Scroll Down',)
        else:
            return (action_lower,)


class AIDesktopLibrary(DataDesktopLibrary):

    def __init__(
            self,
            compute_offset: bool = False,
            ai_url=None, 
            ocr_url=None,
            wait_for_browser=None,
            max_steps=5, 
            with_tasks=False,
            save_screenshots=False,
            *args, 
            **kwargs):
        self.compute_offset = compute_offset
        # ia_url is nginx because the service mode
        self.ai_url = ai_url if ai_url else os.environ.get('AI_URL', 'http://ai_demo.butlerhat.com/predict_rf')
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
    

    def obtain_offset_spanish(self, instruction: str) -> tuple[str, int, str]:
        """
        Obtain the offset of the instruction in spanish.
        Return a tuple with the instruction, the offset and the direction.
        :param instruction: Instruction to obtain the offset
        :return: Tuple with the instruction, the offset and the direction. The direction can be: arriba, abajo, izquierda, derecha, none
        """
        API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom"
        headers = {"Authorization": f"Bearer {self.hf_token}"}

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
        
        BuiltIn().log(f"Waiting for model response. Checking instruction: {instruction}", level='DEBUG', console=self.console)
        output = query({
            "inputs": f"""
                Obten el offset de la frase si lo tiene y reescribela para quitar la inforación del offset?

                Ejemplo:
                Instruccion: clica en el boton aceptar 10 pixeles a la derecha
                Respuesta: clica en el boton aceptar
                Offset: 10 derecha

                Instruccion: pulsa en cargar archivo pero 25 a la izquierda
                Respuesta: pulsa en cargar archivo
                Offset: 25 izquierda

                Instruccion: clica 20 más a arriba en bookmarks
                Respuesta: clica en bookmarks
                Offset: 20 arriba

                Instruccion: clica buscar vuelos
                Respuesta: clica buscar vuelos
                Offset: 0

                Instruccion: selecciona el elemento inventario 10 pixeles más abajo
                Respuesta: selecciona el elemento inventario
                Offset: 10 abajo

                Instruccion: {instruction}
            """,
            "options": {
                "wait_for_model": True
            }
        })
        if isinstance(output, list):
            output = output[0]
        if 'generated_text' not in output:
            BuiltIn().log(f"Error in T5 response: {output}", level='WARN', console=self.console)
            return (instruction, 0, 'none')
        BuiltIn().log(f"Response for element check: {output['generated_text'].strip()}, Instruction: {instruction}", level='DEBUG', console=self.console)
        response: str = output['generated_text'].strip()
        
        # Get the prediction. Is after Instruction: {instruction} and before next Instruction:
        prediction = response.split(f'Instruccion: {instruction}')[1].split('Instruccion:')[0]
        
        # Get the offset after Offset:
        offset = re.findall(r'Offset:\s*(\d+)', prediction)
        offset = int(offset[0]) if offset else 0
        # Get the direction (arriba, abajo, izquierda, derecha) after Offset:
        direction = re.findall(r'Offset:\s*\d+\s*(\w+)', prediction)
        direction = str(direction[0]) if direction else 'none'
        # Get the instruction after Respuesta: and before Offset:
        new_instruction = re.findall(r'Respuesta:\s*(.+)\s*Offset:', prediction)
        new_instruction = str(new_instruction[0]) if new_instruction else instruction
        return (new_instruction, offset, direction)


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

    def _continue_scrolling(self, i: int, action: str):
        """
        Limit the number of scrolls to 1.
        TODO: Do a mode to limit scrolls and let the second prediction be an action
        other than scroll.
        """
        return not('scroll' in action.lower() and i > 0)
    
    def _remove_spanish_characters(self, instruction: str) -> str:
        """
        Replace spanish characters from the instruction. Including accents and ñ.
        """
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
            "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U",
            "ñ": "n", "Ñ": "N"
        }

        # Use maketrans() to create a translation table
        trans_table = str.maketrans(replacements)

        # Use the translation table to replace the characters in the text
        text = instruction.translate(trans_table)

        return text

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
        # TODO: Filter the offset of the instruction
        conv_task = self._remove_spanish_characters(task)
        if 'ir atras' in conv_task.lower() or 've atras' in conv_task.lower() or 'atras' == conv_task.lower():
            self.go_back()
        if self.compute_offset:
            instruction, offset, direction = self.obtain_offset_spanish(task)
        else:
            instruction, offset, direction = task, 0, 'none'
        
        # Change name of ai_task
        conv_task = self._remove_spanish_characters(instruction)
        ai_task.name = conv_task
        task_history: list[PromptStep] =  AIExampleBuilder(root_task, self.with_tasks).build_history(ai_task)
        image: str = self.last_observation.screenshot  # Image in base64

        for i in range(self.max_steps):
            # Send the request to the AI in a POST request.
            list_tasks = [step.to_dict() for step in task_history]
            response = requests.post(self.ai_url, json={'image': image, 'instruction_history': list_tasks})
            response.raise_for_status()
            response = response.json()

            # Parse the response
            parser = IAToRFParser(self._library, offset, direction)
            action_and_args = parser.parse(response['action'])
            if action_and_args is None:
                BuiltIn().fail(f'AI returned an invalid action: {response["action"]}')
            if 'end' in action_and_args[0].lower():
                return
            
            # TODO: Review scrolls
            if not self._continue_scrolling(i, action_and_args[0]):
                BuiltIn().log('Stop instruction to avoid more scrolling', level='DEBUG')
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
            