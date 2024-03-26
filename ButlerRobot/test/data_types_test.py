import unittest
import tempfile
import os
import json
from ButlerRobot.src.data_types import ActionArgs, Context, Observation, PageAction, Task, BBox

class TestStepSaveMethod(unittest.TestCase):

    def test_save_page_action(self):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set up a PageAction instance
            action_args = ActionArgs(selector_dom='div.test', string='Test String', bbox=None)
            context = Context(start_observation=Observation(time='2023-01-01T12:00:00', screenshot='', dom='', pointer_xy=(0, 0)), 
                              status='NOT_SET', 
                              end_observation=Observation(time='2023-01-01T12:01:00', screenshot='', dom='', pointer_xy=(0, 0)))
            page_action = PageAction(id=1, name='Test Page Action', context=context, action_args=action_args)

            # Call save method
            file_path = os.path.join(tmpdirname, 'page_action.json')
            page_action.save(file_path)

            # Verify the file was created
            self.assertTrue(os.path.exists(file_path))

            # Verify the content of the file
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.assertEqual(data['id'], page_action.id)
                self.assertEqual(data['name'], page_action.name)
                self.assertEqual(data['context']['status'], 'NOT_SET')
                self.assertEqual(data['action_args']['selector_dom'], 'div.test')
                self.assertEqual(data['action_args']['string'], 'Test String')

    def test_save_task_with_substeps(self):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set up a Task instance with recursive substeps
            task = Task(id=1, name='Test Task', context=None)
            sub_task = Task(id=2, name='Sub Task', context=None)
            action_args = ActionArgs(selector_dom='input.name', string='John Doe', bbox=None)
            page_action = PageAction(id=3, name='Fill Name', action_args=action_args)
            sub_task.add_step(page_action)
            task.add_step(sub_task)

            # Call save method
            file_path = os.path.join(tmpdirname, 'task.json')
            task.save(file_path)

            # Verify the file was created
            self.assertTrue(os.path.exists(file_path))

            # Verify the content of the file
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.assertEqual(data['id'], task.id)
                self.assertEqual(data['name'], task.name)
                self.assertEqual(len(data['steps']), 1)
                self.assertEqual(data['steps'][0]['id'], sub_task.id)
                self.assertEqual(data['steps'][0]['name'], sub_task.name)
                self.assertEqual(len(data['steps'][0]['steps']), 1)
                self.assertEqual(data['steps'][0]['steps'][0]['id'], page_action.id)
                self.assertEqual(data['steps'][0]['steps'][0]['name'], page_action.name)

    def test_context_bbox_actionargs_serialization(self):
        # Create instances of Context, BBox, and ActionArgs
        bbox = BBox(x=10, y=20, width=100, height=200)
        action_args = ActionArgs(selector_dom='input.test', string='Sample input', bbox=bbox)
        start_observation = Observation(time='2023-02-02T14:00:00', screenshot='screenshot_base64', dom='<html></html>', pointer_xy=(10, 20))
        end_observation = Observation(time='2023-02-02T14:05:00', screenshot='screenshot_base64_end', dom='<html></html>', pointer_xy=(30, 40))
        context = Context(start_observation=start_observation, status='PASSED', end_observation=end_observation)

        # Create a Task with these instances
        page_action = PageAction(id=1, name='Input Test', context=context, action_args=action_args)
        task = Task(id=2, name='Test Task', steps=[page_action])

        # Serialize the Task to JSON
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, 'task.json')
            task.save(file_path)

            # Verify the file was created
            self.assertTrue(os.path.exists(file_path))

            # Deserialize the Task from JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
                restored_task = Task.from_dict(data)

            # Verify the restored objects
            restored_page_action = restored_task.steps[0]
            assert isinstance(restored_page_action, PageAction)
            restored_action_args = restored_page_action.action_args
            restored_context = restored_page_action.context

            self.assertEqual(restored_action_args.selector_dom, action_args.selector_dom)
            self.assertEqual(restored_action_args.string, action_args.string)
            
            assert isinstance(restored_action_args.bbox, BBox)
            self.assertEqual(restored_action_args.bbox.x, bbox.x)
            self.assertEqual(restored_action_args.bbox.y, bbox.y)
            self.assertEqual(restored_action_args.bbox.width, bbox.width)
            self.assertEqual(restored_action_args.bbox.height, bbox.height)

            assert isinstance(restored_context, Context)
            self.assertEqual(restored_context.start_observation.time, context.start_observation.time)
            self.assertEqual(restored_context.status, context.status)
            self.assertEqual(restored_context.end_observation.time, context.end_observation.time)


if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStepSaveMethod)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
