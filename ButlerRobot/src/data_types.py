from __future__ import annotations
from enum import Enum, auto

import math
import base64
import json
import re
import imagehash
from io import BytesIO
from PIL import Image
from dataclasses import dataclass, field, asdict
from typing import Iterable, Optional

"""
Data structure for the ButlerRobot.

= Step: A step could be an action or a task.
    - Context: The context of the step.
        * start_observation: Observation. The observation at the start of the step.
            - screenshot: str. The screenshot at the start of the step.
            - dom: str. The dom at the start of the step.
            - pointer_xy: (int, int). The pointer position at the start of the step.
        * status: str. The status of the step. (NOT SET, PASSED, FAILED, SKIPPED)
        * end_observation: Observation. The observation at the end.

== PageAction(Step): An action is a single step that is executed in the browser.
    - ActionArgs: The arguments of the action.
        * selector: str. The selector of the action.
        * string: str. The input string of the action (Ex: Input Text).
        * bbox: BBox. The bounding box of the element of the selector.
            - x: int. The x coordinate of the bounding box.
            - y: int. The y coordinate of the bounding box.
            - width: int. The width of the bounding box.
            - height: int. The height of the bounding box.

== Task(Step): A task is a group of steps.
    - steps: List[Step]. The steps of the task.
"""

class SaveStatus(Enum):
    """Enum that defines if step must be saved."""

    to_record = auto()
    confirm_record = auto()
    only_substeps = auto()
    no_record = auto()

@dataclass
class Step:
    id: int
    name: str
    status: SaveStatus = field(default=SaveStatus.to_record)  # If the step should be recorded
    context: Optional[Context] = None
    tags: list[str] = field(default_factory=list)

    # to string
    def __str__(self):
        start_time = self.context.start_observation.time if self.context is not None else "Not set"
        end_time = self.context.end_observation.time if self.context is not None else "Not set"
        return f"{self.name} ({self.id}): {start_time} - {end_time}"

    def __repr__(self):
        return self.__str__()

    def is_complete(self) -> bool:
        # Check if all the attributes are set and not None
        context_complete = self.context is not None and self.context.is_complete()
        return all([hasattr(self, attr) and getattr(self, attr) is not None for attr in self.__dataclass_fields__]) and context_complete

@dataclass(init=False)
class PageAction(Step):
    action_args: ActionArgs

    def __init__(self, 
                 id: int, 
                 name: str, 
                 status: SaveStatus = SaveStatus.to_record,
                 context: Optional[Context] = None,
                 tags: list[str] = [],
                 action_args: Optional[ActionArgs] = None):
        # To set default value to kwname and not in ActionArgs
        self.id = id
        self.name = name
        self.context = context
        self.tags = tags
        self.action_args = action_args if action_args else ActionArgs('', '', None)
        self.status = status


