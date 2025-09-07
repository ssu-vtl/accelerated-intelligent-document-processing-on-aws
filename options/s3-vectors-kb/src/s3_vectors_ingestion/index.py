import boto3
import json
import os
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Iterator, Any, Union
from idp_common.bedrock.client import BedrockClient
from idp_common.dynamodb.client import DynamoDBClient
from idp_common.s3 import get_s3_client
from idp_common.s3vectors.client import S3VectorsClient
from idp_common.utils import build_s3_uri
from idp_common.config import get_config

# --- Constants ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
# --- Environment Variables ---
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
S3_VECTORS_BUCKET = os.environ["S3_VECTORS_BUCKET"]
S3_VECTORS_CATALOG_TABLE = os.environ["S3_VECTORS_CATALOG_TABLE"]
CONFIGURATION_TABLE_NAME = os.environ.get("CONFIGURATION_TABLE_NAME")
S3_VECTORS_INDEX_NAME = os.environ.get("S3_VECTORS_INDEX_NAME", "default-index")
EMBEDDING_MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
MAX_VECTORS_PER_BATCH = int(os.environ.get("MAX_VECTORS_PER_BATCH", "100"))
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))
USE_LLM_CLASSIFICATION = os.environ.get("USE_LLM_CLASSIFICATION", "false").lower() == "true"
CLASSIFICATION_MODEL_ID = os.environ.get("CLASSIFICATION_MODEL_ID", "us.amazon.nova-micro-v1:0")
STACK_NAME = os.environ.get('STACK_NAME', 'GenAI-IDP')

# --- AWS Service Clients & Logger ---
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
s3_client = get_s3_client()
s3vectors_client = S3VectorsClient()
bedrock_client = BedrockClient()
cloudwatch_client = boto3.client('cloudwatch')
catalog_table = DynamoDBClient(S3_VECTORS_CATALOG_TABLE)

# --- Main Handler ---
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for S3 vector ingestion. Supports two triggers:
    1. EventBridge Scheduler: Scans the entire output bucket for new/modified documents.
    2. S3 Event (Legacy/Testing): Processes a single document folder based on an S3 trigger.
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Processing event: {json.dumps(event, default=str)}")
    
    try:
        active_filter_keys = load_filter_keys_from_config()

        if event.get('source') == 'scheduler' and event.get('action') == 'scan_and_ingest':
            logger.info("Starting scheduled ingestion scan.")
            result = scan_and_ingest_documents(active_filter_keys)
        elif 'Records' in event and 's3' in event['Records'][0]:
            logger.info("Processing S3 event trigger (legacy mode).")
            result = process_s3_event(event, active_filter_keys)
        else:
            logger.error(f"Unsupported event type: {event}")
            return {'statusCode': 400, 'body': json.dumps('Unsupported event type')}
        
        latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        emit_ingestion_metrics(latency_ms, True, result.get('vectors_processed', 0), result.get('documents_processed', 0))
        return {'statusCode': 200, 'body': json.dumps(result)}

    except Exception:
        logger.error("Fatal error during event processing.", exc_info=True)
        latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        emit_ingestion_metrics(latency_ms, False, 0, 0)
        raise

# --- Event Processing Logic ---
def scan_and_ingest_documents(filter_keys: List[str]) -> Dict[str, Any]:
    """Scans the output bucket for document folders and ingests new or updated ones."""
    documents_processed = vectors_processed = 0
    
    for document_folder in get_document_folders(OUTPUT_BUCKET):
        try:
            if is_document_processed(document_folder):
                vectors_count = process_document_folder(document_folder, filter_keys)
                if vectors_count > 0:
                    documents_processed += 1
                    vectors_processed += vectors_count
        except Exception as e:
            logger.error(f"Error processing document folder {document_folder}: {e}", exc_info=True)
            # Continue processing other documents

    result = {'documents_processed': documents_processed, 'vectors_processed': vectors_processed}
    logger.info(f"Scan complete: {json.dumps(result)}")
    return result

