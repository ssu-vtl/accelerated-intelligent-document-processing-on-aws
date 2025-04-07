# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import os
import json
import time
import logging
from idp_common import bedrock, s3, metrics, image, get_config

CONFIG = get_config()

METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']
OCR_TEXT_ONLY = os.environ.get('OCR_TEXT_ONLY', 'false').lower() == 'true'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def put_metric(name, value, unit='Count', dimensions=None):
    dimensions = dimensions or []
    metrics.put_metric(name, value, unit, dimensions, METRIC_NAMESPACE)

def invoke_llm(page_images, class_label, document_text):
    classes_config = CONFIG["classes"]
    class_config = next((class_obj for class_obj in classes_config if class_obj.get('name', '').lower() == class_label.lower()), None)
    attributes = class_config.get('attributes', []) if class_config else []

    # Create a list of attributes and descriptions
    ATTRIBUTE_NAMES_AND_DESCRIPTIONS = '\n'.join([f"{attr.get('name', None)}  \t[ {attr.get('description', None)} ]" for attr in attributes])

    extraction_config = CONFIG["extraction"]
    model_id = extraction_config["model"]
    temperature = float(extraction_config["temperature"])
    top_k = float(extraction_config["top_k"])
    system_prompt = extraction_config["system_prompt"]
    
    prompt_template = extraction_config["task_prompt"].replace("{DOCUMENT_TEXT}", "%(DOCUMENT_TEXT)s").replace("{DOCUMENT_CLASS}", "%(DOCUMENT_CLASS)s").replace("{ATTRIBUTE_NAMES_AND_DESCRIPTIONS}", "%(ATTRIBUTE_NAMES_AND_DESCRIPTIONS)s")
    task_prompt = prompt_template % {
        "DOCUMENT_TEXT": document_text,
        "DOCUMENT_CLASS": class_label,
        "ATTRIBUTE_NAMES_AND_DESCRIPTIONS": ATTRIBUTE_NAMES_AND_DESCRIPTIONS
    }
    logger.info(f"Task prompt: {task_prompt}")
    content = [{"text": task_prompt}]

    # Bedrock currently supports max 20 image attachments
    # Per science team recommendation, we limit image attachments to 1st 20 pages.
    if len(page_images) > 20:
        page_images = page_images[:20] 
        logger.error(f"Number of pages in the document is greater than 20. Processing with only the first 20 pages")
    
    # Add image attachments to the content
    if page_images:
        logger.info(f"Attaching images to prompt, for {len(page_images)} pages.")
        for img in page_images:
            content.append(image.prepare_bedrock_image_attachment(img))

    # Invoke the model with the common library
    request_start_time = time.time()
    
    # Track total requests
    put_metric('BedrockRequestsTotal', 1)
    
    response_with_metering = bedrock.invoke_model(
        model_id=model_id,
        system_prompt=system_prompt,
        content=content,
        temperature=temperature,
        top_k=top_k
    )
    
    total_duration = time.time() - request_start_time
    put_metric('BedrockTotalLatency', total_duration * 1000, 'Milliseconds')
    
    # Extract text from response
    entities = bedrock.extract_text_from_response(response_with_metering)
    return entities, response_with_metering["metering"]

def handler(event, context):
    """
    Input event for single document / section of given type
    """
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Config: {json.dumps(CONFIG)}")  
    
    # Get parameters from event
    metadata = event.get("metadata")
    section = event.get("section")
    output_bucket = event.get("output_bucket")   
    object_key = metadata.get("object_key")
    class_label = section.get("class")
    pages = section.get("pages")
    page_ids = [page['page_id'] for page in pages]
    output_prefix = object_key

    # Sort pages by page number
    sorted_page_ids = sorted([page['page_id'] for page in section['pages']], key=int)
    start_page = int(sorted_page_ids[0])
    end_page = int(sorted_page_ids[-1])
    logger.info(f"Processing {len(sorted_page_ids)} pages from {object_key} {section}, class {class_label}: {start_page}-{end_page}")

    # Read document text from all pages in order
    t0 = time.time()
    document_texts = []
    for page in sorted(section['pages'], key=lambda x: int(x['page_id'])):
        text_path = page['parsedTextUri']
        page_text = s3.get_text_content(text_path)
        document_texts.append(page_text)
    
    document_text = '\n'.join(document_texts)
    t1 = time.time()
    logger.info(f"Time taken to read text content: {t1-t0:.2f} seconds")

    # Read page images
    page_images = []
    for page in sorted(section['pages'], key=lambda x: int(x['page_id'])):
        imageUri = page['imageUri']
        image_content = image.prepare_image(imageUri)
        page_images.append(image_content)
    
    t2 = time.time()
    logger.info(f"Time taken to read images: {t2-t1:.2f} seconds")

    # Process with LLM
    extracted_entities_str, extraction_metering = invoke_llm(
        page_images,
        class_label,
        document_text,
    )
    t3 = time.time()
    logger.info(f"Time taken by bedrock: {t3-t2:.2f} seconds")

    try:
        extracted_entities = json.loads(extracted_entities_str)
    except Exception as e:
        logger.error(f"Error parsing LLM output - invalid JSON?: {extracted_entities_str} - {e}")
        logger.info(f"Using unparsed LLM output.")
        extracted_entities = extracted_entities_str

    # Write results - emulate BDA for pattern consistency
    output = {
        "document_class": {
            "type": class_label
        },
        "split_document": {
            "page_indices": page_ids
        },
        "inference_result": extracted_entities
    }
    output_key = f"{output_prefix}/sections/{section['id']}/result.json"
    s3.write_content(output, output_bucket, output_key, content_type='application/json')
    
    # Track metrics
    put_metric('InputDocuments', 1)
    put_metric('InputDocumentPages', len(pages))
    
    result = {
        "section": {
            "id": section['id'],
            "class": section['class'],
            "page_ids": page_ids,
            "outputJSONUri": f"s3://{output_bucket}/{output_key}",
        },
        "pages": pages,
        "metering": extraction_metering
    }
    
    logger.info(f"Response: {json.dumps(result, default=str)}")
    return result