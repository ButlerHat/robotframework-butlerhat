import os
import sys
import subprocess
import json
import pickle
import dataclasses
import inspect
from datetime import datetime
from typing import Optional
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from robot.running.arguments.embedded import EmbeddedArguments
# Install with pip install -e .
# Needs this import to be able to reuse pickle
from .src.data_types import BBox, Observation, Context, Step, PageAction, Task, DomSet, SaveStatus


class ExecStack:
    def __init__(self):
        self.stack: list[Step] = []

    def get_stack(self):
        return self.stack

    def get_root(self):
        assert not self.is_empty(), "Error getting root. Stack is empty."
        return self.stack[0]
    
    def get_last_step(self):
        assert not self.is_empty(), "Error getting last step. Stack is empty."
        return self.stack[-1]
    
    def is_empty(self):
        return len(self.stack) == 0
    
    def add_to_parent(self, step: Step):
        if not isinstance(self.stack[-1], Task):
            raise Exception(f"Keyword {self.stack[-1].name} is not a Task. Last step in stack is not a Task")
        # Get the last task that has not only_steps status
        for i in range(1, len(self.stack) + 1):
            # Check if step is a task
            if isinstance(self.stack[-i], Task):
                if self.stack[-i].status != SaveStatus.only_substeps:
                    self.stack[-i].steps.append(step)  # type: ignore
                    return self
        else:
            raise Exception("Fail adding step to parent. No Task found in stack without only_substeps status")
    
    def push(self, step: Step):
        self.stack.append(step)
        return self

    def pop(self):
        return self.stack.pop()
    
    def remove_last_step_from_last_task(self) -> tuple[bool, str]:
        if not self.is_empty():
            last_task: Optional[Task] = None
            # Get last task
            for i in range(len(self.stack)-1, 0, -1):
                # Check if step is a task
                step = self.stack[i]
                if isinstance(step, Task):
                    last_task = step
            if last_task is None:
                return False, "No task found in stack"
            
            if len(last_task.steps) > 0:
                # Remove last step
                step_removed = last_task.steps.pop()
                return True, f"Removed {step_removed.name} from task {last_task.name}"
            else:
                return False, f"Task {last_task.name} has no steps. Doing nothing."
            
        else:
            return False, "Stack is empty. Doing nothing."
        
    def remove_action(self):
        """
        Replace a keyword with another.
        """
        assert not self.is_empty(), 'Trying to replace a keyword. The stack is empty'
        # Get bbox where to click
        assert isinstance(self.get_last_step(), PageAction), 'Trying to replace a keyword. The last step in the stack is not a PageAction'
        # Remove this action from the stack
        current_action: PageAction = self.stack.pop()  # type: ignore

        return current_action
    