def process_s3_event(event: Dict[str, Any], filter_keys: List[str]) -> Dict[str, Any]:
    """Processes a legacy S3 event, targeting a single document folder."""
    total_vectors = 0
    for record in event['Records']:
        vector_length = process_document_folder(record['s3']['object']['key'], filter_keys)
        total_vectors += vector_length
    return {'documents_processed': len(event['Records']), 'vectors_processed': total_vectors}

def process_document_folder(document_folder: str, filter_keys: List[str]) -> int:
    """Extracts, chunks, embeds, and stores vectors for a single document folder."""
    reader = DocumentReader(OUTPUT_BUCKET, document_folder)
    text_chunks = reader.extract_text_chunks()
    if not text_chunks:
        logger.warning(f"No text chunks extracted from document folder: {document_folder}")
        return 0

    vectors = []
    for page_data in text_chunks:
        page_metadata = {k: v for k, v in page_data.items() if k != 'chunks'}
        
        for chunk_idx, chunk_text in enumerate(page_data.get('chunks', [])):
            try:
                embedding = bedrock_client.generate_embedding(text=chunk_text, model_id=EMBEDDING_MODEL_ID)
                if not embedding:
                    continue
                    
                # Combine all metadata
                metadata = {
                    **page_metadata,
                    'text': chunk_text,
                    'chunk_idx': chunk_idx
                }
                
                # Add classification if enabled
                if USE_LLM_CLASSIFICATION and filter_keys:
                    metadata.update(classify_chunk_metadata(chunk_text, filter_keys))
                
                # Clean up confidence fields
                if 'average_confidence' in metadata:
                    metadata['confidence'] = metadata.pop('average_confidence')
                metadata.pop('min_confidence', None)
                metadata.pop('count', None)
                
                vectors.append((embedding, metadata))
            except Exception:
                logger.error(f"Failed to create vector for chunk {chunk_idx}", exc_info=True)
    
    store_vectors_in_batches(vectors)
    return len(vectors)

# --- Idempotency Check ---
def is_document_processed(document_id: str) -> bool:
    """Checks DynamoDB to see if this document has been processed."""
    try:
        response = catalog_table.get_item(Key={'PK': f"DOC#{document_id}"})
        return response.get('Item') is None  # Return True if not found (needs processing)
    except Exception:
        logger.warning(f"Failed to check processing status for {document_id}", exc_info=True)
        return True  # Assume needs processing if check fails

# --- S3 Bucket Scanning ---
def get_document_folders(bucket_name: str, pages_prefix: str = None) -> Union[List[Dict[str, str]], Iterator[str]]:
    """Iteratively yields top-level document folders from an S3 bucket.
    
    If pages_prefix is provided, returns a list of folder prefixes within that prefix.
    """
    if pages_prefix is not None:
        return _get_page_folders(bucket_name, pages_prefix)
    else:
        return _get_top_level_folders(bucket_name)

def _get_page_folders(bucket_name: str, pages_prefix: str) -> List[Dict[str, str]]:
    """Returns a list of page folder prefixes within the given prefix."""
    paginator = s3_client.get_paginator('list_objects_v2')
    
    logger.info(f"Scanning bucket '{bucket_name}' for folders in prefix '{pages_prefix}'")
    folders = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=pages_prefix, Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append({'Prefix': prefix.get('Prefix', '')})
    return folders

