from enum import Enum


class RobotActions(Enum):
    """
    Actions that will learn the AI
    """
    click_at_bbox = "Click At BBox"
    keyboard_input = "Keyboard Input"
    scroll_down = "Scroll Down"
    scroll_up = "Scroll Up"
    scroll_down_at_bbox = "Scroll Down At BBox"
    scroll_up_at_bbox = "Scroll Up At BBox"

class ActionParser:
    @staticmethod
    def parse_action(action: str) -> RobotActions:
        if action == "click_at_bbox":
            return RobotActions.click_at_bbox
        elif action == "keyboard_input":
            return RobotActions.keyboard_input
        elif action == "scroll_down":
            return RobotActions.scroll_down
        elif action == "scroll_up":
            return RobotActions.scroll_up
        elif action == "scroll_down_at_bbox":
            return RobotActions.scroll_down_at_bbox
        elif action == "scroll_up_at_bbox":
            return RobotActions.scroll_up_at_bbox
        else:
            raise Exception("Action not found")