@dataclass
class Task(Step):
    steps: list[Step] = field(default_factory=list)

    def _get_parents_ids(self, step_id: int) -> list[int]:
        """
        Returns the ids of the parents of the step but not the step itself. 
        The first is the root and the last is the parent of the step.
        """
        def search_parent_step_rec(ids_: list, step: Task) -> tuple[bool, list]:
            if step_id in [sub_step.id for sub_step in step.steps]:
                return True, ids_
            else:
                for sub_step in step.steps:
                    if isinstance(sub_step, Task):
                        ids_.append(sub_step.id)
                        is_step, ids_ = search_parent_step_rec(ids_, sub_step)
                        if is_step:
                            return True, ids_
                        else:
                            ids_.pop()
                else:
                    return False, ids_
        
        # If the step is the root
        if step_id == self.id:
            return []

        ids = [self.id]  # Add root
        is_step, ids = search_parent_step_rec(ids, self)
        if not is_step:
            raise ValueError(f"Step with id {step_id} not found")
        return ids
    
    def get_all_steps(self) -> Iterable[Step]:
        def recursive_get_steps(steps):
            for step in steps:
                yield step
                if isinstance(step, Task):
                    yield from recursive_get_steps(step.steps)
        yield from recursive_get_steps([self])

    def get_all_tasks(self) -> Iterable[Task]:
        for step in self.get_all_steps():
            if isinstance(step, Task):
                yield step

    def get_child(self, id: int) -> Step:
        for step in self.steps:
            if step.id == id:
                return step
        return None  # type: ignore
    
    def find_step(self, step_id: int) -> Optional[Step]:
        def search_step_rec(step: Step) -> Optional[Step]:
            if step_id == step.id:
                return step
            else:
                if isinstance(step, Task):
                    for sub_step in step.steps:
                        found_step = search_step_rec(sub_step)
                        if found_step is not None:
                            return found_step
            return None
        
        step = search_step_rec(self)
        if step is None:
            raise ValueError(f"Step with id {step_id} not found")
        return step

    def get_parent(self, step_id: int) -> Task:
        ids = self._get_parents_ids(step_id)
        task = self.find_step(ids[-1])
        if not isinstance(task, Task):
            raise ValueError(f"Found step with id {ids[-1]} is not a Task")
        return task

    def add_step(self, step: Step):
        self.steps.append(step)

    def remove_step(self, step: Step):
        self.steps.remove(step)
    
    def remove_step_by_id(self, step_id: int):
        step = self.get_child(step_id)
        if step is None:
            raise ValueError(f"Step with id {step_id} not found")
        self.steps.remove(step)

    def replace_step_by_id(self, step_id: int, new_step: Step):
        parent = self.get_parent(step_id)
        # Replace the step in same position of the parent parent.steps
        for i, step in enumerate(parent.steps):
            if step.id == step_id:
                parent.steps[i] = new_step
                return True
        return False

    def get_history_instructions(self, step_id: int, with_tasks: bool=False) -> dict:
        """
        Get previous steps names in nested list. The first element is always a Task.
        The last element (max depth, last of 'steps' list) is the step with the given id.
        Example:
        {
            "id": 1,
            "name": "Task 1",
            "type": "task",
            "args": {},
            "steps": [
                {
                    "id": 1.1,
                    "name": "Task 1.1",
                    "type": "task",
                    "args": {},
                    "steps": []
                },
                {
                    "id": 1.1,
                    "name": "Page Action 1.1",
                    "steps": [
                        {
                            "id": 1.2.1,
                            "name": "Task 1.1.1",
                            "type": "task",
                            "args": ActionArgs.to_dict(),
                            "steps": []
                        }
                    ]
                }
            ]                
        }
        """
        def recursive_get_history(parents: list) -> dict:
            """
            First element of parents is the current step.
            """
            step_id = parents.pop()
            step = self.find_step(step_id)
            assert step is not None, f"Error getting step from parents. Step id {step_id}"
            if len(parents) == 0:
                # Should be a Task (root). In this dictionary we will add all the steps
                assert isinstance(step, Task), "Root element must be a Task"
                return {
                    "id": step.id,
                    "name": step.name,
                    "type": "task",
                    "args": {},
                    "steps": []
                }
            else:
                all_history = recursive_get_history(parents[:])
                assert isinstance(all_history, dict), "Recursive function fail, root element must be a dict"
                # Get parent dictionary
                parent_history = all_history
                for parent_id in parents:
                    for parent_step in parent_history["steps"]:
                        if parent_step["id"] == parent_id:
                            parent_history = parent_step
                            break

                # Add siblings to parent_history
                parent = self.find_step(parents[-1])
                assert isinstance(parent, Task), "Parent must be a Task"
                for sibling in parent.steps:
                    parent_history["steps"].append({
                        "id": sibling.id,
                        "name": sibling.name,
                        "type": "task" if isinstance(sibling, Task) else "action",
                        "args": sibling.action_args.to_dict() if isinstance(sibling, PageAction) else {},
                        "steps": []
                    })
                    if sibling.id == step.id:
                        break
                return all_history
            
        ids = self._get_parents_ids(step_id) + [step_id]
        # Only return siblings
        if not with_tasks:
            step = self.find_step(step_id)
            if isinstance(step, Task):
                # Return only itself (formated in a dict)
                return recursive_get_history([step_id])
            else:
                # Return task parent, siblings and itself.
                return recursive_get_history(ids[-2:])
        else:
            return recursive_get_history(ids)

    def set_status_to_all_children(self, status: SaveStatus):
        for step in self.steps:
            step.status = status
            if isinstance(step, Task):
                step.set_status_to_all_children(status)

    def to_dict(self):
        asdict(self)

    def to_json(self):
        return json.dumps(asdict(self))

    def has_confirmed_tasks_inside(self) -> bool:
        for step in self.get_all_tasks():
            if step.status == SaveStatus.confirm_record:
                return True
        return False
    
    def has_confirmed_tasks_inside_legacy(self) -> bool:
        for step in self.get_all_tasks():
            if step.id >= 1000:
                return True
        return False

