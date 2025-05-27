"""
Extraction service for documents using LLMs.

This module provides a service for extracting fields and values from documents
using LLMs, with support for text and image content.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List

from idp_common import bedrock, image, metrics, s3, utils
from idp_common.models import Document

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting fields from documents using LLMs."""

    def __init__(self, region: str = None, config: Dict[str, Any] = None):
        """
        Initialize the extraction service.

        Args:
            region: AWS region for Bedrock
            config: Configuration dictionary
        """
        self.config = config or {}
        self.region = (
            region or self.config.get("region") or os.environ.get("AWS_REGION")
        )

        # Get model_id from config for logging
        model_id = self.config.get("model_id") or self.config.get("extraction", {}).get(
            "model"
        )
        logger.info(f"Initialized extraction service with model {model_id}")

    def _get_class_attributes(self, class_label: str) -> List[Dict[str, Any]]:
        """
        Get attributes for a specific document class from configuration.

        Args:
            class_label: The document class name

        Returns:
            List of attribute configurations
        """
        classes_config = self.config.get("classes", [])
        class_config = next(
            (
                class_obj
                for class_obj in classes_config
                if class_obj.get("name", "").lower() == class_label.lower()
            ),
            None,
        )
        return class_config.get("attributes", []) if class_config else []

    def _format_attribute_descriptions(self, attributes: List[Dict[str, Any]]) -> str:
        """
        Format attribute descriptions for the prompt.

        Args:
            attributes: List of attribute configurations

        Returns:
            Formatted attribute descriptions as a string
        """
        return "\n".join(
            [
                f"{attr.get('name', '')}  \t[ {attr.get('description', '')} ]"
                for attr in attributes
            ]
        )

    def _prepare_prompt_from_template(
        self,
        prompt_template: str,
        substitutions: Dict[str, str],
        required_placeholders: List[str] = None,
    ) -> str:
        """
        Prepare prompt from template by replacing placeholders with values.

        Args:
            prompt_template: The prompt template with placeholders
            substitutions: Dictionary of placeholder values
            required_placeholders: List of placeholder names that must be present in the template

        Returns:
            String with placeholders replaced by values

        Raises:
            ValueError: If a required placeholder is missing from the template
        """
        from idp_common.bedrock import format_prompt

        return format_prompt(prompt_template, substitutions, required_placeholders)

    def _build_content_with_few_shot_examples(
        self,
        task_prompt_template: str,
        document_text: str,
        class_label: str,
        attribute_descriptions: str,
    ) -> List[Dict[str, Any]]:
        """
        Build content array with few-shot examples inserted at the FEW_SHOT_EXAMPLES placeholder.

        Args:
            task_prompt_template: The task prompt template containing {FEW_SHOT_EXAMPLES}
            document_text: The document text content
            class_label: The document class label
            attribute_descriptions: Formatted attribute names and descriptions

        Returns:
            List of content items with text and image content properly ordered
        """
        # Split the task prompt at the FEW_SHOT_EXAMPLES placeholder
        parts = task_prompt_template.split("{FEW_SHOT_EXAMPLES}")

        if len(parts) != 2:
            # Fallback to regular prompt processing if placeholder not found or malformed
            task_prompt = self._prepare_prompt_from_template(
                task_prompt_template,
                {
                    "DOCUMENT_TEXT": document_text,
                    "DOCUMENT_CLASS": class_label,
                    "ATTRIBUTE_NAMES_AND_DESCRIPTIONS": attribute_descriptions,
                },
                required_placeholders=[
                    "DOCUMENT_TEXT",
                    "DOCUMENT_CLASS",
                    "ATTRIBUTE_NAMES_AND_DESCRIPTIONS",
                ],
            )
            return [{"text": task_prompt}]

        # Replace other placeholders in the prompt parts
        before_examples = self._prepare_prompt_from_template(
            parts[0],
            {
                "DOCUMENT_TEXT": document_text,
                "DOCUMENT_CLASS": class_label,
                "ATTRIBUTE_NAMES_AND_DESCRIPTIONS": attribute_descriptions,
            },
            required_placeholders=[],  # Don't enforce required placeholders for partial templates
        )

        after_examples = self._prepare_prompt_from_template(
            parts[1],
            {
                "DOCUMENT_TEXT": document_text,
                "DOCUMENT_CLASS": class_label,
                "ATTRIBUTE_NAMES_AND_DESCRIPTIONS": attribute_descriptions,
            },
            required_placeholders=[],  # Don't enforce required placeholders for partial templates
        )

        # Build content array
        content = []

        # Add the part before examples
        if before_examples.strip():
            content.append({"text": before_examples})

        # Add few-shot examples from config for this specific class
        examples_content = self._build_few_shot_examples_content(class_label)
        content.extend(examples_content)

        # Add the part after examples
        if after_examples.strip():
            content.append({"text": after_examples})

        return content

    def _build_few_shot_examples_content(
        self, class_label: str
    ) -> List[Dict[str, Any]]:
        """
        Build content items for few-shot examples from the configuration for a specific class.

        Args:
            class_label: The document class label to get examples for

        Returns:
            List of content items containing text and image content for examples
        """
        content = []
        classes = self.config.get("classes", [])

        # Find the specific class that matches the class_label
        target_class = None
        for class_obj in classes:
            if class_obj.get("name", "").lower() == class_label.lower():
                target_class = class_obj
                break

        if not target_class:
            logger.warning(
                f"No class found matching '{class_label}' for few-shot examples"
            )
            return content

        # Get examples from the target class only
        examples = target_class.get("examples", [])
        for example in examples:
            attributes_prompt = example.get("attributesPrompt")
            image_path = example.get("imagePath")

            if attributes_prompt:
                content.append({"text": attributes_prompt})

            if image_path:
                try:
                    # Load image content from the path
                    import os

                    from idp_common import image, s3

                    # Handle different path types
                    if image_path.startswith("s3://"):
                        # Direct S3 URI
                        image_content = s3.get_binary_content(image_path)
                    else:
                        # Check if CONFIGURATION_BUCKET environment variable is set
                        config_bucket = os.environ.get("CONFIGURATION_BUCKET")
                        if config_bucket:
                            # Use environment bucket with imagePath as key
                            s3_uri = f"s3://{config_bucket}/{image_path}"
                            image_content = s3.get_binary_content(s3_uri)
                        else:
                            # Read from local filesystem
                            # Use ROOT_DIR environment variable if set, otherwise calculate from service location
                            root_dir = os.environ.get("ROOT_DIR")
                            if root_dir:
                                # Use relative path from ROOT_DIR
                                full_image_path = os.path.join(root_dir, image_path)
                                full_image_path = os.path.normpath(full_image_path)
                                with open(full_image_path, "rb") as f:
                                    image_content = f.read()
                            else:
                                # throw an error if neither CONFIGURATION_BUCKET nor ROOT_DIR is not set
                                raise ValueError(
                                    "No CONFIGURATION_BUCKET or ROOT_DIR set. Cannot read example image from local filesystem."
                                )

                    # Prepare image content for Bedrock
                    image_attachment = image.prepare_bedrock_image_attachment(
                        image_content
                    )
                    content.append(image_attachment)

                except Exception as e:
                    raise ValueError(
                        f"Failed to load example image from {image_path}: {e}"
                    )

        return content

    def process_document_section(self, document: Document, section_id: str) -> Document:
        """
        Process a single section from a Document object.

        Args:
            document: Document object containing section to process
            section_id: ID of the section to process

        Returns:
            Document: Updated Document object with extraction results for the section
        """
        # Validate input document
        if not document:
            logger.error("No document provided")
            return document

        if not document.sections:
            logger.error("Document has no sections to process")
            document.errors.append("Document has no sections to process")
            return document

        # Find the section with the given ID
        section = None
        for s in document.sections:
            if s.section_id == section_id:
                section = s
                break

        if not section:
            error_msg = f"Section {section_id} not found in document"
            logger.error(error_msg)
            document.errors.append(error_msg)
            return document

        # Extract information about the section
        class_label = section.classification
        output_bucket = document.output_bucket
        output_prefix = document.input_key
        output_key = f"{output_prefix}/sections/{section.section_id}/result.json"
        output_uri = f"s3://{output_bucket}/{output_key}"

        # Check if the section has required pages
        if not section.page_ids:
            error_msg = f"Section {section_id} has no page IDs"
            logger.error(error_msg)
            document.errors.append(error_msg)
            return document

        # Sort pages by page number
        sorted_page_ids = sorted(section.page_ids, key=int)
        start_page = int(sorted_page_ids[0])
        end_page = int(sorted_page_ids[-1])
        logger.info(
            f"Processing {len(sorted_page_ids)} pages, class {class_label}: {start_page}-{end_page}"
        )

        # Track metrics
        metrics.put_metric("InputDocuments", 1)
        metrics.put_metric("InputDocumentPages", len(section.page_ids))

        try:
            # Read document text from all pages in order
            t0 = time.time()
            document_texts = []
            for page_id in sorted_page_ids:
                if page_id not in document.pages:
                    error_msg = f"Page {page_id} not found in document"
                    logger.error(error_msg)
                    document.errors.append(error_msg)
                    continue

                page = document.pages[page_id]
                text_path = page.parsed_text_uri
                page_text = s3.get_text_content(text_path)
                document_texts.append(page_text)

            document_text = "\n".join(document_texts)
            t1 = time.time()
            logger.info(f"Time taken to read text content: {t1 - t0:.2f} seconds")

            # Read page images
            page_images = []
            for page_id in sorted_page_ids:
                if page_id not in document.pages:
                    continue

                page = document.pages[page_id]
                image_uri = page.image_uri
                image_content = image.prepare_image(image_uri)
                page_images.append(image_content)

            t2 = time.time()
            logger.info(f"Time taken to read images: {t2 - t1:.2f} seconds")

            # Get extraction configuration
            extraction_config = self.config.get("extraction", {})
            model_id = self.config.get("model_id") or extraction_config.get("model")
            temperature = float(extraction_config.get("temperature", 0))
            top_k = float(extraction_config.get("top_k", 5))
            top_p = float(extraction_config.get("top_p", 0.1))
            max_tokens = (
                int(extraction_config.get("max_tokens", 4096))
                if extraction_config.get("max_tokens")
                else None
            )
            system_prompt = extraction_config.get("system_prompt", "")

            # Get attributes for this document class
            attributes = self._get_class_attributes(class_label)
            attribute_descriptions = self._format_attribute_descriptions(attributes)

            # Prepare prompt
            prompt_template = extraction_config.get("task_prompt", "")

            if not prompt_template:
                # Default prompt if template not found
                task_prompt = f"""
                Extract the following fields from this {class_label} document:
                
                {attribute_descriptions}
                
                Document text:
                {document_text}
                
                Respond with a JSON object containing each field name and its extracted value.
                """
                content = [{"text": task_prompt}]
            else:
                # Check if task prompt contains FEW_SHOT_EXAMPLES placeholder
                if "{FEW_SHOT_EXAMPLES}" in prompt_template:
                    content = self._build_content_with_few_shot_examples(
                        prompt_template,
                        document_text,
                        class_label,
                        attribute_descriptions,
                    )
                else:
                    # Use the common format_prompt function from bedrock
                    from idp_common.bedrock import format_prompt

                    try:
                        task_prompt = format_prompt(
                            prompt_template,
                            {
                                "DOCUMENT_TEXT": document_text,
                                "DOCUMENT_CLASS": class_label,
                                "ATTRIBUTE_NAMES_AND_DESCRIPTIONS": attribute_descriptions,
                            },
                            required_placeholders=[
                                "DOCUMENT_TEXT",
                                "DOCUMENT_CLASS",
                                "ATTRIBUTE_NAMES_AND_DESCRIPTIONS",
                            ],
                        )
                        content = [{"text": task_prompt}]
                    except ValueError as e:
                        logger.warning(
                            f"Error formatting prompt template: {str(e)}. Using default prompt."
                        )
                        # Fall back to default prompt if template validation fails
                        task_prompt = f"""
                        Extract the following fields from this {class_label} document:
                        
                        {attribute_descriptions}
                        
                        Document text:
                        {document_text}
                        
                        Respond with a JSON object containing each field name and its extracted value.
                        """
                        content = [{"text": task_prompt}]

            # Add image attachments to the content (limit to 20 images as per Bedrock constraints)
            if page_images:
                logger.info(
                    f"Attaching images to prompt, for {len(page_images)} pages."
                )
                # Limit to 20 images as per Bedrock constraints
                for img in page_images[:20]:
                    content.append(image.prepare_bedrock_image_attachment(img))

            logger.info(
                f"Extracting fields for {class_label} document, section {section_id}"
            )

            # Time the model invocation
            request_start_time = time.time()

            # Invoke Bedrock with the common library
            response_with_metering = bedrock.invoke_model(
                model_id=model_id,
                system_prompt=system_prompt,
                content=content,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                max_tokens=max_tokens,
            )

            total_duration = time.time() - request_start_time
            logger.info(f"Time taken for extraction: {total_duration:.2f} seconds")

            # Extract text from response
            extracted_text = bedrock.extract_text_from_response(response_with_metering)
            metering = response_with_metering.get("metering", {})

            # Parse response into JSON
            extracted_fields = {}
            parsing_succeeded = True  # Flag to track if parsing was successful

            try:
                # Try to parse the extracted text as JSON
                extracted_fields = json.loads(self._extract_json(extracted_text))
            except Exception as e:
                # Handle parsing error
                logger.error(
                    f"Error parsing LLM output - invalid JSON?: {extracted_text} - {e}"
                )
                logger.info("Using unparsed LLM output.")
                extracted_fields = {"raw_output": extracted_text}
                parsing_succeeded = False  # Mark that parsing failed

            # Write to S3
            output = {
                "document_class": {"type": class_label},
                "inference_result": extracted_fields,
                "metadata": {
                    "parsing_succeeded": parsing_succeeded,
                    "extraction_time_seconds": total_duration,
                },
            }
            s3.write_content(
                output, output_bucket, output_key, content_type="application/json"
            )

            # Update the section with extraction result URI only (not the attributes themselves)
            section.extraction_result_uri = output_uri

            # Update document with metering data
            document.metering = utils.merge_metering_data(
                document.metering, metering or {}
            )

            t3 = time.time()
            logger.info(
                f"Total extraction time for section {section_id}: {t3 - t0:.2f} seconds"
            )

        except Exception as e:
            error_msg = f"Error processing section {section_id}: {str(e)}"
            logger.error(error_msg)
            document.errors.append(error_msg)

        return document

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON string from text response.

        Args:
            text: The text response from the model

        Returns:
            Extracted JSON string
        """
        # Check for code block format
        if "```json" in text:
            start_idx = text.find("```json") + len("```json")
            end_idx = text.find("```", start_idx)
            if end_idx > start_idx:
                return text[start_idx:end_idx].strip()
        elif "```" in text:
            start_idx = text.find("```") + len("```")
            end_idx = text.find("```", start_idx)
            if end_idx > start_idx:
                return text[start_idx:end_idx].strip()

        # Check for simple JSON
        if "{" in text and "}" in text:
            start_idx = text.find("{")
            # Find matching closing brace
            open_braces = 0
            for i in range(start_idx, len(text)):
                if text[i] == "{":
                    open_braces += 1
                elif text[i] == "}":
                    open_braces -= 1
                    if open_braces == 0:
                        return text[start_idx : i + 1].strip()

        # If we can't find JSON, return the text as-is
        return text
