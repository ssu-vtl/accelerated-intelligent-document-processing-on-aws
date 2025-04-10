# Changelog

## [Unreleased] - fix/refactor-to-modularize branch

### Major Changes

#### Unified Document Model Architecture
- Introduced a consistent Document object model across all services
- Implemented full Document-based input/output for OCR, Classification, and Extraction services
- Added `Document`, `Section`, and `Page` classes with comprehensive serialization methods
- Added `from_dict()` and `to_dict()` methods to support seamless serialization/deserialization

#### Service Modularization
- Created a unified service architecture with consistent interfaces
- Refactored OcrService to accept and return Document objects
- Refactored ClassificationService to work with Document objects
- Refactored ExtractionService to process document sections within Document objects
- Updated Pattern-1, Pattern-2, and Pattern-3 functions to use the new Document model

#### Multi-Backend Support
- Enhanced ClassificationService with support for both Bedrock and SageMaker/UDOP backends
- Added configuration-based backend selection
- Implemented efficient metering for both backends
- Optimized handling of Claude 3.5 and 3.7 models

#### Workflow Optimization
- Improved state machine workflows to utilize the Document object for state tracking
- Optimized extraction process to create focused Document instances with only relevant sections
- Implemented better error handling with standardized error reporting
- Added support for parallel processing of document sections

#### Package Improvements
- Created a modular package structure with granular dependency management
- Added the ability to install specific components via extras (core, ocr, classification, extraction)
- Improved consistency of imports and initialization patterns
- Enhanced request/response logging for better debugging

### Benefits

1. **Improved Maintainability**
   - Consistent interfaces across services reduce code duplication
   - Clear data flow between components with standardized objects
   - Unified error handling approach

2. **Enhanced Flexibility**
   - Support for multiple backend services (Bedrock, SageMaker)
   - Configuration-driven behavior changes
   - Simplified extension of services for new backends

3. **Better Performance**
   - Optimized document processing with focused document instances
   - Reduced memory usage by storing large results in S3
   - Parallel processing capabilities

4. **Developer Experience**
   - Comprehensive Jupyter notebook showcasing end-to-end processing
   - Improved documentation with code examples
   - Granular package installation options

5. **Integration Readiness**
   - Standardized interfaces make integration with other systems easier
   - Consistent metadata and metering for monitoring and billing
   - Clear separation of concerns between services

### Technical Updates

- Added support for Claude 3.5 and 3.7 models
- Updated workflow state machines for all patterns
- Refactored Lambda functions in all three patterns
- Enhanced S3 URI management for resource tracking
- Improved configuration handling with typed defaults
- Added complete example notebook demonstrating the Document-based workflow
- Fixed various bugs related to serialization and error handling
- Optimized extraction process to work with focused documents

### Example Applications

1. **Insurance Document Processing**
   - Updated example notebook demonstrating insurance document processing
   - Showcases OCR, classification, and extraction with the unified Document model
   - Uses real AWS services (S3, Textract, Bedrock) for accurate demonstration

2. **Banking Document Processing**
   - Enhanced BDA pattern for banking document workflows
   - Updated state machine to leverage Document objects for complete traceability
   - Improved error handling and metering for production scenarios

3. **Multi-Backend Classification**
   - Added support for both Bedrock LLMs and SageMaker UDOP models
   - Simplified switching between backends via configuration
   - Consistent interface regardless of backend choice