@dataclass
class Context:
    start_observation: Observation
    status: str
    end_observation: Observation = field(default=None)  # type: ignore

    def is_complete(self) -> bool:
        # Check if all the attributes are set and not None
        start_complete = self.end_observation is not None and self.start_observation.is_complete()
        end_complete = self.end_observation is not None and self.end_observation.is_complete()
        return all([hasattr(self, attr) and getattr(self, attr) is not None for attr in self.__dataclass_fields__]) and start_complete and end_complete

@dataclass
class ActionArgs:
    selector_dom: str  # Where the action was performed
    string: str  # The string that was used in the action. Ex: "Type text" -> "Hello World"
    bbox: Optional[BBox] = field(default=None)  # Bounding box of the element

    def to_dict(self):
        return asdict(self)

@dataclass
class Observation:
    time: str
    screenshot: str
    dom: str
    pointer_xy: tuple[int, int] = field(default=(0, 0))

    def __init__(self, time, screenshot, dom, pointer_xy=(0, 0)):
        if not isinstance(time, str):
            self.time: str = time.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            self.time: str = time
        self.screenshot: str = screenshot
        self.dom: str = dom
        self.pointer_xy: tuple[int, int] = pointer_xy

    def measure_similarity(self, other: Observation) -> int:
        """
        Measure the similarity between two observations.
        """
        image_hash = imagehash.average_hash(Image.open(BytesIO(base64.b64decode(self.screenshot))))
        other_image_hash = imagehash.average_hash(Image.open(BytesIO(base64.b64decode(other.screenshot))))
        return image_hash - other_image_hash

    def is_complete(self) -> bool:
        # Check if all the attributes are set and not empty
        # Ignore dom
        dom = self.dom
        self.dom = 'True'
        complete = all([hasattr(self, attr) and getattr(self, attr) for attr in self.__dataclass_fields__])
        self.dom = dom
        return complete

    def __hash__(self):
        """
        Only hash the image with imagehasg.
        """
        if not self.screenshot:
            return ''
        return str(imagehash.average_hash(Image.open(BytesIO(base64.b64decode(self.screenshot)))))


    def __eq__(self, other):
        """
        Only compare the image.
        """
        return self.__hash__() == other.__hash__()

@dataclass
class DomSet:
    dom_set: set[str] = field(default_factory=set)

    def add_dom(self, dom: str):
        if dom not in self.dom_set:
            self.dom_set.add(dom)
        else:
            dom = next((d for d in self.dom_set if d == dom), None)  # type: ignore
        
        return dom


@dataclass
class BBox:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        self.x = int(self.x)
        self.y = int(self.y)
        self.width = int(self.width)
        self.height = int(self.height)

    # To dict
    def to_dict(self):
        return asdict(self)

    def pillow_print(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def distance(self, other: BBox) -> float:
        """
        Calculate the distance between two bounding boxes with the center.
        """
        return math.dist(self.center(), other.center())
    
    def is_above_of(self, other: BBox) -> bool:
        """
        Check if the bounding box is above the other.
        """
        return self.y < other.y + other.height
    
    def is_left_to(self, other: BBox) -> bool:
        """
        Check if the bounding box is left of the other.
        """
        return self.x < other.x + other.width

    @classmethod
    def from_rf_string(cls, string: str):
        """
        Create a BBox from a string like this:
        - BBox(x=0, y=0, width=100, height=100)
        - BBox(x1=0, y1=0, x2=100, y2=100)  In this case x2 is the width and y2 is the height
        - BBox(0, 0, 100, 200)
        """
        # Get arguments from parenteses
        args = string[string.find("(") + 1:string.find(")")]
        # Split arguments
        args = args.split(",")
        # Get the right side of the equal sign
        args = [arg.split("=")[-1] for arg in args]
        # Only get the digits
        args = [int(re.sub(r'\D', '', arg)) for arg in args]
        return cls(*args)
