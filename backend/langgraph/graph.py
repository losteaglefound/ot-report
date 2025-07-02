"""
ChatBot class for langraph integration.
This module provides a ChatBot class that wraps the langraph functionality.
"""

from typing import Dict, Any, Optional
from . import graph_invoke


class ChatBot:
    """
    A ChatBot class that provides a simple interface to the langraph agent.
    """
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the ChatBot.
        
        Args:
            system_prompt: Optional system prompt override (not used in current implementation)
        """
        self.system_prompt = system_prompt
        self.conversation_history = []
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke the langraph agent with a prompt.
        
        Args:
            prompt: The user prompt
            **kwargs: Additional arguments (currently unused)
            
        Returns:
            str: The AI response
        """
        try:
            response = graph_invoke(prompt)
            
            # Store conversation history
            self.conversation_history.append({
                "role": "user",
                "content": prompt
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
            return response
        except Exception as e:
            error_message = f"Error in ChatBot.invoke: {e}"
            print(error_message)
            return error_message
    
    def chat(self, message: str) -> str:
        """
        Alias for invoke method to provide a more intuitive interface.
        
        Args:
            message: The user message
            
        Returns:
            str: The AI response
        """
        return self.invoke(message)
    
    def get_conversation_history(self) -> list:
        """
        Get the conversation history.
        
        Returns:
            list: List of conversation turns
        """
        return self.conversation_history.copy()
    
    def clear_history(self):
        """
        Clear the conversation history.
        """
        self.conversation_history.clear()
    
    def set_system_prompt(self, system_prompt: str):
        """
        Set a new system prompt (placeholder for future implementation).
        
        Args:
            system_prompt: The new system prompt
        """
        self.system_prompt = system_prompt
        print(f"System prompt set (note: current implementation uses fixed system prompt)")


# Convenience function for backward compatibility
def create_chatbot(system_prompt: Optional[str] = None) -> ChatBot:
    """
    Create a ChatBot instance.
    
    Args:
        system_prompt: Optional system prompt
        
    Returns:
        ChatBot: A new ChatBot instance
    """
    return ChatBot(system_prompt=system_prompt) 