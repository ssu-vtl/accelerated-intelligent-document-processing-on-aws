import os
import json
import torch
import logging
from transformers import AutoProcessor

from udop import UDOPModel
from utils import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def model_fn(model_dir):
    """
    Load the model for inference
    """
    logger.info("Starting model loading...")
    try:
        model = UDOPModel()
        model.load_state_dict(torch.load(os.path.join(model_dir, 'model.pth')))
        logger.info("Model architecture: %s", model)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", device)
        if torch.cuda.is_available():
            logger.info("CUDA device count: %d", torch.cuda.device_count())
            logger.info("CUDA device name: %s", torch.cuda.get_device_name(0))

        model.to(device)
        logger.info("Model successfully loaded and moved to device")
        return model
    except Exception as e:
        logger.error("Error loading model: %s", str(e), exc_info=True)
        raise

def predict_fn(input_data, model):
    """
    Apply model to the incoming request
    """
    logger.info("Starting prediction...")
    try:
        logger.info("Input data type: %s", type(input_data))
        input_data = prepare_input_s3(input_data)
        logger.info("Input data prepared from S3")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device for inference: %s", device)
        
        # Process input
        logger.info("Loading processor...")
        processor = AutoProcessor.from_pretrained("nielsr/udop-large", apply_ocr=False)
        
        logger.info("Processing input with AutoProcessor...")
        encoding = processor(**input_data)
        logger.info("Encoding keys: %s", encoding.keys())
        
        # Move the processed tensors to device
        logger.info("Moving tensors to device...")
        encoding = {k: v.to(device) if isinstance(v, torch.Tensor) else v 
                   for k, v in encoding.items()}
        
        # Log tensor shapes and devices
        for k, v in encoding.items():
            if isinstance(v, torch.Tensor):
                logger.info("Tensor %s - Shape: %s, Device: %s", 
                          k, v.shape, v.device)

        # Generate prediction
        logger.info("Generating prediction...")
        with torch.no_grad():
            outputs = model.model.generate(**encoding)
        logger.info("Output shape: %s", outputs.shape)

        # Decode output
        logger.info("Decoding prediction...")
        prediction = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        logger.info("Final prediction: %s", prediction)

        return prediction
    except Exception as e:
        logger.error("Error during prediction: %s", str(e), exc_info=True)
        raise

def input_fn(request_body, request_content_type):
    """
    Deserialize and prepare the prediction input
    """
    logger.info("Processing input with content type: %s", request_content_type)
    try:
        if request_content_type == "application/json":
            request = json.loads(request_body)
            logger.info("Successfully parsed JSON input")
        else:
            request = request_body
            logger.info("Using raw input")
        logger.info("Input type: %s", type(request))
        return request
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", str(e))
        logger.error("Received body: %s", request_body)
        raise ValueError(f"Invalid JSON input: {str(e)}. Received: {request_body}")
    except Exception as e:
        logger.error("Error in input processing: %s", str(e), exc_info=True)
        raise

def output_fn(prediction, response_content_type):
    """
    Serialize and prepare the prediction output
    """
    logger.info("Formatting output with content type: %s", response_content_type)
    try:
        if response_content_type == "application/json":
            response = json.dumps({"prediction": prediction})
            logger.info("Formatted JSON response")
        else:
            response = str(prediction)
            logger.info("Formatted string response")
        return response
    except Exception as e:
        logger.error("Error in output formatting: %s", str(e), exc_info=True)
        raise