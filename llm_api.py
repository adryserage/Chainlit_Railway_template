import os
from typing import List, Dict, AsyncGenerator, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from openai import AsyncOpenAI
import google.generativeai as genai
from anthropic import AsyncAnthropic

# Load environment variables
_ = load_dotenv('.env')

class ModelProvider(Enum):
    """Supported model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

@dataclass
class StreamResponse:
    """Unified response format for all providers"""
    choices: List[Dict]
    
    @classmethod
    def create(cls, content: Optional[str] = None):
        return cls(choices=[{"delta": {"content": content}}])

class LLMConfig:
    """Configuration for LLM models"""
    def __init__(self):
        self.model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '2000'))
        self._detect_provider()
    
    def _detect_provider(self) -> None:
        """Detect the model provider based on model name"""
        if self.model.startswith(('gpt-', 'text-davinci-')):
            self.provider = ModelProvider.OPENAI
        elif self.model.startswith(('claude-', 'claude-2', 'claude-3')):
            self.provider = ModelProvider.ANTHROPIC
        elif self.model.startswith('gemini'):
            self.provider = ModelProvider.GEMINI
        else:
            self.provider = ModelProvider.OPENAI  # Default to OpenAI
    
    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

class LLMClient:
    """Unified client for different LLM providers"""
    def __init__(self):
        self.config = LLMConfig()
        self._init_client()
    
    def _init_client(self) -> None:
        """Initialize the appropriate client based on provider"""
        if self.config.provider == ModelProvider.OPENAI:
            self.client = AsyncOpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                organization=os.getenv('OPENAI_ORGANIZATION')
            )
        elif self.config.provider == ModelProvider.ANTHROPIC:
            self.client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        elif self.config.provider == ModelProvider.GEMINI:
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.client = genai.GenerativeModel(
                model_name=self.config.model,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens
                )
            )
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Format messages according to provider requirements"""
        if self.config.provider == ModelProvider.ANTHROPIC:
            system_message = next((msg['content'] for msg in messages if msg['role'] == 'system'), None)
            conversation = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    continue
                content = msg['content']
                if msg['role'] == 'user' and system_message and not conversation:
                    content = f"{system_message}\n\nUser: {content}"
                conversation.append({"role": "user" if msg['role'] == 'user' else "assistant", "content": content})
            return conversation
            
        elif self.config.provider == ModelProvider.GEMINI:
            return [{
                'role': 'user' if msg['role'] == 'user' else 'model',
                'parts': [msg['content']]
            } for msg in messages if msg['role'] != 'system']
            
        return messages  # OpenAI format is our default format

    async def generate_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[StreamResponse, None]:
        """Generate streaming response from the selected model"""
        formatted_messages = self._format_messages(messages)
        
        if self.config.provider == ModelProvider.OPENAI:
            stream = await self.client.chat.completions.create(
                messages=formatted_messages,
                stream=True,
                **self.config.to_dict()
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield StreamResponse.create(chunk.choices[0].delta.content)
                
        elif self.config.provider == ModelProvider.ANTHROPIC:
            stream = await self.client.messages.create(
                messages=formatted_messages,
                stream=True,
                **self.config.to_dict()
            )
            async for chunk in stream:
                if chunk.type == 'content_block_delta':
                    yield StreamResponse.create(chunk.text)
                    
        elif self.config.provider == ModelProvider.GEMINI:
            chat = self.client.start_chat(history=formatted_messages[:-1])
            stream = await chat.send_message_async(
                formatted_messages[-1]['parts'][0],
                stream=True
            )
            async for chunk in stream:
                yield StreamResponse.create(chunk.text)

# Initialize global LLM client
llm_client = LLMClient()

# Main entry point for the chatbot
async def openai_chatbot_chain(messages: List[Dict[str, str]]):
    """Main entry point for chat completion - maintains backward compatibility"""
    formatted_messages = llm_client._format_messages(messages)
    
    if llm_client.config.provider == ModelProvider.OPENAI:
        stream = await llm_client.client.chat.completions.create(
            messages=formatted_messages,
            stream=True,
            **llm_client.config.to_dict()
        )
    elif llm_client.config.provider == ModelProvider.ANTHROPIC:
        stream = await llm_client.client.messages.create(
            messages=formatted_messages,
            stream=True,
            **llm_client.config.to_dict()
        )
    elif llm_client.config.provider == ModelProvider.GEMINI:
        chat = llm_client.client.start_chat(history=formatted_messages[:-1])
        stream = await chat.send_message_async(
            formatted_messages[-1]['parts'][0],
            stream=True
        )
    return stream
