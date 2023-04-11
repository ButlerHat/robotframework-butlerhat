import requests
import copy
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from Browser import Browser
from .DataBrowserLibrary import DataBrowserLibrary
from .src.data_types import PageAction, Step, Task, BBox
from .src.data_to_ai.data_example_builder import AIExampleBuilder
from .src.data_to_ai.data_types import PromptStep

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
            max_steps=5, 
            with_tasks=False, 
            fix_bbox=False,
            *args, 
            **kwargs):
        # ia_url is nginx because the service mode
        super().__init__(*args, **kwargs)
        self.ai_url = ai_url
        self.max_steps = max_steps
        self.with_tasks = with_tasks
        self.fix_bbox = fix_bbox

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

    @keyword('AI.${task}', tags=['task'])  # Tag for recording in data
    def ai_task(self, task):
        """
        Run the task on the AI
        """
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
            BuiltIn().run_keyword(*action_and_args)

            # Update the image
            image = self.last_observation.screenshot
            # Update the task history
            last_action = ai_task.steps[-1]
            task_history: list[PromptStep] = AIExampleBuilder(root_task, self.with_tasks).build_history(last_action)
            