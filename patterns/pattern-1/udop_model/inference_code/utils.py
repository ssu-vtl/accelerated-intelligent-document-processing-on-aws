## utility functions to process the data

from PIL import Image
import json
import boto3
import numpy as np
import s3fs
from io import BytesIO
from urllib.parse import urlparse
from textractor.parsers import response_parser

s3_client = boto3.client('s3')
fs = s3fs.S3FileSystem()

## utility functions

def get_bucket_and_key(s3_uri):
    if "s3://" not in s3_uri:
         s3_uri = "s3://" + s3_uri
    parsed = urlparse(s3_uri, allow_fragments=False)
    return {"Bucket": parsed.netloc, "Key": parsed.path.lstrip("/")}


def get_words_in_order(doc):
    """Helper method to get words from textract document in order (left to right, top to bottom)"""
    ws = []
    for p in doc.pages:
        for l in p.lines:
            for w in l.words:
                ws.append(w)
    return ws


def get_boxes_from_textract(textract, model_norm_dim=1000):
    """Gets the bounding boxes and words from the textract output"""
    doc = response_parser.parse(textract)
    words = get_words_in_order(doc)
    if len(words) == 0:
        return None, []
    bxs = []
    texts = []
    for w in words:
        bxs.append(w.bbox.as_denormalized_numpy())
        texts.append(w.text)
    bxs = np.array(bxs)
    bxs[:, 2] += bxs[:, 0]
    bxs[:, 3] += bxs[:, 1]
    bxs[:, [1, 3]] /= doc.pages[0].height
    bxs[:, [0, 2]] /= doc.pages[0].width
    bxs *= model_norm_dim
    return bxs, texts


def prepare_input_s3(ex):
    #get textract
    textract_loc = "s3://" + ex["textract"]
    with fs.open(textract_loc, "r") as f:
        textract = json.load(f)
    textract_boxes, textract_words = get_boxes_from_textract(textract)

    prompt = f"Document Classification on Transflo Dataset."
    prompt_words = prompt.split(" ")
    prompt_boxes = np.array([[0, 0, 0, 0] for _ in prompt_words])

    obj_loc = get_bucket_and_key(ex["image"])
    file_byte_string = s3_client.get_object(Bucket=obj_loc['Bucket'], Key=obj_loc['Key'])['Body'].read()
    image = Image.open(BytesIO(file_byte_string)) #<------- is RGB conversion needed?
    return {
        "prompt": prompt,
        "boxes": prompt_boxes
        if textract_boxes is None
        else np.concatenate([prompt_boxes, np.array(textract_boxes)]),
        "text": prompt_words + textract_words,
        "images": np.array(image),
        "return_tensors": "pt",
    }

def prepare_input_local(ex):
    #get textract
    textract_loc = ex["textract"]
    with open(textract_loc, "r") as f:
        textract = json.load(f)
    textract_boxes, textract_words = get_boxes_from_textract(textract)

    prompt = f"Document Classification on Transflo Dataset."
    prompt_words = prompt.split(" ")
    prompt_boxes = np.array([[0, 0, 0, 0] for _ in prompt_words])

    obj_loc = ex["image"]
    image = Image.open(obj_loc)
    return {
        "prompt": prompt,
        "boxes": prompt_boxes
        if textract_boxes is None
        else np.concatenate([prompt_boxes, np.array(textract_boxes)]),
        "text": prompt_words + textract_words,
        "images": np.array(image),
        "return_tensors": "pt",
    }