import os
import logging
import copy
from datetime import datetime, timedelta
from ButlerRobot.src.robot_actions import RobotActions
from ButlerRobot.src.data_types import Observation, Context, Step, PageAction, Task, ActionArgs

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

    
class ExecStackRecorder:
    def __init__(self, config: dict):
        """
        Initialize the RootTaskRecorder. This does not require an exec stack due to the task creation is after
        the actions and there are not nested tasks.
        :param config: In config, the following keys are required:
            - output_path: The path to the output directory (default: output) 
        """
        self.root_task: Task | None = None
        self.last_actions: list[Step] = []
        self.last_step: Step | None = None  # This is to complete the end observation
        self.out_path: str = config.get("output_path", os.path.join(os.getcwd()))
        self.id_count = 0
        self.start_time = datetime.now()

    def _update_last_task(self, observation: Observation):
        """
        Update the las_step of the last task with the observation. This observations is the start observation of the
        next task.
        """
        # Update end observation to the last step. If is a Task, update to the last step of the task also.
        if self.last_step is not None:
            assert self.last_step.context is not None, "Trying to update last step. No context found"
            if isinstance(self.last_step, Task):
                assert self.last_step.steps, "Trying to update last task. No steps found"
                assert self.last_step.steps[-1].context, "Trying to update last task. No context found in this last step"
                self.last_step.steps[-1].context.end_observation = observation
            self.last_step.context.end_observation = observation


    def start_root_task(self, task_name: str):
        """	
        Start a new root task. Is the same as the 'start test' keyword in Robot Framework.
        :param task_name: The name of the task
        """
        logger.info(f"Starting task {task_name}")

        # Configure the output path
        file_name = f"{task_name}_{datetime.now().strftime('%H-%M_%d-%m-%Y')}.pickle"
        self.out_path = os.path.join(self.out_path, file_name)

        # Create task
        self.root_task = Task(id=self.id_count, name=task_name)
        self.id_count += 1

    def store_page_action(self, action: RobotActions, action_args: ActionArgs, screenshot: str):
        """
        Add a page action without instruction. This will be stored until add_task is called.
        """
        assert self.root_task is not None, "No task started"
        
        # Create page action
        time = self.start_time + timedelta(seconds=self.id_count)
        start_observation = Observation(time=time, screenshot=screenshot, dom="", pointer_xy=(-1, -1))
        context = Context(start_observation=start_observation, status='PASS')
        page_action = PageAction(id=self.id_count, name=action.value, context=context, action_args=action_args)
        
        # Add page action to exec stack
        self.id_count += 1
        self.last_actions.append(page_action)
        logger.info(f"Stored page action {action.value}")

        self._update_last_task(start_observation)
        self.last_step = page_action

    def store_task(self, task_name: str):
        """
        Add a task to the root task.
        :param task_name: The name of the task
        :param screenshot: The screenshot of the page at the end of the task.
        """
        assert self.root_task, "Trying to store a task. No root task found"
        assert self.last_actions, "Trying to store a task without any actions"
        
        # Create task. The end observation is pending to be updated by next page action or save task.
        assert self.last_actions[0].context, "Trying to store a task. No first observation found"
        start_observation = self.last_actions[0].context.start_observation
        context = Context(start_observation=start_observation, status='PASS')

        # Update end observation to the last step
        assert self.last_step, "Trying to update last task. No last step found"
        assert self.last_step.context, "Trying to update last task. No context found in last step"
        self.last_step.context.end_observation = start_observation
        task = Task(id=self.id_count, name=task_name, context=context, steps=self.last_actions)
        
        # Add task to the root task
        self.id_count += 1
        self.root_task.steps.append(task)
        self.last_actions = []
        self.last_step = task
        logger.info(f"Stored task {task_name}")
        
    def save_task(self, screenshot: str):
        """
        Save the task to a pickle file. The screenshot is to update the end observation.
        :param screenshot: The screenshot of the page at the end of the task
        """
        assert self.root_task, "Trying to save task. No root task found"
        assert self.root_task.steps, "Trying to save task. No steps found in root task"
        assert screenshot, "Trying to save task. No screenshot found"
        assert self.last_step, "Trying to save task. No last step found"
        assert self.last_step.context, "Trying to save task. No context found in last step"

        start_context = copy.deepcopy(self.root_task.steps[0].context)
        assert start_context, "Trying to save task. No context found in first step"
        end_time = self.start_time + timedelta(seconds=self.id_count)
        end_observation = Observation(time=end_time, screenshot=screenshot, dom="", pointer_xy=(-1, -1))
        self._update_last_task(end_observation)
        self.root_task.context = start_context
        self.root_task.context.end_observation = end_observation
        
        assert self.root_task, "Trying to save task. No root task found"
        assert self.root_task.steps, "Trying to save task. No steps found in root task"
        
        # Save task
        self.root_task.save(self.out_path)
        logger.info(f"Saved task {self.root_task.name}")
        return self.root_task.name
        
