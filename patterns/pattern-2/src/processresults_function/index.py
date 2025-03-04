import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Consolidates the results from multiple extraction steps into a single output.
    
    Expected event structure:
        {
            "output_bucket": "idp-udop-3-outputbucket-zzuuzg2qi52q",
            "metadata": {
                "input_bucket": <BUCKET>,
                "object_key": <KEY>,
                "output_bucket": <BUCKET>,
                "output_prefix": <PREFIX>,
                "num_pages": <NUMBER OF PAGES IN ORIGINAL INPUT DOC>
            },
            "extraction_results": [
                {
                "section": {
                    "id": <ID>,
                    "class": <CLASS>,
                    "page_ids": [<PAGEID>, ...],
                    "extracted_entities": "{...}",
                    "outputJSONUri": <S3_URI>,
                },
                "pages": [
                    {
                    "page_id": <NUM>,
                    "class": <TYPE or CLASS>,
                    "rawTextUri": <S3_URI>,
                    "parsedTextUri": <S3_URI>,
                    "imageUri": <S3_URI>
                    }
                ],
                ...
            ]
        }

    The Output must observe the structure below.. it is consumed by the GenAIIDP parent stack workflow tracker to update job status/UI etc: 
        {
            'Sections': [
                {
                    "Id": <ID>,
                    "PageIds": [<PAGEID>, ...],
                    "Class": <CLASS>,
                    "OutputJSONUri": <S3_URI>
                }
            ],
            'Pages': [
                "Id": <ID>,
                "Class": <CLASS>,
                "RawTextUri": <S3_URI>,
                "ParsedTextUri": <S3_URI>,
                "ImageUri": <S3_URI>
            ],
            'PageCount': <NUMBER OF PAGES IN ORIGINAL INPUT DOC>
        }
    """
    logger.info(f"Processing event: {json.dumps(event)}")

    sections=[]
    for result in event.get("extraction_results"):
        section = result.get("section")
        sections.append({
            "Id": section.get("id"),
            "PageIds": section.get("page_ids"),
            "Class": section.get("class"),
            "OutputJSONUri": section.get("outputJSONUri")
        })

    pages=[]
    for result in event.get("extraction_results"):
        for page in result.get("pages"):
            pages.append({
                "Id": page.get("page_id"),
                "Class": page.get("class"),
                "TextUri": page.get("rawTextUri"),
                "ImageUri": page.get("imageUri")
            })  

    statemachine_output = {
        "Sections": sections,
        "Pages": pages,
        "PageCount": event.get("metadata").get("num_pages")
    }

    return statemachine_output

        
