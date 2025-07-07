import asyncio
import base64
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from openai import AsyncOpenAI
import io
from PIL import Image

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
sys.path.append(PROJECT_DIR.__str__())

from backend.common.logging import logging

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
        # self.vision_llm = ChatOpenAI(
        #     model=model,
        #     temperature=0.1,
        #     max_tokens=2000,
        #     api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        # )
        self.vision_llm = init_chat_model(
            "openai:gpt-4-vision-preview",
            temperature=0.2,
            max_tokens=2000,
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Build the graph
        self.graph = self._build_graph()
        self.logger.info("✅ LangGraph OCR Agent initialized successfully")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow
        workflow = StateGraph(OCRAgentState)
        
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
        
        return workflow.compile()
    
    async def _validate_input(self, state: OCRAgentState) -> OCRAgentState:
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
    
    async def _preprocess_image(self, state: OCRAgentState) -> OCRAgentState:
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
    
    async def _extract_text_with_vision(self, state: OCRAgentState) -> OCRAgentState:
        """Extract text using OpenAI Vision API"""
        self.logger.info("👁️ Extracting text with OpenAI Vision...")
        
        state["current_step"] = "extract_text_vision"
        state["retry_count"] = state.get("retry_count", 0)
        
        try:
            # Convert image to base64
            base64_image = base64.b64encode(state["image_data"]).decode('utf-8')
            
            # Create specialized prompt for medical/assessment documents
            prompt = self._create_extraction_prompt(state)
            
            # Prepare messages for GPT-4 Vision
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
                                "detail": "high"  # Use high detail for document processing
                            }
                        }
                    ]
                }
            ]
            
            # Call OpenAI Vision API
            response = await self.vision_llm.ainvoke(messages)
            
            # Store the raw response
            state["metadata"]["raw_vision_response"] = response.content
            state["metadata"]["model_used"] = self.vision_llm.model_name
            
            self.logger.info(f"✅ Vision API response received ({state['metadata']['model_used']})")
            
        except Exception as e:
            error_msg = f"Vision API extraction failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            state["retry_count"] += 1
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    def _create_extraction_prompt(self, state: OCRAgentState) -> str:
        """Create specialized prompt for text extraction"""
        
        base_prompt = """You are an expert OCR specialist analyzing a medical/assessment document image. 
        Please extract all text content with high accuracy and provide structured information.

        Extract and format the response as a JSON object with the following structure:
        {
            "main_text": "All extracted text content",
            "context": "Description of document type and layout",
            "confidence": "high/medium/low",
            "special_characters": ["list", "of", "special", "symbols"],
            "tables": "Any table data found",
            "headers": "Any headers or titles",
            "scores": "Any numerical scores or measurements",
            "patient_info": "Any patient demographic information"
        }

        Pay special attention to:
        - Medical terminology and abbreviations
        - Numerical scores and measurements
        - Patient demographic information
        - Table structures and data relationships
        - Any handwritten notes or annotations
        - Assessment names and test results

        Ensure high accuracy for all numerical values and medical terms."""
        
        # Add context-specific instructions based on metadata
        if state.get("metadata", {}).get("document_type"):
            doc_type = state["metadata"]["document_type"]
            base_prompt += f"\n\nThis appears to be a {doc_type} document. Focus on extracting relevant {doc_type} data."
        
        return base_prompt
    
    async def _process_vision_response(self, state: OCRAgentState) -> OCRAgentState:
        """Process and structure the Vision API response"""
        self.logger.info("🔄 Processing Vision API response...")
        
        state["current_step"] = "process_response"
        
        try:
            raw_response = state["metadata"].get("raw_vision_response", "")
            
            if not raw_response:
                error_msg = "No response from Vision API"
                state["processing_errors"].append(error_msg)
                return state
            
            # Try to parse as JSON first
            try:
                parsed_response = json.loads(raw_response)
                state["extracted_text"] = parsed_response.get("main_text", "")
                state["confidence_level"] = parsed_response.get("confidence", "medium")
                state["context_info"] = parsed_response.get("context", "")
                state["special_characters"] = parsed_response.get("special_characters", [])
                state["metadata"]["structured_data"] = parsed_response
                
            except json.JSONDecodeError:
                # If not JSON, parse using text patterns
                structured_data = self._parse_text_response(raw_response)
                state["extracted_text"] = structured_data["main_text"]
                state["confidence_level"] = structured_data["confidence"]
                state["context_info"] = structured_data["context"]
                state["special_characters"] = structured_data["special_characters"]
                state["metadata"]["structured_data"] = structured_data
            
            self.logger.info(f"✅ Response processed - {len(state['extracted_text'])} characters extracted")
            
        except Exception as e:
            error_msg = f"Response processing failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    def _parse_text_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        
        # Extract sections using pattern matching
        sections = {
            "main_text": "",
            "context": "",
            "confidence": "medium",
            "special_characters": [],
            "tables": "",
            "headers": "",
            "scores": "",
            "patient_info": ""
        }
        
        # Simple pattern matching for common structures
        lines = raw_response.split('\n')
        current_section = "main_text"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if any(keyword in line.lower() for keyword in ["confidence:", "context:", "special characters:"]):
                if "confidence:" in line.lower():
                    current_section = "confidence"
                    sections["confidence"] = line.split(":")[-1].strip()
                elif "context:" in line.lower():
                    current_section = "context"
                    sections["context"] = line.split(":")[-1].strip()
                elif "special characters:" in line.lower():
                    current_section = "special_characters"
                continue
            
            # Add content to appropriate section
            if current_section == "main_text":
                sections["main_text"] += line + " "
            elif current_section == "context":
                sections["context"] += line + " "
        
        # Clean up
        sections["main_text"] = sections["main_text"].strip()
        sections["context"] = sections["context"].strip()
        
        return sections
    
    async def _validate_extraction(self, state: OCRAgentState) -> OCRAgentState:
        """Validate the quality of text extraction"""
        self.logger.info("✅ Validating extraction quality...")
        
        state["current_step"] = "validate_extraction"
        
        # Check extraction quality
        extracted_text = state.get("extracted_text", "")
        confidence = state.get("confidence_level", "medium")
        
        # Basic quality checks
        quality_score = 0
        quality_issues = []
        
        # Check text length
        if len(extracted_text) < 50:
            quality_issues.append("Text too short")
        else:
            quality_score += 1
        
        # Check for medical/assessment content
        medical_keywords = ["score", "assessment", "test", "patient", "age", "percentile", "scaled"]
        if any(keyword in extracted_text.lower() for keyword in medical_keywords):
            quality_score += 1
        else:
            quality_issues.append("No medical/assessment terms found")
        
        # Check confidence level
        if confidence in ["high", "medium"]:
            quality_score += 1
        else:
            quality_issues.append("Low confidence reported")
        
        # Check for numbers (scores)
        import re
        numbers = re.findall(r'\d+', extracted_text)
        if len(numbers) > 0:
            quality_score += 1
        else:
            quality_issues.append("No numerical values found")
        
        # Store validation results
        state["metadata"]["quality_score"] = quality_score
        state["metadata"]["quality_issues"] = quality_issues
        state["metadata"]["validation_passed"] = quality_score >= 3
        
        self.logger.info(f"📊 Quality score: {quality_score}/4")
        if quality_issues:
            self.logger.warning(f"⚠️ Quality issues: {', '.join(quality_issues)}")
        
        return state
    
    def _should_enhance_text(self, state: OCRAgentState) -> str:
        """Determine next step based on validation results"""
        
        # Check for critical errors
        if state.get("processing_errors") and state.get("retry_count", 0) >= state.get("max_retries", 3):
            return "error"
        
        # Check if we should retry
        if state.get("processing_errors") and state.get("retry_count", 0) < state.get("max_retries", 3):
            return "retry"
        
        # Check validation results
        validation_passed = state.get("metadata", {}).get("validation_passed", False)
        quality_score = state.get("metadata", {}).get("quality_score", 0)
        
        # If quality is poor and we have retries left, try again
        if quality_score < 2 and state.get("retry_count", 0) < state.get("max_retries", 3):
            return "retry"
        
        # If validation passed but quality could be improved, enhance
        if validation_passed and quality_score < 4:
            return "enhance"
        
        # Otherwise, finalize
        return "finalize"
    
    async def _enhance_extracted_text(self, state: OCRAgentState) -> OCRAgentState:
        """Enhance extracted text using LLM"""
        self.logger.info("🔧 Enhancing extracted text...")
        
        state["current_step"] = "enhance_text"
        
        try:
            extracted_text = state.get("extracted_text", "")
            
            if not extracted_text:
                return state
            
            # Create enhancement prompt
            enhancement_prompt = f"""
            Please review and enhance the following extracted text from a medical/assessment document.
            Fix any obvious OCR errors, improve formatting, and structure the content clearly.
            
            Original extracted text:
            {extracted_text}
            
            Please provide:
            1. Cleaned and corrected text
            2. Identified any medical terms or scores
            3. Structured format if possible
            
            Return the enhanced version maintaining all original information.
            """
            
            # Use LLM to enhance text
            messages = [
                SystemMessage(content="You are an expert at cleaning and enhancing OCR text from medical documents."),
                HumanMessage(content=enhancement_prompt)
            ]
            
            response = await self.vision_llm.ainvoke(messages)
            
            # Store enhanced text
            state["metadata"]["original_text"] = extracted_text
            state["extracted_text"] = response.content
            state["metadata"]["enhanced"] = True
            
            self.logger.info("✅ Text enhancement completed")
            
        except Exception as e:
            error_msg = f"Text enhancement failed: {str(e)}"
            state["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    async def _finalize_results(self, state: OCRAgentState) -> OCRAgentState:
        """Finalize and prepare results"""
        self.logger.info("🎯 Finalizing results...")
        
        state["current_step"] = "finalize_results"
        
        # Prepare final results
        final_results = {
            "extracted_text": state.get("extracted_text", ""),
            "confidence_level": state.get("confidence_level", "medium"),
            "context_info": state.get("context_info", ""),
            "special_characters": state.get("special_characters", []),
            "processing_metadata": state.get("metadata", {}),
            "quality_score": state.get("metadata", {}).get("quality_score", 0),
            "enhanced": state.get("metadata", {}).get("enhanced", False),
            "processing_errors": state.get("processing_errors", []),
            "timestamp": datetime.now().isoformat()
        }
        
        state["metadata"]["final_results"] = final_results
        
        # Log summary
        text_length = len(state.get("extracted_text", ""))
        self.logger.info(f"🎉 OCR processing completed:")
        self.logger.info(f"   📝 Text length: {text_length} characters")
        self.logger.info(f"   📊 Quality score: {final_results['quality_score']}/4")
        self.logger.info(f"   🔧 Enhanced: {final_results['enhanced']}")
        self.logger.info(f"   ⚠️ Errors: {len(final_results['processing_errors'])}")
        
        return state
    
    async def _handle_error(self, state: OCRAgentState) -> OCRAgentState:
        """Handle processing errors"""
        self.logger.error("❌ Handling processing errors...")
        
        state["current_step"] = "error_handling"
        
        errors = state.get("processing_errors", [])
        
        # Log all errors
        for error in errors:
            self.logger.error(f"   ❌ {error}")
        
        # Create error summary
        error_summary = {
            "success": False,
            "errors": errors,
            "retry_count": state.get("retry_count", 0),
            "max_retries": state.get("max_retries", 3),
            "timestamp": datetime.now().isoformat()
        }
        
        state["metadata"]["error_summary"] = error_summary
        
        return state
    
    async def process_image(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """Main method using LangGraph invoke"""
        self.logger.info("🚀 Starting OCR processing with LangGraph...")
        
        # Initialize state
        initial_state = OCRAgentState(
            messages=[],
            image_data=image_data,
            extracted_text="",
            confidence_level="medium",
            context_info="",
            special_characters=[],
            processing_errors=[],
            metadata=kwargs,
            current_step="init",
            retry_count=0,
            max_retries=kwargs.get("max_retries", 3)
        )
        
        # Run the graph using invoke (not direct API calls)
        final_state = await self.graph.ainvoke(initial_state)
        
        return final_state["metadata"]["final_results"]


async def main():
    """Test the OCR agent"""
    # Initialize agent
    agent = LangGraphOCRAgent()
    
    # Test with sample image
    sample_image_path = os.path.join(PROJECT_DIR, "assets", "sample_assessment.png")
    
    if os.path.exists(sample_image_path):
        with open(sample_image_path, 'rb') as f:
            image_data = f.read()
        
        # Process image
        results = await agent.process_image(
            image_data=image_data,
            document_type="assessment",
            expected_content="scores and patient info"
        )
        
        print("OCR Results:")
        print(f"Success: {results.get('success', True)}")
        print(f"Text length: {len(results.get('extracted_text', ''))}")
        print(f"Quality score: {results.get('quality_score', 0)}")
        print(f"Enhanced: {results.get('enhanced', False)}")
        print(f"Errors: {len(results.get('processing_errors', []))}")
        
        if results.get('extracted_text'):
            print(f"\nExtracted text preview:\n{results['extracted_text'][:200]}...")
    
    else:
        print("Sample image not found. Please provide a test image.")


if __name__ == "__main__":
    asyncio.run(main()) 