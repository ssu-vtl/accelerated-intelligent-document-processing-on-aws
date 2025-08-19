```mermaid
flowchart TD
    InputBucket[(Input S3 Bucket)]
    ConfigBucket[(Configuration S3 Bucket)]
    WorkingBucket[(Working S3 Bucket)]
    OutputBucket[(Output S3 Bucket)]
    TrackingTable[(Tracking DynamoDB)]
    ConfigTable[(Configuration DynamoDB)]
    
    StateMachine((DocumentProcessing StateMachine))
    OCR((OCR Function))
    Classification((Classification Function))
    Extraction((Extraction Function))
    Assessment((Assessment Function))
    ProcessResults((ProcessResults Function))
    Summarization((Summarization Function))
    
    Bedrock((AWS Bedrock))
    Textract((AWS Textract))
    AppSync((AppSync API))
    
    InputBucket -->|Document| StateMachine
    StateMachine -->|Document| OCR
    
    OCR -->|Document| Textract
    OCR -->|Image| Bedrock
    OCR -->|OCR Results| WorkingBucket
    OCR -->|Status Update| AppSync
    OCR -->|Configuration Query| ConfigTable
    
    StateMachine -->|OCR Results| Classification
    Classification -->|Document Class| WorkingBucket
    Classification -->|Status Update| AppSync
    Classification -->|LLM Request| Bedrock
    Classification -->|Configuration Query| ConfigTable
    Classification -->|Example Data| ConfigBucket
    Classification -->|Track Document| TrackingTable
    
    StateMachine -->|Document Class| Extraction
    Extraction -->|LLM Request| Bedrock
    Extraction -->|Extracted Data| WorkingBucket
    Extraction -->|Status Update| AppSync
    Extraction -->|Configuration Query| ConfigTable
    Extraction -->|Example Data| ConfigBucket
    
    StateMachine -->|Extracted Data| Assessment
    Assessment -->|LLM Request| Bedrock
    Assessment -->|Assessment Results| WorkingBucket
    Assessment -->|Status Update| AppSync
    Assessment -->|Configuration Query| ConfigTable
    
    StateMachine -->|Assessment Results| Summarization
    Summarization -->|LLM Request| Bedrock
    Summarization -->|Document Summary| WorkingBucket
    Summarization -->|Status Update| AppSync
    Summarization -->|Configuration Query| ConfigTable
    
    StateMachine -->|Processing Results| ProcessResults
    ProcessResults -->|Final Document| OutputBucket
    ProcessResults -->|Status Update| AppSync
    ProcessResults -->|Working Data| WorkingBucket
```