def _get_top_level_folders(bucket_name: str) -> Iterator[str]:
    """Generator that yields top-level document folders."""
    paginator = s3_client.get_paginator('list_objects_v2')
    logger.info(f"Scanning bucket '{bucket_name}' for document folders.")
    for page in paginator.paginate(Bucket=bucket_name, Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folder_name = prefix.get('Prefix', '').strip('/')
            if folder_name:
                yield folder_name

# --- Document Reading and Chunking ---
class DocumentReader:
    """Encapsulates the complex logic of reading text and metadata from the S3 output structure."""
    def __init__(self, bucket: str, folder: str):
        self.bucket = bucket
        self.folder = folder
        self.s3_uri = f"s3://{bucket}/{folder}"

    def extract_text_chunks(self) -> List[Dict[str, Any]]:
        pages = self._get_preferred_text()
        if not pages:
            return []
        
        processed_pages = []
        for page_data in pages:
            result_data, confidence_score, page_number, s3_uri, document_type, document_id = page_data
            
            # Create page metadata without the text
            page_info = {
                **confidence_score,
                **page_number, 
                **s3_uri,
                **document_type,
                **document_id,
                "chunks": self._create_chunks({"text": result_data.get("text", "")})
            }
            processed_pages.append(page_info)

        return processed_pages

    def _get_preferred_text(self) -> Tuple[Optional[str], str]:
        pages = get_document_folders(self.bucket, pages_prefix=f'{self.folder}/pages/')
        document_type_raw = json.loads(s3_client.get_object(Bucket=self.bucket, Key=f"{self.folder}/sections/1/result.json")['Body'].read().decode('utf-8'))
        document_type = {"document_type": document_type_raw.get("document_class").get("type")}
        if pages:  
            page_texts = []  
            for page_num in pages:
                try:
                    # Get result.json
                    
                    result_data = json.loads(s3_client.get_object(Bucket=self.bucket, 
                        Key=f"{page_num['Prefix']}result.json")['Body'].read().decode('utf-8'))
                    
                    # Get textConfidence.json
                    confidence_data = json.loads(s3_client.get_object(Bucket=self.bucket, 
                        Key=f"{page_num['Prefix']}textConfidence.json")['Body'].read().decode('utf-8'))
                    
                    confidence_score = self._calculate_confidence_stats(confidence_data.get('text'))
                    page_number = {"page_number": f"{page_num['Prefix'].split("/")[:-1]}"}
                    s3_uri = {'s3_uri': f'{self.s3_uri}/pages/{page_number}'}
                    document_id = {'document_id': self.folder}
                    if result_data and confidence_score:
                        page_texts.append((result_data, confidence_score, page_number, s3_uri, document_type, document_id))

                except Exception as e:
                    print(f"Error reading page {page_num}: {e}")
                    continue
            return page_texts
        return None, "none"
    
    def _calculate_confidence_stats(self, text_data):
        lines = text_data.splitlines()
        scores = []
        
        for line in lines[2:]:  # Skip header lines
            try:
                parts = line.split('|')
                if len(parts) >= 3 and parts[-2].strip():
                    scores.append(float(parts[-2].strip()))
            except (ValueError, IndexError):
                continue

        if not scores:
            return {"average_confidence": 0, "min_confidence": 0, "count": 0}

        return {
            "average_confidence": sum(scores) / len(scores),
            "min_confidence": min(scores),
            "count": len(scores)
        }


    def _create_chunks(self, text_data: Dict[str, Any]) -> List[str]:
        text = text_data.get('text', '')
        words = text.split()
        
        if not words:
            return []

        # Single chunk if text is small enough
        if len(words) <= CHUNK_SIZE:
            return [text]

        # Create overlapping chunks
        chunks = []
        step = CHUNK_SIZE - CHUNK_OVERLAP
        for start in range(0, len(words), step):
            chunk_text = ' '.join(words[start:start + CHUNK_SIZE])
            chunks.append(chunk_text)
        
        return chunks

def store_vectors_in_batches(vectors: List[Tuple]):
    """Stores vectors in S3 Vectors using batches and updates the DynamoDB catalog."""
    if not vectors: 
        return
    
    for i in range(0, len(vectors), MAX_VECTORS_PER_BATCH):
        batch_tuples = vectors[i:i + MAX_VECTORS_PER_BATCH]
        batch = []
        
        for embedding, flattened_data in batch_tuples:
            vector_key = f"{flattened_data['document_id']}_{flattened_data['page_number']}_{flattened_data['chunk_idx']}"
            # Remove chunk_idx from metadata since it's now in the key
            metadata = {k: v for k, v in flattened_data.items() if k != 'chunk_idx'}
            
            #  Retained section_type as an uninitialized system-side filterable key
            vector_obj = {
                "objectId": vector_key,
                "vector": embedding,
                "metadata": metadata
            }
            batch.append(vector_obj)
        
        try:
            s3vectors_client.put_vectors(
                vectorBucketName=S3_VECTORS_BUCKET,
                indexName=S3_VECTORS_INDEX_NAME,
                vectors=batch
            )
            time.sleep(0.2)  # Rate limiting
        except Exception:
            logger.error(f"Failed to store batch starting at index {i}", exc_info=True)
            raise  # Fail fast on vector storage errors
    
    # Update catalog after successful storage
    if vectors:
        first_vector_metadata = vectors[0][1]
        update_dynamodb_catalog({
            "length": str(len(vectors)), 
            "document_id": first_vector_metadata.get("document_id"), 
            "s3_uri": first_vector_metadata.get("s3_uri")
        })

def update_dynamodb_catalog(vector: Dict):
    """Updates the DynamoDB catalog for a single processed vector chunk."""
    try:
        catalog_table.put_item(Item={
            'PK': f"DOC#{vector['document_id']}",
            's3_uri': vector['s3_uri'],
            'number_of_vectors': vector['length'],
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.error(f"Failed to update catalog for document {vector.get('document_id')}", exc_info=True)

# --- Configuration & Classification ---
def load_filter_keys_from_config() -> List[str]:
    """Loads custom filterable metadata keys from the DynamoDB configuration table."""
    if not CONFIGURATION_TABLE_NAME:
        return []
    
    try:
        config = get_config(CONFIGURATION_TABLE_NAME)
        keys = config.get('s3Vectors', {}).get('filterableMetadataKeys', [])
        
        # Handle both list and comma-separated string formats
        if isinstance(keys, list):
            parsed = [str(v).strip() for v in keys if str(v).strip()]
        elif isinstance(keys, str):
            parsed = [v.strip() for v in keys.split(',') if v.strip()]
        else:
            parsed = []
            
        logger.info(f"Loaded {len(parsed)} filterable keys from config")
        return parsed[:6]  # Limit to 6 keys
    except Exception:
        logger.warning("Failed to load filter keys from config", exc_info=True)
        return []

def classify_chunk_metadata(text: str, fields: List[str]) -> Dict[str, Any]:
    """Uses a Bedrock LLM to classify a text chunk against a defined schema."""
    if not fields:
        return {}
        
    try:
        response = bedrock_client.invoke_model(
            model_id=CLASSIFICATION_MODEL_ID,
            system_prompt='You are an expert document classifier. Return only a valid JSON object with the requested fields.',
            content=[{"text": f"Analyze and classify this text using fields {fields}: {text[:500]}..."}],
            temperature=0.1,
            max_tokens=500,
        )
        
        classified_data = json.loads(response["content"][0]["text"])
        return {field: classified_data.get(field, "unknown") for field in fields}
    except Exception:
        logger.warning("LLM classification failed", exc_info=True)
        return {field: "unknown" for field in fields}

# --- CloudWatch Metrics ---
def emit_ingestion_metrics(latency_ms: float, success: bool, vectors: int, docs: int):
    """  Not implemented currently
    Emits CloudWatch metrics for ingestion performance and success rate.

    try:
        cloudwatch_client.put_metric_data(
            Namespace=STACK_NAME,
            MetricData=[
                {'MetricName': 'IngestionLatency', 'Value': latency_ms, 'Unit': 'Milliseconds'},
                {'MetricName': 'IngestionSuccessRate', 'Value': 100.0 if success else 0.0, 'Unit': 'Percent'},
                {'MetricName': 'DocumentsIngested', 'Value': docs, 'Unit': 'Count'},
                {'MetricName': 'VectorsIngested', 'Value': vectors, 'Unit': 'Count'},
            ]
        )
    except Exception:
        logger.warning("Failed to emit CloudWatch metrics.", exc_info=True)
    """
    pass