import logging
from ..data_types import SaveStatus, Task, PageAction, Step
from .data_types import AIExample, PromptStep


class AIExampleBuilder:
    """
    Build all UDOP examples from a task.
    """
    def __init__(self, task: Task, history_with_tasks: bool = False):
        self.task = task
        self.history_with_tasks = history_with_tasks

    def build_history(self, step: Step, ignore_scrolls: bool = True) -> 'list[PromptStep]':
        """
        Build the history of a step for inference.
        """
        history = self.task.get_history_instructions(step_id=step.id, with_tasks=self.history_with_tasks)
        intermediate_tasks = self._get_prompts(history)
        # Get the largest prompt
        length = 0
        task_history = []
        for prompt in intermediate_tasks:
            if len(prompt) > length:
                task_history = prompt
                length = len(prompt)
        if ignore_scrolls:
            history_no_scroll = []
            for step_prompt in task_history:
                if 'scroll' not in step_prompt.name.lower():
                    history_no_scroll.append(step_prompt)
            task_history = history_no_scroll
        
        return task_history

    def build(self, ignore_scrolls: bool = True) -> 'list[AIExample]':
        """
        Build all UDOP examples from a task. For dataset creation.
        """
        examples = []

        for step in self.task.get_all_steps():
            if step.status == SaveStatus.no_record:
                continue
            history = self.task.get_history_instructions(step_id=step.id, with_tasks=self.history_with_tasks)
            intermediate_tasks = self._get_prompts(history)
            start_screen = step.context.start_observation.screenshot if step.context else ''
            end_screen = step.context.end_observation.screenshot if step.context else ''
            if not start_screen or not end_screen:
                logging.warning(f'No screenshot for step {step.id}')
            # Add actions as examples
            if isinstance(step, PageAction):
                for prompt in intermediate_tasks:
                    # Remove scroll actions from history
                    if ignore_scrolls:
                        instruction_history = [s for s in prompt[:-1] if s.type == 'task' or (s.type == 'action' and 'scroll' not in s.name.lower())]
                    else:
                        instruction_history = prompt[:-1]
                    examples.append(AIExample(
                        instruction_history=instruction_history,
                        screenshot=start_screen,
                        action=prompt[-1]
                    ))
                # Add end of task as examples
                is_last_step = self.task.get_parent(step.id).steps[-1].id == step.id
                if is_last_step:
                    examples.append(AIExample(
                        instruction_history=intermediate_tasks[-1],
                        screenshot=end_screen,
                        action=PromptStep(name='end', args={}, type='action')
                        ))

            # TODO: Explore add end to tasks like: 
            #   'Create user' -> 'Login' -> 'Go to users' -> 'Add user' -> 'end'
            elif isinstance(step, Task) and self.history_with_tasks:
                if step.context and step.context.end_observation is None:
                    continue
                for prompt in intermediate_tasks:
                    examples.append(AIExample(
                        instruction_history=prompt,
                        screenshot=end_screen,
                        action=PromptStep(name='end', args={}, type='action')
                    ))
        return examples
    
    @staticmethod
    def _get_prompts(history: dict) -> 'list[list[PromptStep]]':
        """	
        For training.
        Get all possible prompts from a history, intermediate prompts included.
        :param history: The history to get the prompts from.
        :return: A list of prompts.
        """
        def recursive_get_prompts(history: dict, prompts: list=[], save_prompt=True) -> list:
            his_to_save = PromptStep(
                name=history['name'],
                args=history['args'],
                type=history['type']
            )
            if len(history['steps']) == 0:
                if save_prompt and his_to_save.type == 'task':
                    prompts.append([his_to_save])
                return [[his_to_save]]
            else:
                new_prompt = [his_to_save]
                for i, step in enumerate(history['steps']):
                    save_prompt = bool(i == len(history['steps']) - 1)
                    new_prompt += recursive_get_prompts(step, prompts, save_prompt)[-1]
                prompts.append(new_prompt)
                return prompts
        return recursive_get_prompts(history)