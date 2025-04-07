import os
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from idp_common import bedrock, s3, metrics, image, utils, get_config

# Configuration
CONFIG = get_config()
MAX_WORKERS = 20     # Adjust based on your needs

region = os.environ['AWS_REGION']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add thread-safe metric publishing
metric_lock = Lock()

def put_metric(name, value, unit='Count', dimensions=None):
    dimensions = dimensions or []
    with metric_lock:
        metrics.put_metric(name, value, unit, dimensions, METRIC_NAMESPACE)

def classify_single_page(page_id, page_data):
    """Classify a single page using Bedrock"""
    # Read text content from S3
    text_content = s3.get_text_content(page_data['parsedTextUri'])
    image_content = image.prepare_image(page_data['imageUri'])

    classes_config = CONFIG["classes"]

    # create a list of classes and descriptions
    CLASS_NAMES_AND_DESCRIPTIONS = '\n'.join([f"{class_obj.get('name', None)}  \t[ {class_obj.get('description', None)} ]" for class_obj in classes_config])

    classification_config = CONFIG["classification"]
    model_id = classification_config["model"]
    temperature = float(classification_config["temperature"])
    top_k = float(classification_config["top_k"])
    system_prompt = classification_config["system_prompt"]
    
    prompt_template = classification_config["task_prompt"].replace("{DOCUMENT_TEXT}", "%(DOCUMENT_TEXT)s").replace("{CLASS_NAMES_AND_DESCRIPTIONS}", "%(CLASS_NAMES_AND_DESCRIPTIONS)s")
    task_prompt = prompt_template % {
        "CLASS_NAMES_AND_DESCRIPTIONS": CLASS_NAMES_AND_DESCRIPTIONS,
        "DOCUMENT_TEXT": text_content
    }
    logger.info(f"Task prompt: {task_prompt}")
    content = [{"text": task_prompt}]

    # Add the image to content
    content.append(image.prepare_bedrock_image_attachment(image_content))

    logger.info(f"Classifying page {page_id}, {page_data}")
    
    # Invoke Bedrock with the common library
    response_with_metering = bedrock.invoke_model(
        model_id=model_id,
        system_prompt=system_prompt,
        content=content,
        temperature=temperature,
        top_k=top_k
    )
    
    response = response_with_metering["response"]
    metering = response_with_metering["metering"]
    
    # Return classification results along with page data
    classification_json = response['output']['message']['content'][0].get("text")
    final_classification = json.loads(classification_json).get("class", "Unknown")
    logger.info(f"Page {page_id} classified as {final_classification}")
    
    return {
        'page_id': page_id,
        'class': final_classification,
        'metering': metering,
        **page_data
    }

def group_consecutive_pages(results):
    """
    Group consecutive pages with the same classification into sections.
    Returns a list of sections, each containing an id, class, and pages.
    """
    sorted_results = sorted(results, key=lambda x: x['page_id'])
    sections = []
    current_group = 1
    
    if not sorted_results:
        return sections
        
    current_class = sorted_results[0]['class']
    current_pages = [sorted_results[0]]
    
    for result in sorted_results[1:]:
        if result['class'] == current_class:
            current_pages.append(result)
        else:
            sections.append({
                'id': f"{current_group}",
                'class': current_class,
                'pages': current_pages
            })
            current_group += 1
            current_class = result['class']
            current_pages = [result]
    
    sections.append({
        'id': f"{current_group}",
        'class': current_class,
        'pages': current_pages
    })
    
    return sections

def classify_pages_concurrently(pages):
    """Classify multiple pages concurrently using a thread pool"""
    all_results = []
    futures = []
    metering = {}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for page_num, page_data in pages.items():
            future = executor.submit(classify_single_page, page_num, page_data)
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                result = future.result()
                page_metering = result.pop("metering", {})
                all_results.append(result)
                
                # Merge metering using common utility
                metering = utils.merge_metering_data(metering, page_metering)
            except Exception as e:
                logger.error(f"Error in concurrent classification: {str(e)}")
                raise
    
    return all_results, metering

def handler(event, context):
    """
    Input event containing page level OCR and image data from OCR step
    """
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Config: {json.dumps(CONFIG)}")  
    
    metadata = event.get("OCRResult", {}).get("metadata")
    pages = event.get("OCRResult", {}).get("pages")

    if not all([metadata, pages]):
        raise ValueError("Missing required parameters in event")

    t0 = time.time()
    
    total_pages = len(pages)
    put_metric('BedrockRequestsTotal', total_pages)
    
    all_results, classification_metering = classify_pages_concurrently(pages)
    
    t1 = time.time()
    logger.info(f"Time taken for classification: {t1-t0:.2f} seconds")

    sections = group_consecutive_pages(all_results)
    
    # Merge incoming metering with classification metering
    incoming_metering = metadata.pop("metering", {})
    merged_metering = utils.merge_metering_data(classification_metering, incoming_metering)
    
    logger.info(f"Merged metering data: {json.dumps(merged_metering)}")
    metadata["metering"] = merged_metering
    
    response = {
        "metadata": metadata,
        "sections": sections,
    }
    
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response