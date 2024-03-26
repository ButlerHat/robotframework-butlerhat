import os
from openai import OpenAI
import base64
from PIL import Image


prompt_v1 = """
You are a documentation writer for step-by-step computer tasks. Your sole function is to describe the actions being performed on the screen. You will be told what action is being taken and given a screenshot highlighting the element being interacted with, and you must describe that action in a sentence.

Example with click action:

Action: Click
Image: Look at the image, in this example imagine there is a yellow accept button at the bottom right
Documentation writer (you): Click on the yellow accept button located at the bottom right.

Example with typing action:

Action: Type 'David'
Image: Look at the image, in this example imagine there is a login form where the user field says username
Documentation writer (you): Type David in the username field of the login form.

These have been two examples, where you respond with only one sentence explaining the action. For each of the messages you receive, you must consider the action being described and the image that you will ALWAYS NEED TO VISUALIZE to identify the element being interacted with so you can describe it in a single sentence. 
Use different verbs, not just click and type, you can say navigate to a page, press, enter text, etc. Don't use quotation marks in the response. Respond with only that sentence and nothing more.
"""

prompt_v2 = """
You are an AI specialized in documenting computer tasks. 
Your role is to describe, in one sentence, the actions to perform on the screen based on a given action and a screenshot. 
For each task, you must visualize the screenshot, identify the highlighted element, and succinctly describe the interaction using all kinds of verbs (click, type, type text, navigate to a page, press, enter text or the most convenient) and describe element by layout, color, text, placeholder and anything you consider to be a reach description. 
Respond with only the action sentence, tell the text in typing but don't use quotation marks and don't say that the element is outlined, without extra commentary.
"""

prompt_duo_v2 = """
You are an AI specialized in documenting computer tasks. 
Your role is to describe, in one sentence, the actions to perform on the screen based on a given action and a screenshot. 
For each task, you must visualize two screenshot, first of the page to know layout of the element marked on red and other of the element. Identify the highlighted element, and succinctly describe the interaction using all kinds of verbs (click, type, type text, navigate to a page, press, enter text or the most convenient) and describe element by layout, color, text, placeholder and anything you consider to be a reach description. 
Respond with only the action sentence, tell the text in typing but don't use quotation marks and don't say that the element is outlined, without extra commentary.
"""

# Function to encode the image
def encode_image(image_path, size=None):
    if size is not None:
        with Image.open(image_path) as img:
            img.thumbnail(size)
            img = img.convert("RGB")
            img.save("temp.jpg")
            image_path = "temp.jpg"

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def predict_instruction_accurate(action: str, screenshot_path: str, element_path: str) -> str:
    # Get api key
    api_key = os.environ.get("OPENAI_API_KEY")
    assert api_key, "Please set the OPENAI_API_KEY environment variable."

    client = OpenAI(
        api_key=api_key
    )

    # Getting the base64 string
    base64_image1 = encode_image(screenshot_path, (1024, 1024))
    base64_image2 = encode_image(element_path)

    response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
           "role": "user", 
           "content": prompt_duo_v2

        },{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Action: {action}",
                },{
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image1}",
                        "detail": "high"
                    },
                },{
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image2}",
                        "detail": "low"
                    },
                }
                
            ],
        }
    ],
    max_tokens=300,
    )

    print(response.choices[0].message.content)
    print(response.usage)
    
    return response.choices[0].message.content if response.choices[0].message.content else "Not"


if __name__ == "__main__":

    client = OpenAI(
        api_key="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"
    )

    # Path to your image
    image_path1 = "/workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/ButlerRobot/keywords/images/wikipedia_page.png"
    image_path2 = "/workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/ButlerRobot/keywords/images/wikipedia_href.png"
    

    # Getting the base64 string
    base64_image1 = encode_image(image_path1, (1024, 1024))
    base64_image2 = encode_image(image_path2)

    response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
           "role": "user", 
           "content": prompt_duo_v2

        },{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Type: '3000'",
                },{
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image1}",
                        "detail": "high"
                    },
                },{
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image2}",
                        "detail": "low"
                    },
                }
                
            ],
        }
    ],
    max_tokens=300,
    )
    print(response.choices[0])
    print(response.usage)