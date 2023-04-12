import io
import base64
import json
import requests
import fastdeploy as fd
from ..data_types import BBox
from PIL import Image

def request_ocr(url: str, image: Image.Image | str, lang='en', format='PNG'):
    if isinstance(image, str):
        img_str = image
    else:
        # Transform image to base64 string
        byte_io = io.BytesIO()
        image.save(byte_io, format=format)
        byte_io = byte_io.getvalue()
        img_str = base64.b64encode(byte_io).decode('utf-8')
    
    headers = {"Content-Type": "application/json"}
    data = {"data": {"image": img_str}, "parameters": {}}
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        r_json = json.loads(response.json()["result"])
        return fd.vision.utils.json_to_ocr(r_json)
    else:
        raise Exception(f"Error in ocr request. Code: {response.status_code} Text: {response.text}")
    

def get_all_text(url, image: Image.Image | str, conf_threshold: float = 0.8, lang='en') -> str | None:
    """
    Process TiffImageFile with OCR, tokenize the text and for every token create a bounding box.
    :param image: Image. Image to process.
    :param image_size: int. Size of the image.
    :return: tuple. list_tokens, list_bboxes, image, page_size
    """
    try:
        result = request_ocr(url, image, lang)
    except Exception as e:
        print(f"OCR failed for {url}: {e}")
        return None
    
    all_text = ''
    for text, confidence in zip(result.text, result.rec_scores):
    # box = [top_left-x, top_left-y, top_right-x, top_right-y, bottom_right-x, bottom_right-y, bottom_left-x, bottom_left-y]
        if not text.strip() or confidence < conf_threshold:
            continue
        all_text += text.strip() + ' '

    return all_text.strip()

def get_text_and_bbox(url, image: Image.Image, conf_threshold: float = 0.8, lang='en') -> tuple[list[str], list[BBox]] | None:
    """
    Process TiffImageFile with OCR, tokenize the text and for every token create a bounding box.
    :param image: Image. Image to process.
    :param image_size: int. Size of the image.
    :return: tuple. list_tokens, list_bboxes, image, page_size
    """
    try:
        result = request_ocr(url, image, lang)
    except Exception as e:
        print(f"OCR failed for {url}: {e}")
        return None
    
    list_tokens = []
    list_bboxes = []
    for text, confidence, box in zip(result.text, result.rec_scores, result.boxes):
    # box = [top_left-x, top_left-y, top_right-x, top_right-y, bottom_right-x, bottom_right-y, bottom_left-x, bottom_left-y]
        if not text.strip() or confidence < conf_threshold:
            continue
        list_tokens.append(text.strip())
        # Create BBox(x, y, w, h) and append to list
        list_bboxes.append(BBox(box[0], box[1], box[4] - box[0], box[5] - box[1]))

    return list_tokens, list_bboxes