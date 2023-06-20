import os
import uuid
import argparse
import base64
import io
import logging
from PIL import Image
from ButlerRobot.src.data_types import ActionArgs, BBox
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from ButlerRobot.src.exec_stack_recorder import ExecStackRecorder
from ButlerRobot.src.robot_actions import RobotActions, ActionParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Argument parsing
current_dir = os.path.dirname(os.path.realpath(__file__))
parser = argparse.ArgumentParser(description='FastAPI server with ExecStackRecorder.')
parser.add_argument('--output_path', type=str, default=f'{current_dir}/data', help='The path to the output directory')
parser.add_argument('--port', type=int, default=8000, help='The port to run the server on')
parser.add_argument('--resize', type=bool, default=True, help='Whether to resize the screenshots')
parser.add_argument('--resize_to', type=tuple, default=(1280, 720), help='The size to resize the screenshots to')
args = parser.parse_args()
port = args.port
config = {
    "output_path": args.output_path
}
resize = args.resize
resize_to = args.resize_to

app = FastAPI()

# Models
def _resize(img: str, bbox: BBox | None = None):
    img_ = Image.open(io.BytesIO(base64.b64decode(img)))
    resized_img = img_.resize(resize_to)
    buffered = io.BytesIO()
    resized_img.save(buffered, format="PNG")
    screenshot = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Resize the bbox
    if bbox:
        bbox_ = BBox(
            x=int(bbox.x * resize_to[0] / img_.width),
            y=int(bbox.y * resize_to[1] / img_.height),
            width=int(bbox.width * resize_to[0] / img_.width),
            height=int(bbox.height * resize_to[1] / img_.height),
        )
    else:
        bbox_ = None

    return screenshot, bbox_


class NewTask(BaseModel):
    task_name: str

class EndTask(BaseModel):
    screenshot: str

    def post_init(self):
        # Plugin sends the screenshot as a base64 string with comma in the beginning
        if self.screenshot:
            self.screenshot = self.screenshot.split(",")[1]
            if resize:
                self.screenshot, _ = _resize(self.screenshot)

class NewTaskAction(BaseModel):
    screenshot: str
    action: str = ""
    task_instruction: str = ""
    selector_dom: str = ""
    bbox: dict | BBox | None = None
    keySequence: str = ""

    def post_init(self):
        if self.bbox is not None and isinstance(self.bbox, dict):
            self.bbox = BBox(x=self.bbox['left'], y=self.bbox['top'], width=self.bbox['width'], height=self.bbox['height'])
            if not self.selector_dom:
                self.selector_dom = str(self.bbox)

        # Plugin sends the screenshot as a base64 string with comma in the beginning
        if self.screenshot:
            self.screenshot = self.screenshot.split(",")[1]

        if resize:
            self.screenshot, self.bbox = _resize(self.screenshot, self.bbox)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# To hold the task data
recorders: Dict[str, ExecStackRecorder] = {}


@app.post("/start_root_task")
async def new_task(new_task: NewTask):
    task_id = str(uuid.uuid4())
    recorders[task_id] = ExecStackRecorder(config)
    recorders[task_id].start_root_task(new_task.task_name)
    return {"task_id": task_id}


@app.post("/add_page_action/{task_id}")
async def add_page_action(task_id: str, page_action: NewTaskAction):
    if task_id not in recorders:
        raise HTTPException(status_code=404, detail="Task not found")

    recorder = recorders[task_id]

    # Parse the action
    try:
        assert page_action.screenshot, "Screenshot is required"
        action: RobotActions = ActionParser.parse_action(page_action.action)
        page_action.post_init()
        assert not isinstance(page_action.bbox, dict), "BBox must be a BBox object"
    except Exception as e:
        HTTPException(status_code=400, detail=e)
        return
    action_args = ActionArgs(
        selector_dom=page_action.selector_dom,
        bbox=page_action.bbox,  # type: ignore
        string=page_action.keySequence,
    )
    screenshot = page_action.screenshot

    # Create the action
    recorder.store_page_action(action, action_args, screenshot)
    return {"message": "Action added successfully"}


@app.post("/add_task/{task_id}")
async def add_task(task_id: str, task: NewTask):
    if task_id not in recorders:
        logging.error(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")

    recorder = recorders[task_id]

    try:
        assert task.task_name, "Task instruction is required"
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)

    recorder.store_task(task.task_name)
    return {"message": "Task added successfully"}


@app.post("/add_task_and_action/{task_id}")
async def add_step(task_id: str, action_task: NewTaskAction):
    if task_id not in recorders:
        logging.error(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")

    recorder = recorders[task_id]

    try:
        assert action_task.screenshot, "Screenshot is required"
        assert action_task.task_instruction, "Task instruction is required"
        action: RobotActions = ActionParser.parse_action(action_task.action)
        action_task.post_init()
        assert not isinstance(action_task.bbox, dict), "BBox must be a BBox object"
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)
    
    action_args = ActionArgs(
        selector_dom=action_task.selector_dom,
        bbox=action_task.bbox,  # type: ignore
        string=action_task.keySequence,
    )

    recorder.store_page_action(action, action_args, action_task.screenshot)
    recorder.store_task(action_task.task_instruction)
    return {"message": "Action and task added successfully"}


@app.post("/save_task/{task_id}")
async def end_task(task_id: str, task: EndTask):
    if task_id not in recorders:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        assert task.screenshot, "Screenshot is required"
        task.post_init()
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)

    recorder = recorders[task_id]
    recorder.save_task(task.screenshot)
    del recorders[task_id]
    return {"message": "Task ended successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
