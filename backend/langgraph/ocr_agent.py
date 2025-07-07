import asyncio
import base64
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
import io
from PIL import Image

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OCRAgentState(TypedDict):
    """State for the OCR LangGraph agent"""
    messages: List[Any]
    image_data: bytes
    extracted_text: str
    confidence_level: str
    context_info: str
    special_characters: List[str]
    processing_errors: List[str]
    metadata: Dict[str, Any]
    current_step: str
    retry_count: int
    max_retries: int


class LangGraphOCRAgent:
    """LangGraph agent for OCR text extraction using OpenAI Vision API"""
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🤖 Initializing LangGraph OCR Agent...")
        
        # Initialize LangChain OpenAI model
        self.vision_llm = init_chat_model(
            "openai:gpt-4-vision-preview",
            temperature=0.2,
            max_tokens=2000,
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize OpenAI client for direct API calls
        self.openai_client = AsyncOpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Build the graph
        self.graph = self._build_graph()
        self.logger.info("✅ LangGraph OCR Agent initialized successfully")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow with simple dict state
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("preprocess_image", self._preprocess_image)
        workflow.add_node("extract_text_vision", self._extract_text_with_vision)
        workflow.add_node("process_response", self._process_vision_response)
        workflow.add_node("validate_extraction", self._validate_extraction)
        workflow.add_node("enhance_text", self._enhance_extracted_text)
        workflow.add_node("finalize_results", self._finalize_results)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define the flow
        workflow.set_entry_point("validate_input")
        
        # Add edges
        workflow.add_edge("validate_input", "preprocess_image")
        workflow.add_edge("preprocess_image", "extract_text_vision")
        workflow.add_edge("extract_text_vision", "process_response")
        workflow.add_edge("process_response", "validate_extraction")
        
        # Conditional edges for validation
        workflow.add_conditional_edges(
            "validate_extraction",
            self._should_enhance_text,
            {
                "enhance": "enhance_text",
                "finalize": "finalize_results",
                "retry": "extract_text_vision",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("enhance_text", "finalize_results")
        workflow.add_edge("finalize_results", END)
        workflow.add_edge("handle_error", END)
        
        # Compile without checkpointer
        return workflow.compile()
    
    async def _validate_input(self, state: dict) -> dict:
        """Validate input data"""
        self.logger.info("🔍 Validating input data...")
        
        state["current_step"] = "validate_input"
        state["processing_errors"] = state.get("processing_errors", [])
        
        # Check if image data exists
        if not state.get("image_data"):
            error_msg = "No image data provided"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
            return state
        
        # Validate image format
        try:
            image = Image.open(io.BytesIO(state["image_data"]))
            state["metadata"] = state.get("metadata", {})
            state["metadata"]["image_format"] = image.format
            state["metadata"]["image_size"] = image.size
            state["metadata"]["image_mode"] = image.mode
            
            self.logger.info(f"✅ Image validated: {image.format} {image.size} {image.mode}")
            
        except Exception as e:
            error_msg = f"Invalid image format: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    async def _preprocess_image(self, state: dict) -> dict:
        """Preprocess image for optimal OCR"""
        self.logger.info("🔧 Preprocessing image...")
        
        state["current_step"] = "preprocess_image"
        
        try:
            # Convert image to optimal format for OCR
            image = Image.open(io.BytesIO(state["image_data"]))
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large (max 2048x2048 for OpenAI Vision)
            max_size = 2048
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                self.logger.info(f"📏 Image resized to {image.size}")
            
            # Convert back to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=95)
            state["image_data"] = img_byte_arr.getvalue()
            
            # Update metadata
            state["metadata"]["processed_size"] = image.size
            state["metadata"]["processed_format"] = "JPEG"
            
            self.logger.info("✅ Image preprocessing completed")
            
        except Exception as e:
            error_msg = f"Image preprocessing failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    async def _extract_text_with_vision(self, state: dict) -> dict:
        """Extract text using OpenAI Vision API"""
        self.logger.info("👁️ Extracting text with OpenAI Vision...")
        
        state["current_step"] = "extract_text_vision"
        
        try:
            # Convert image to base64
            base64_image = base64.b64encode(state["image_data"]).decode('utf-8')
            
            # Create specialized prompt for medical/assessment documents
            prompt = self._create_extraction_prompt(state)
            
            # Prepare messages for OpenAI Vision
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # Call OpenAI Vision API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                max_tokens=2000,
                temperature=0.1
            )
            
            # Store the raw response
            raw_content = response.choices[0].message.content
            state["raw_response"] = raw_content
            
            # Debug logging
            self.logger.info(f"✅ OpenAI Vision extraction completed")
            self.logger.info(f"📝 Raw response length: {len(raw_content) if raw_content else 0} characters")
            if raw_content:
                preview = raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
                self.logger.info(f"👁️ Response preview: {preview}")
            else:
                self.logger.warning("⚠️ OpenAI returned empty response")
            
        except Exception as e:
            error_msg = f"OpenAI Vision extraction failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    def _create_extraction_prompt(self, state: dict) -> str:
        """Create specialized prompt for medical/assessment documents"""
        
        # Get context information
        document_type = state.get("metadata", {}).get("document_type", "medical_assessment")
        page_number = state.get("metadata", {}).get("page_number", 1)
        
        base_prompt = """
        You are a specialized OCR assistant for medical and developmental assessment documents.
        
        Please extract ALL text from this image with the following requirements:
        
        1. ACCURACY: Preserve exact text, including:
           - All numbers (scores, percentiles, age equivalents)
           - All medical/assessment terminology
           - All formatting (tables, lists, sections)
           - All special characters and symbols
        
        2. STRUCTURE: Maintain the document structure:
           - Preserve headings and subheadings
           - Keep tables in table format
           - Maintain bullet points and lists
           - Preserve spacing and alignment where meaningful
        
        3. CLINICAL FOCUS: Pay special attention to:
           - Test scores and percentiles
           - Age equivalents and developmental milestones
           - Clinical observations and recommendations
           - Assessment names and dates
           - Child demographics and information
        
        4. COMPLETENESS: Include everything visible, even if:
           - Text is small or faint
           - Text is partially obscured
           - Text appears to be headers/footers
           - Text is in tables or forms
        
        5. QUALITY INDICATORS: After extraction, provide:
           - Confidence level (high/medium/low)
           - Any unclear or uncertain text marked with [?]
           - Note any areas that might need human review
        
        Return the extracted text in a clear, readable format that preserves the original document structure.
        """
        
        if document_type == "medical_assessment":
            base_prompt += """
            
            MEDICAL ASSESSMENT SPECIFIC INSTRUCTIONS:
            - Look for standardized test scores (Bayley-4, SP-2, etc.)
            - Extract percentile ranks and standard scores
            - Capture age equivalents and developmental levels
            - Include all clinical observations and recommendations
            - Preserve any diagnostic codes or classifications
            """
        
        return base_prompt
    
    async def _process_vision_response(self, state: dict) -> dict:
        """Process the vision API response"""
        self.logger.info("🔧 Processing vision response...")
        
        state["current_step"] = "process_response"
        
        try:
            raw_response = state.get("raw_response", "")
            
            if not raw_response or not raw_response.strip():
                error_msg = "No response from Vision API"
                state["processing_errors"].append(error_msg)
                self.logger.error(f"❌ {error_msg}")
                return state
            
            # Parse the response
            parsed_data = self._parse_text_response(raw_response)
            
            # Update state with parsed data
            state["extracted_text"] = parsed_data.get("text", "")
            state["confidence_level"] = parsed_data.get("confidence", "medium")
            state["context_info"] = parsed_data.get("context", "")
            state["special_characters"] = parsed_data.get("special_chars", [])
            
            # Add processing metadata
            state["metadata"]["text_length"] = len(state["extracted_text"])
            state["metadata"]["processing_time"] = datetime.now().isoformat()
            
            self.logger.info(f"✅ Response processed: {len(state['extracted_text'])} characters extracted")
            
        except Exception as e:
            error_msg = f"Response processing failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    def _parse_text_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse the raw vision response into structured data"""
        
        # Initialize result
        result = {
            "text": "",
            "confidence": "medium",
            "context": "",
            "special_chars": [],
            "quality_score": 0.7
        }
        
        try:
            # The response should be the extracted text
            # Look for confidence indicators in the response
            lines = raw_response.split('\n')
            
            text_lines = []
            confidence_indicators = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for confidence indicators
                if any(indicator in line.lower() for indicator in ['confidence:', 'quality:', 'unclear:', 'uncertain:']):
                    confidence_indicators.append(line)
                elif line.startswith('[') and line.endswith(']'):
                    # Metadata or confidence info
                    confidence_indicators.append(line)
                else:
                    # Actual text content
                    text_lines.append(line)
            
            # Join text lines
            result["text"] = '\n'.join(text_lines)
            
            # Determine confidence based on indicators
            if any('high' in indicator.lower() for indicator in confidence_indicators):
                result["confidence"] = "high"
                result["quality_score"] = 0.9
            elif any('low' in indicator.lower() for indicator in confidence_indicators):
                result["confidence"] = "low"
                result["quality_score"] = 0.5
            elif any('[?]' in raw_response or 'unclear' in raw_response.lower()):
                result["confidence"] = "medium"
                result["quality_score"] = 0.6
            else:
                result["confidence"] = "medium"
                result["quality_score"] = 0.7
            
            # Extract context information
            result["context"] = '; '.join(confidence_indicators)
            
            # Look for special characters
            special_chars = set()
            for char in result["text"]:
                if not char.isalnum() and not char.isspace() and char not in '.,;:!?-()[]{}':
                    special_chars.add(char)
            
            result["special_chars"] = list(special_chars)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error parsing response: {e}")
            result["text"] = raw_response  # Fallback to raw response
        
        return result
    
    async def _validate_extraction(self, state: dict) -> dict:
        """Validate the extracted text"""
        self.logger.info("✅ Validating extraction...")
        
        state["current_step"] = "validate_extraction"
        
        extracted_text = state.get("extracted_text", "")
        
        # Basic validation checks
        validation_results = {
            "has_text": bool(extracted_text and extracted_text.strip()),
            "min_length": len(extracted_text) >= 10,
            "has_numbers": any(char.isdigit() for char in extracted_text),
            "has_medical_terms": any(term in extracted_text.lower() for term in [
                'score', 'percentile', 'assessment', 'test', 'age', 'development',
                'cognitive', 'language', 'motor', 'social', 'emotional', 'adaptive'
            ]),
            "structure_preserved": '\n' in extracted_text or '\t' in extracted_text
        }
        
        # Calculate validation score
        validation_score = sum(validation_results.values()) / len(validation_results)
        
        state["metadata"]["validation_score"] = validation_score
        state["metadata"]["validation_results"] = validation_results
        
        # Determine if extraction is acceptable
        if validation_score >= 0.6:
            state["validation_passed"] = True
            self.logger.info(f"✅ Validation passed: {validation_score:.2f}")
        else:
            state["validation_passed"] = False
            self.logger.warning(f"⚠️ Validation failed: {validation_score:.2f}")
        
        return state
    
    def _should_enhance_text(self, state: dict) -> str:
        """Determine next step based on validation results"""
        
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        validation_passed = state.get("validation_passed", False)
        validation_score = state.get("metadata", {}).get("validation_score", 0)
        
        # Log current state for debugging
        self.logger.info(f"🔍 Decision point - retry_count: {retry_count}, max_retries: {max_retries}")
        self.logger.info(f"🔍 Validation passed: {validation_passed}, score: {validation_score}")
        self.logger.info(f"🔍 Processing errors: {len(state.get('processing_errors', []))}")
        
        # Check for errors first
        if state.get("processing_errors"):
            if retry_count < max_retries:
                # Increment retry count before retrying
                state["retry_count"] = retry_count + 1
                self.logger.info(f"🔄 Retrying (attempt {state['retry_count']}/{max_retries})")
                return "retry"
            else:
                self.logger.info("❌ Max retries reached, going to error handling")
                return "error"
        
        # If validation passed and score is good
        if validation_passed and validation_score >= 0.8:
            self.logger.info("✅ High quality extraction, finalizing")
            return "finalize"
        
        # If validation passed but score is medium, enhance
        if validation_passed and validation_score >= 0.6:
            self.logger.info("🔧 Medium quality extraction, enhancing")
            return "enhance"
        
        # If validation failed, retry or error
        if retry_count < max_retries:
            # Increment retry count before retrying
            state["retry_count"] = retry_count + 1
            self.logger.info(f"🔄 Validation failed, retrying (attempt {state['retry_count']}/{max_retries})")
            return "retry"
        
        self.logger.info("❌ Validation failed and max retries reached, going to error handling")
        return "error"
    
    async def _enhance_extracted_text(self, state: dict) -> dict:
        """Enhance extracted text using additional processing"""
        self.logger.info("🔧 Enhancing extracted text...")
        
        state["current_step"] = "enhance_text"
        
        try:
            extracted_text = state.get("extracted_text", "")
            
            if not extracted_text:
                return state
            
            # Basic text enhancement
            enhanced_text = self._apply_text_enhancements(extracted_text)
            
            # Update state
            state["extracted_text"] = enhanced_text
            state["metadata"]["enhanced"] = True
            state["metadata"]["enhancement_applied"] = datetime.now().isoformat()
            
            self.logger.info("✅ Text enhancement completed")
            
        except Exception as e:
            error_msg = f"Text enhancement failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    def _apply_text_enhancements(self, text: str) -> str:
        """Apply various text enhancements"""
        
        # Basic cleanup
        enhanced = text.strip()
        
        # Fix common OCR errors
        replacements = {
            'O': '0',  # O instead of 0 in numbers
            'l': '1',  # l instead of 1 in numbers
            'S': '5',  # S instead of 5 in numbers
        }
        
        # Apply replacements in numeric contexts
        import re
        for old, new in replacements.items():
            # Replace in numeric contexts
            enhanced = re.sub(f'\\b{old}(?=\\d)', new, enhanced)
            enhanced = re.sub(f'(?<=\\d){old}\\b', new, enhanced)
        
        # Normalize whitespace
        enhanced = re.sub(r'\s+', ' ', enhanced)
        enhanced = re.sub(r'\n\s*\n', '\n\n', enhanced)
        
        return enhanced
    
    async def _finalize_results(self, state: dict) -> dict:
        """Finalize the OCR results"""
        self.logger.info("✅ Finalizing results...")
        
        state["current_step"] = "finalize_results"
        
        # Create final result summary
        final_result = {
            "extracted_text": state.get("extracted_text", ""),
            "confidence_level": state.get("confidence_level", "medium"),
            "context_info": state.get("context_info", ""),
            "metadata": state.get("metadata", {}),
            "quality_score": state.get("metadata", {}).get("validation_score", 0.7),
            "enhanced": state.get("metadata", {}).get("enhanced", False),
            "processing_errors": state.get("processing_errors", []),
            "processing_complete": True,
            "completed_at": datetime.now().isoformat()
        }
        
        state["final_result"] = final_result
        
        self.logger.info(f"🎉 OCR processing completed successfully")
        self.logger.info(f"   📝 {len(final_result['extracted_text'])} characters extracted")
        self.logger.info(f"   📊 Quality score: {final_result['quality_score']:.2f}")
        self.logger.info(f"   🔧 Enhanced: {final_result['enhanced']}")
        
        return state
    
    async def _handle_error(self, state: dict) -> dict:
        """Handle processing errors"""
        self.logger.info("❌ Handling processing errors...")
        
        state["current_step"] = "handle_error"
        
        errors = state.get("processing_errors", [])
        
        # Create error result
        error_result = {
            "extracted_text": state.get("extracted_text", ""),
            "confidence_level": "low",
            "context_info": "Processing failed with errors",
            "metadata": state.get("metadata", {}),
            "quality_score": 0.0,
            "enhanced": False,
            "processing_errors": errors,
            "processing_complete": False,
            "completed_at": datetime.now().isoformat(),
            "error_summary": f"Processing failed after {state.get('retry_count', 0)} retries"
        }
        
        state["final_result"] = error_result
        
        self.logger.error(f"❌ OCR processing failed: {len(errors)} errors")
        for error in errors:
            self.logger.error(f"   - {error}")
        
        return state
    
    async def process_image(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """
        Process an image and extract text using the LangGraph workflow
        
        Args:
            image_data: Image bytes
            **kwargs: Additional metadata (document_type, page_number, etc.)
        
        Returns:
            Dict containing extracted text and metadata
        """
        self.logger.info("🚀 Starting OCR processing...")
        
        # Initialize state
        initial_state = {
            "messages": [],
            "image_data": image_data,
            "extracted_text": "",
            "confidence_level": "medium",
            "context_info": "",
            "special_characters": [],
            "processing_errors": [],
            "metadata": kwargs,
            "current_step": "init",
            "retry_count": 0,
            "max_retries": 2
        }
        
        try:
            # Run the workflow without config (no checkpointer)
            final_state = await self.graph.ainvoke(initial_state)
            
            # Return the final result
            return final_state.get("final_result", {})
            
        except Exception as e:
            self.logger.error(f"❌ OCR workflow failed: {e}")
            return {
                "extracted_text": "",
                "confidence_level": "low",
                "context_info": "Workflow execution failed",
                "metadata": kwargs,
                "quality_score": 0.0,
                "enhanced": False,
                "processing_errors": [str(e)],
                "processing_complete": False,
                "completed_at": datetime.now().isoformat()
            }


# Export the agent
__all__ = ["LangGraphOCRAgent"] 