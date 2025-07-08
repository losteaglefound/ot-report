import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class OCRState(TypedDict):
    """Simple state for OCR processing"""
    image_path: str
    extracted_text: str
    error: Optional[str]


class SimpleOCRAgent:
    """Simple OCR agent that takes image path and returns extracted text"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🤖 Initializing Simple OCR Agent...")
        
        # Initialize LangChain model
        self.llm = init_chat_model(
            "openai:gpt-4-turbo-2024-04-09",
            temperature=0.1,
            max_tokens=2000,
            api_key=openai_api_key
        )
        
        # Build the graph
        self.graph = self._build_graph()
        self.logger.info("✅ Simple OCR Agent initialized successfully")
    
    def _build_graph(self) -> StateGraph:
        """Build the simple LangGraph workflow"""
        
        # Define the workflow
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("extract_text", self._extract_text)
        
        # Define the flow
        workflow.set_entry_point("extract_text")
        workflow.add_edge("extract_text", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def _extract_text(self, state: dict) -> dict:
        """Extract text from image using Vision API"""
        self.logger.info("👁️ Extracting text from image...")
        
        try:
            image_path = state["image_path"]
            
            # Check if file exists
            if not Path(image_path).exists():
                state["error"] = f"Image file not found: {image_path}"
                state["extracted_text"] = ""
                return state
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Create message with image
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "Extract all text from this image. Return only the extracted text without any additional commentary or formatting."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            )
            
            # Get response from model
            response = await self.llm.ainvoke([message])
            
            # Extract text from response
            extracted_text = response.content if hasattr(response, 'content') else str(response)
            
            state["extracted_text"] = extracted_text
            state["error"] = None
            
            self.logger.info(f"✅ Text extracted successfully: {len(extracted_text)} characters")
            
        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            state["error"] = error_msg
            state["extracted_text"] = ""
            self.logger.error(f"❌ {error_msg}")
        
        return state
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from an image file
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dict containing extracted text and any error information
        """
        self.logger.info(f"🚀 Starting text extraction from: {image_path}")
        
        # Initialize state
        initial_state = {
            "image_path": image_path,
            "extracted_text": "",
            "error": None
        }
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "extracted_text": final_state.get("extracted_text", ""),
                "error": final_state.get("error"),
                "success": final_state.get("error") is None
            }
            
        except Exception as e:
            self.logger.error(f"❌ OCR workflow failed: {e}")
            return {
                "extracted_text": "",
                "error": str(e),
                "success": False
            }


# Export the agent
__all__ = ["SimpleOCRAgent"] 