class DataWrapperLibrary:
    """
    This libray is the base class for all the libraries that wrap a browser. 
    It records two types of Steps:
    - PageAction: A PageAction is an action that is executed in the browser.
    - Task: A task is a set of PageAction or/and Tasks that are executed in the browser.

    This library assigns the type of the step depending on this rules:
    
    - PageAction: If the keyword is named and executed with the same name as the library that implements.
        Example: 
            1. Import DataBrowserLibrary as Browser. 
            2. Call the keyword `Browser.Click`. (Click must be in action_keywords list -> Declared in DataBrowserLibrary)
        Justification: This is done to use already implemented tests with Browser or SeleniumLibrary.
    
    - Task: If the Keyword is called without a library name (It means that that keyword is declared in the .robot file)
            If the Keyword is called with a library includen in task_libraries list. It can be added with the method `add_task_library`.
        Example:
            1. Import LibraryWithKeywords. -> LibraryWithKeywords is added to task_libraries list in the top of this file.
            2. Call the keyword `LibraryWithKeywords.Keyword`. All the PageAction in this keyword will be recorded as normal Page Action inside this Task.
    
    - Ignored: Keywords that are not in the action_keywords list and are not in the task_libraries list.
        Example: 
            1. Import DataBrowserLibrary as Browser.
            2. Call the keyword `Browser.Open Browser`. (Open is not in action_keywords list)

            1. Import LibraryWithKeywords.
            2. Call the keyword `LibraryWithKeywords.Keyword`. (LibraryWithKeywords is not in task_libraries list)

    """


    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LISTENER_API_VERSION = 2

    # ====== UNDEFINED METHODS ======

    def _get_screenshot(self, selector: Optional[str]=None) -> str:
        raise NotImplementedError

    def _is_browser_open(self) -> bool:
        raise NotImplementedError

    def _get_action_tags(self) -> list[str]:
        raise NotImplementedError

    def _get_exclude_tags(self):
        return self.exclude_tags
    
    def _get_exclude_tasks(self):
        return self.exclude_tasks
    
    def _get_exclude_types(self):
        return self.exclude_types

    def _get_dom(self) -> str:
        raise NotImplementedError
    
    def _wait_for_browser(self) -> None:
        raise NotImplementedError
    
    def _retrieve_bbox_and_pointer_from_page(self, selector: str) -> tuple[BBox, tuple]:
        raise NotImplementedError
    
    def _get_viewport(self) -> dict:
        """
        Returns the viewport of the browser.
        Format: {"width": width, "height": height}
        """
        raise NotImplementedError
    
    def _run_scroll(self, selector: str) -> None:
        raise NotImplementedError
    
    def _scroll_to_top(self) -> None:
        raise NotImplementedError

    def _get_key_from_keyword(self, keyword):
        return keyword.lower().replace(" ", "").replace("_", "")

    def _get_observation(self) -> Observation:
        """
        This method crates an Observation. The page must be open.
        """
        # Check if dom exists in set to save space disk
        dom = self._get_dom()
        dom = self.dom_set.add_dom(dom)
        
        return Observation(
            datetime.now(),
            self._get_screenshot(), 
            dom, 
            self.last_pointer_xy
        )
    
    def _get_bbox_and_pointer(self, selector: str | BBox) -> tuple[None, None] | tuple[BBox, tuple]:
            """
            This method gets the BBox and pointer of a selector.
            """
            # When is a BBox selector
            if isinstance(selector, str) and selector.startswith("BBox") or isinstance(selector, BBox):
                bbox: BBox = BBox.from_rf_string(selector) if isinstance(selector, str) else selector
                
                if bbox is not None:
                    return (bbox, (bbox.x + bbox.width/2, bbox.y + bbox.height/2))
                else:
                    raise ValueError(f"Invalid BBox selector: {selector}")
            # When is a xpath (or any) selector
            else:
                str_selector: str = str(selector)
                return self._retrieve_bbox_and_pointer_from_page(str_selector)
            
    def _update_observation_and_set_in_parents(self, observation: Observation | None = None) -> None:
            self.last_observation = self._get_observation() if observation is None else observation
            
            # Update observation to inmediate parents with no steps
            for prev_step_idx in range(len(self.exec_stack.get_stack())-1, 0, -1):
                prev_step = self.exec_stack.get_stack()[prev_step_idx]
                if isinstance(prev_step, Task) and len(prev_step.steps) == 0:
                    assert prev_step.context is not None, 'Trying to scroll to top. Error when updating context.'
                    prev_step.context.start_observation = self.last_observation
                else:
                    break

    def _add_scroll_when_recording(self, step: PageAction) -> PageAction:
        """
        This method adds a scroll to the step if the step element is not in the viewport.
        Also updates the new bbox.
        """

        # Ignore scroll
        if 'scroll' in step.name.lower():
            return step
        
        bbox = step.action_args.bbox
        assert bbox, 'Trying to scroll a PageAction. Error retrieving bbox.'
        selector = step.action_args.selector_dom
        assert selector, 'Trying to scroll a PageAction. Error retrieving selector.'

        # Get viewport position and scroll position
        viewport = self._get_viewport()

        scrolled = False
        # Scroll up if the element is above the viewport
        if bbox.y < 0:
            # Go to the top of the page
            self._scroll_to_top()
            self._update_observation_and_set_in_parents()
            bbox, pointer_xy = self._get_bbox_and_pointer(selector)
            scrolled = True

        if bbox:
            if bbox.y + bbox.height > viewport['height']:
                # Record scroll down
                self._run_scroll(selector)
                scrolled = True

        if scrolled:
            # Update step
            bbox, pointer_xy = self._get_bbox_and_pointer(selector)
            if pointer_xy:
                self.last_pointer_xy = pointer_xy
            step.action_args.bbox = bbox
            assert step.context is not None, 'Trying to scroll a PageAction. Error when updating context.'
            step.context.start_observation = self.last_observation

        return step

    def _teardown(self):
        if not os.getenv('DEVELOPMENT_SERVER'):
            # Execute in the environment the pip uninstall command. Don't show output in stdout and stderr
            subprocess.run(f"{sys.executable} -m pip uninstall -y robotframework-butlerhat", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ========================= LISTENER METHODS =========================

    def _start_suite(self, name, attrs):
        """
        This method is called when a suite starts. The things that are done here are:
        - Save dir name with the name of the suite.
        """
        BuiltIn().log(f"Starting suite {name}", console=self.console)

        dir_name = f"{name}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
        self.suite_out_path: str = os.path.join(BuiltIn().get_variable_value("${OUTPUT_DIR}"), 'data') if self.suite_out_path is None else self.suite_out_path
        self.suite_out_path: str = os.path.join(self.suite_out_path, dir_name)

    def _end_suite(self, name, attrs):
        # If is not a development server, uninstall python package
        self._teardown()
        
    def _start_test(self, name, attrs):
        """
        This method is called when a test starts. The things that are done here are:
        - Create the first Task that will be the root of all nested tasks or actions.
        """
        BuiltIn().log(f"Starting test {name}", console=self.console)

        # Create a task with the steps of the test
        context = Context(start_observation=self.last_observation, status='NOT SET')
        test_task = Task(id=self.id_count, name=attrs['originalname'], context=context)
        self.id_count += 1

        # For start task keyword
        last_step = None
        if not self.exec_stack.is_empty():
            last_step = self.exec_stack.pop()

        self.exec_stack: ExecStack = ExecStack()
        self.exec_stack.push(test_task)
        
        # For start task keyword
        if last_step:
            self.exec_stack.push(last_step)

    def _end_test(self, name, attrs):
        """
        This method is called when a test ends. The things that are done here are:
        - Warn test with no steps.
        """
        BuiltIn().log(f"Ending test {name}", console=self.console)

        if not self.record:
            return

        assert not self.exec_stack.is_empty(), "Error ending test. The stack must not be empty"
        test_task = self.exec_stack.pop()
        assert isinstance(test_task, Task), "Error ending test. The last element in the stack must be a Task"

        # Warn test with no steps
        if len(test_task.steps) <= 0:
            BuiltIn().log("Test with no steps", "WARN", console=True)

        # Set end observation
        assert test_task.context is not None, "Error setting end observation to root Task. The context must not be None"
        test_task.context.end_observation = self.last_observation
        # Set status
        test_task.context.status = attrs['status']
        
        # Save test_task to pickle
        if not os.path.exists(self.suite_out_path):
            os.makedirs(self.suite_out_path)
        BuiltIn().log(f"Saving test {test_task.name} to {self.suite_out_path}", console=True, level="DEBUG")
        
        # Save pickle
        with open(os.path.join(self.suite_out_path, f"{name}.pickle"), "wb") as f:
            pickle.dump(test_task, f, pickle.HIGHEST_PROTOCOL)

        # Save test_task to keyword_libraries
        if self.all_json or 'json' in attrs['tags']:
            with open(os.path.join(self.suite_out_path, f"{name}.json"), 'w', encoding='utf-8') as f:
                json.dump(dataclasses.asdict(test_task), f, ensure_ascii=False, indent=4)

    def _start_keyword(self, name, attrs) -> Optional[Step]:
        """
        This method is called when a keyword starts. The things that are done here are:
        - Set policy if is a keyword that have to be stored. 
            For now: Test Keyword, Browser(only actions if only_actions=True)
        - Create a step. Set start observation with existing last observation.
        - Stack step in steps list.
        """
        def is_exclude_type(type_name):
            return any([exclude_type == type_name for exclude_type in self.exclude_types])
        
        def has_bad_tags(tags):
            return ('task' in tags and 'action' in tags)
        
        def is_task(tags, libname):
            """
            Task: if doesn't have a libname or
            has a libname but is included in the list of keyword_libraries or
            has a tag 'task' and not 'action'

            If true is a task, else is an action

            Action: if has a libname and 
            is not included in the list of keyword_libraries and
            has a tag 'action' and not 'task'
            """
            return not 'action' in tags and \
                (not libname \
                or libname and libname in self.keyword_libraries \
                or 'task' in tags)
        
        def is_action_from_other_lib(step: Step, libname: str):
            """
            Ingore PageActions from other libraries that isn't the wrapper library
            """
            return isinstance(step, PageAction) and \
                libname != self._library.__class__.__name__

        def has_exclude_tags(tags):
            return any([tag in self._get_exclude_tags() for tag in tags])
        
        def has_only_substeps_tags(tags: list[str]):
            return any([tag.lower() in ['only_substeps'] for tag in tags])
        
        def is_keyword_register_in_lib_as_action(step, tags):
            """	
            Ignore if keyword has a tag in the list of excluded tags or ignore if keyword has no tag in the list of action tags
            """
            return isinstance(step, Task) or \
                (isinstance(step, PageAction) and self.only_actions and \
                 any([tag in self._get_action_tags() for tag in tags]))
            
        
        # ============ STEP CREATION ============
        BuiltIn().log(f"Starting keyword {attrs['kwname']}", console=self.console)
        context = Context(start_observation=self.last_observation, status=attrs['status'])
        step: Step = Step(
            id=self.id_count, 
            name=attrs['kwname'], 
            context=context,
            status=SaveStatus.to_record,
            tags=attrs['tags']
        )
        self.id_count += 1


        # ============ STEP FILTERING ============
        # Try and excepts and other
        if not name:
            step.status = SaveStatus.only_substeps

        # Exclude by type
        if is_exclude_type(attrs['type']):
            BuiltIn().log(f"Keyword {name} is of type {attrs['type']}. Excluding", console=False, level="INFO")
            step.status = SaveStatus.only_substeps

        # Classify keyword as task or action
        if has_bad_tags(attrs['tags']):
            raise ValueError(f"Keyword {name} can't be a task and an action at the same time")
        
        # Task
        elif is_task(attrs['tags'], attrs['libname']):
            step = Task(
                id=step.id, 
                name=step.name, 
                status=step.status, 
                context=step.context,
                tags=step.tags,
                steps=[])

        # Action
        else:
            step = PageAction(id=step.id, name=step.name, status=step.status, context=step.context, tags=step.tags)

        # Filter keywords from other libraries that aren't the wrapper library
        if is_action_from_other_lib(step, attrs['libname']):
            BuiltIn().log(f"Ignoring kw {name}. Page action not from {self._library.__class__.__name__}", level="INFO", console=self.console)
            step.status = SaveStatus.no_record

        # Filter keywords with exclude tags
        if has_exclude_tags(attrs['tags']):
            BuiltIn().log(f"Ignoring kw {name}. Has exclude tags", level="INFO", console=self.console)
            step.status = SaveStatus.no_record

        # Filter keywords with only_substeps tags
        if has_only_substeps_tags(attrs['tags']):
            BuiltIn().log(f"Keyword {name} has only_substeps tag. Only substeps will be recorded", level="INFO", console=self.console)
            step.status = SaveStatus.only_substeps

        # If only_actions: ignore PageAction keywords that are not actions by tag
        if not is_keyword_register_in_lib_as_action(step, attrs['tags']):
            BuiltIn().log(f"Ignoring kw {name}. No registered as action", level="INFO", console=self.console)
            step.status = SaveStatus.no_record

        if step.status == SaveStatus.no_record:
            self.exec_stack.push(step)
            return

        # ============ COMPLETE STEP CONTEXT ============

    	# Capture observation if browser is open and no observation was captured. This means is the first keyword after the open browser.
        if self._is_browser_open():  # and self.last_observation == Observation(datetime.now(), "", "", (0, 0)):
            observation = self._get_observation()
            # Update start observation of the rest of the step stack
            if self.last_observation == Observation(datetime.now(), "", "", (0, 0)):
                for prev_step in self.exec_stack.get_stack():
                    if prev_step.context:
                        prev_step.context.start_observation = observation
                    else:
                        BuiltIn().log(f"Step {prev_step.name} has no context. No setting it", level="WARN", console=self.console)
            self.last_observation = observation
        
        assert step.context, f"Step {step.name} has no context. Cannot set start_observation"
        step.context.start_observation = self.last_observation

        # Change name with resolved variables
        name = attrs['kwname']
        embedded = EmbeddedArguments.from_name(name)
        for arg in embedded.args:
            value = BuiltIn().get_variable_value('${' + arg + '}')
            name = name.replace('${' + arg + '}', str(value))
        step.name = name

        # ============ STEP STACKING ============
        # Last step must be a Task. If is a PageAction it means that it invokes another PageAction. Not expected, fails.
        if self.exec_stack.is_empty():
            BuiltIn().log("Executing keyword without Test (interpreter only). To start recording use 'Start Task  ${task_name}'. This keyword won't be recorded.", 
                console=self.console, level="INFO")
        # Stack step
        self.exec_stack.push(step)

    def _end_keyword(self, name, attrs):
        """
        This method is called when a keyword ends. The things that are done here are:
        - Check if keyword is the last step of the stack. Do nothing if not.
        - Unstack step from steps list.
        - Update last observation.
        - Set step properties: end_observation, status.
        """
        def is_exclude_task(step: Step, tags: list[str]):
            """
            Exclude task by tag like no_record.
            """
            return isinstance(step, Task) and any([tag in self._get_exclude_tasks() for tag in tags])

        BuiltIn().log(f"Ending keyword {attrs['kwname']}", console=self.console)

        if self.exec_stack.is_empty():
            BuiltIn().log(f"Steps stack is empty. Skipping keywrod!", console=self.console, level="WARN")
            return
        
        # If is try/except calls more times end_keyword than start_keyword
        if not name:
            # Check if the last step is type try/except. If not, ignore
            if not self.exec_stack.get_last_step() != name:
                BuiltIn().log('Ignoring step with no name. end_keyword called more times than start_keyword', console=self.console, level="DEBUG")

        step: Step = self.exec_stack.pop()
        
        if step.status == SaveStatus.no_record:
            # If is an sleep refresh observation
            if step.name.lower() == 'sleep':
                if self._is_browser_open():
                    self.last_observation = self._get_observation()
            BuiltIn().log(f"Not recording {step.name}. Not valid. Skipping", console=self.console, level="DEBUG")
            return
        
        if isinstance(step, PageAction) and attrs["status"] in ["FAIL", "NOT SET", "NOT RUN"]:
            BuiltIn().log(f"Not recording {step.name}. Keyword with status'{attrs['status']}'. Skipping", console=self.console, level="DEBUG")
            return
        
        if is_exclude_task(step, attrs['tags']):
            BuiltIn().log(f"Not recording {step.name}. Task with exclude tags. Skipping", console=self.console, level="DEBUG")
            return

        # Shoud be a task in the stack
        if self.exec_stack.is_empty():
            BuiltIn().log(f"Not recording {step.name}. Steps stack is empty. Interpreter case only.", console=self.console, level="WARN")
            return

        # Remove task if is a Task and not have steps
        if isinstance(step, Task) and len(step.steps) == 0:
            BuiltIn().log(
                f"Not recording {step.name}. Is a Task and not have steps", "WARN", console=self.console)
            return

        # Update if browser is not open
        if self._is_browser_open():
            self.last_observation = self._get_observation()
            assert step.context, f"Step {step.name} has no context. Cannot set end_observation"
            step.context.end_observation = self.last_observation
            step.context.status = attrs['status']
            
        
        # Storing step
        try:
            self.exec_stack.add_to_parent(step)
            BuiltIn().log(f"Step {step.name} stored", console=self.console, level="INFO")
        except Exception as e:
            BuiltIn().log(f"Not recording {step.name}.Error adding to parent: {e}", console=self.console, level="WARN")
        return
            

    # ========================= PROXY LIBRARY =========================

    def __init__(self, library, console=True, record=True, output_path=None, all_json=False, only_actions=True):
        
        self._library = library
        self.keyword_libraries = []
        self.only_actions = only_actions
        self.ROBOT_LIBRARY_LISTENER = self
        self.record = record
        
        # Check if wait time is set
        if not hasattr(self, 'wait_time'):
            self.wait_time = 0
        
        # For identifying every step
        self.id_count = 0

        # Add keywords with @keyword decorator, remove @property and @classmethod to don't evaluate
        attributes = []
        for name in dir(self):
            # Check if is a property or classmethod
            if hasattr(self.__class__, name):
                if isinstance(getattr(self.__class__, name), property):
                    continue
                if isinstance(getattr(self.__class__, name), classmethod):
                    continue
            attributes.append((name, getattr(self, name)))
        self.keywords_decorator = [(name, value) for name, value in attributes
                    if not isinstance(value, self.__class__) and hasattr(value, 'robot_name')]
        
        # Keyboard keywords and string argument position
        self.typing_kw_stringpos = {'observation': 0}

        # Exclude tasks
        self.exclude_tasks = ['no_record']

        # Exclude types
        self.exclude_types = ['FOR', 'ITERATION', 'IF', 'ELSE IF', 'ELSE', 'END', 'WHILE', 'TRY', 'EXCEPT', 'FINALLY']

        # Added keywords spec
        self.added_keywords = []

        # Create output path
        self.suite_out_path = output_path or os.path.join(os.getcwd(), "data")
        self.all_json = all_json
        self.console = console

        # This observation will be modified when browser opens
        self.last_observation = Observation(datetime.now(), "", "", (0, 0))
        # Create task's steps list and stack for embedded tasks
        self.exec_stack: ExecStack = ExecStack()
        # Create a set of dom to save space disk
        self.dom_set: DomSet = DomSet()
        # Save last pointer x y
        self.last_pointer_xy = (0, 0)
    
    def __getattr__(self, name):
        """
        Proxy every method call to Robot Framework.

        Explanation: getattr for methods and not variables
        """
        # Keyword names may not be initialized yet
        try:
            keyword_keys = [self._get_key_from_keyword(k) for k in self.get_keyword_names()]
        except:
            keyword_keys = []
        # To make method behave like a keyword
        if self._get_key_from_keyword(name) in keyword_keys:
            def method_as_keyword(*args, **kwargs):
                return BuiltIn().run_keyword(name, *args, **kwargs)
            return method_as_keyword
        else:
            return super().__getattribute__(name)

    def run_keyword(self, name, args, kwargs=None):
        def complete_page_action(action: PageAction) -> PageAction:
            kw = name.lower().replace(' ', '').replace('_', '')
            string_kw = [k for k in self.typing_kw_stringpos.keys() if k in kw]
            
            # First arg: BBox, if not string kw
            if 'bbox' in name.lower() or 'scroll' not in name.lower() and len(args) > 0 \
                and not(len(string_kw) > 0 and self.typing_kw_stringpos[string_kw[0]] == 0):

                # Best effort to get the bbox and pointer. Could be a BBox or a selector
                bbox, pointer_xy = self._get_bbox_and_pointer(args[0])
                
                if pointer_xy:
                    self.last_pointer_xy = pointer_xy
                if bbox:
                    action.action_args.bbox = bbox
                    action.action_args.selector_dom = str(args[0])
            
            # String
            if len(args) > 0 and len(string_kw) > 0:
                    # Lets assume that the second argument is the string (Input text)
                    action.action_args.string = args[self.typing_kw_stringpos[string_kw[0]]]

            return action

        # ============ COMPLETE STEP ARGUMENTS ============
        # Complete step here since the variables only are resolved here
        if not self.exec_stack.is_empty():
            step = self.exec_stack.pop()
            if isinstance(step, PageAction) and step.status != SaveStatus.no_record:
                # Update pointer before action. This is due to the fact that the selector corresponds to start dom.
                # Check if first argument keyword is a selector. Ignore if is a scroll to element
                step = complete_page_action(step)

                try:
                    step = self._add_scroll_when_recording(step)
                except Exception as e:
                    BuiltIn().log(f'Error trying to scroll: {e}', 'DEBUG')

            # Updated and scrolled step
            self.exec_stack.push(step)
        
        # ============ RUN KEYWORD ============
        # Keywords with @keyword decorator
        for n, value in self.keywords_decorator:
                if name == value.robot_name.replace(' ', '_').lower() or name == n:
                    return_value = getattr(self, n)(*args, **kwargs)
                    break
        else:
            # Keywords added manually
            if name in self.added_keywords:
                return_value = getattr(self, name)(*args, **kwargs)
            # Keywords from library
            else:
                return_value = self._library.run_keyword(name, args, kwargs)
        
        # ============ WAIT ACTION ============
        if self._is_browser_open():
            if not self.exec_stack.is_empty():
                step = self.exec_stack.get_last_step()
                if isinstance(step, PageAction) and step.status != SaveStatus.no_record:
                    self._wait_for_browser()
        
        return return_value
    
    def get_keyword_names(self):
        keyword_decorator = [value.robot_name.replace(' ', '_').lower() or name 
                             for name, value in self.keywords_decorator]
        keyword_names = self.added_keywords + self._library.get_keyword_names() + keyword_decorator
        # Remove duplicates (overwritten keywords)
        return list(dict.fromkeys(keyword_names))

    def get_keyword_arguments(self, name):
        # Hand made keywords
        if name in self.added_keywords:
            return getattr(self, f"_{name}_rf")['args']
        # Keywords with @keyword decorator
        for func_name, value in self.keywords_decorator:
            if name == (value.robot_name.replace(' ', '_').lower() or func_name):
                arguments = []
                for param in inspect.signature(getattr(self, func_name)).parameters.values():
                    if param.name != 'self':
                        if param.kind == inspect.Parameter.VAR_POSITIONAL:
                            arguments.append(f'*{param.name}')
                        elif param.kind == inspect.Parameter.VAR_KEYWORD:
                            arguments.append(f'**{param.name}')
                        elif param.default == inspect.Parameter.empty:
                            arguments.append(param.name)
                        else:
                            arguments.append((param.name, param.default))
                return arguments
        return self._library.get_keyword_arguments(name)

    def get_keyword_documentation(self, name):
        if name in self.added_keywords:
            return getattr(self, f"_{name}_rf")['doc']
        for func_name, value in self.keywords_decorator:
            if name == (value.robot_name.replace(' ', '_').lower() or func_name):
                return getattr(self, func_name).__doc__.strip() if getattr(self, func_name).__doc__ else ""
        return self._library.get_keyword_documentation(name)

    def get_keyword_tags(self, name):
        if name in self.added_keywords:
            return getattr(self, f"_{name}_rf")['tags']
        for func_name, value in self.keywords_decorator:
            if name == (value.robot_name.replace(' ', '_').lower() or func_name):
                return value.robot_tags
        return self._library.get_keyword_tags(name)

    def get_keyword_types(self, name):
        if name in self.added_keywords:
            return getattr(self, f"_{name}_rf")['types']
        for func_name, value in self.keywords_decorator:
            if name == (value.robot_name.replace(' ', '_').lower() or func_name):
                return getattr(self, func_name).__annotations__
        return self._library.get_keyword_types(name)

    def get_keyword_source(self, name):
        if name in self.added_keywords:
            return getattr(self, f"_{name}_rf")['source']
        for func_name, value in self.keywords_decorator:
            if name == (value.robot_name.replace(' ', '_').lower() or func_name):
                return f'{value.__code__.co_filename}:{value.__code__.co_firstlineno}'
        return self._library.get_keyword_source(name)


    # ========================= KEYWORDS =========================
    @keyword(name='Set Browser Wait Time', tags=['action', 'no_record'])
    def set_browser_wait_time(self, time):
        """
        Set browser wait time.
        """
        self.wait_time = time

    @keyword(name='Add Task Library', tags=['task', 'StaticWrapper'])
    def add_task_library(self, *lib_names):
        """
        Library added as Task library make that all keywords 
        called from this library are considered Task.
        """
        for lib in lib_names:
            self.keyword_libraries.append(lib)

    @keyword(name='Record Test', tags=['task', 'StaticWrapper'])
    def start_test_kw(self, task_name):
        """
        Start a task. Record when using RobotFramework in interpreter.
        """
        BuiltIn().log(f"Starting task {task_name}", console=self.console)

        # Configure output path
        if self.suite_out_path is None:
            self.suite_out_path =  os.path.join(BuiltIn().get_variable_value("${OUTPUT_DIR}"), 'data')
        else:
            self.suite_out_path = self.suite_out_path

        # Create task
        self._start_test(task_name, {'originalname': task_name})

    @keyword(name='Save Test', tags=['task', 'StaticWrapper'])
    def end_test_kw(self, to_json=False):
        """
        End a task. Record when using RobotFramework in interpreter.
        """
        BuiltIn().log(f"Ending task", console=self.console)

        assert not self.exec_stack.is_empty(), "Error ending task, stack is empty and should be 'End Task' step at least."
        self.exec_stack.pop()  # Ignore 'End Task' step

        # Check if steps_stack is empty
        if self.exec_stack.is_empty():
            BuiltIn().log(f"Keyword 'Start Task' must be called before 'End Task. Doing nothing.", console=self.console, level="WARN")
            return
        
        task = self.exec_stack.get_last_step()
        attrs = {
            'status': 'PASS',
            'tags': ['json'] if to_json else [],
        }
        # Log name if the task
        BuiltIn().log(f"Task name: {task.name}", console=self.console)

        self._end_test(task.name, attrs)

    @keyword(name='Start Task', tags=['task', 'no_record'])
    def start_task_kw(self, task_name):
        """
        Start a task. Record when using RobotFramework in interpreter.
        """
        BuiltIn().log(f"Starting task {task_name}", console=self.console)

        # Configure output path
        if self.suite_out_path is None:
            self.suite_out_path =  os.path.join(BuiltIn().get_variable_value("${OUTPUT_DIR}"), 'data')
        else:
            self.suite_out_path = self.suite_out_path

        # Create task
        self._start_keyword(task_name, {
            'doc': 'Task created manually',
            'assign': [],
            'tags': ['task', 'manual_task'], 
            'lineno': 0,
            'source': f'{__file__}',
            'type': 'KEYWORD',
            'status': 'NOT SET',
            'starttime': datetime.now().strftime("%Y%m%d %H:%M:%S.%f"),
            'kwname': task_name,
            'libname': 'DataWrapperLibrary',
            'args': []
            }
        )

    @keyword(name='End Task', tags=['task', 'no_record'])
    def end_task_kw(self):
        """
        End a task. Record when using RobotFramework in interpreter.
        """
        assert not self.exec_stack.is_empty(), "Error ending task, stack is empty and should be 'End Task' step at least."
        self.exec_stack.pop()  # Ignore 'End Task' step, use end task
        assert 'manual_task' not in self.exec_stack.get_last_step().tags, "Error ending task, before calling 'End Task' a 'Start Task' must be called." + \
            "Last stack step: " + str(self.exec_stack.get_last_step().name)
        BuiltIn().log(f"Ending task {self.exec_stack.get_last_step().name}", console=self.console)
        # end_task will be called after this keyword. Hopefully, the last task in the stack is the one we want to end ('manual_task in tags). 

    @keyword(name='Remove Last Task', tags=['task', 'StaticWrapper'])
    def remove_last_task(self):
        """
        Remove last task from the stack.
        """
        is_removed, msg = self.exec_stack.remove_last_step_from_last_task()
        level = 'WARN' if not is_removed else 'INFO'
        BuiltIn().log(msg, console=self.console, level=level)

    @keyword(name='Observation', tags=['action', 'AI'])
    def observation_kw(self, observation: str):
        """
        Add an observation to help the model with the prediction.
        """
        BuiltIn().log(f"Adding observation {observation}", console=self.console)

if __name__ == '__main__':
    from robot.run import run
    run('./ButlerRobot/TestDataWrapper.robot', outputdir='results')
