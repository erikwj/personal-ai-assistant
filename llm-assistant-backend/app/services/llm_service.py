from llama_cpp import Llama
from app.models.chat import ChatMessage
import os
from pathlib import Path
from typing import Generator, Optional, AsyncGenerator
import logging
import aiohttp

class LLMService:
    def __init__(self, docstore_url: str = "http://localhost:8001"):
        self.docstore_url = docstore_url
        model_path = os.getenv("MODEL_PATH")
        
        # Define system prompts
        self.system_prompt = """You are a helpful AI assistant that provides accurate information based strictly on the given context. 
Your responses should:
1. Only use information explicitly stated in the provided context
2. Say "I don't have enough information" when no context is provided unless the the user has a factual question
3. Never make assumptions or infer details on questions or topics that are not factual
4. Quote relevant parts of the context when appropriate
5. Be concise and direct"""

        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please download a GGUF format model and place it in the models directory, "
                "or set the MODEL_PATH environment variable to point to your model file."
            )
        
        logging.getLogger('llama_cpp').setLevel(logging.ERROR)
        
        try:
            self.llm = Llama(
                model_path=model_path,
                n_gpu_layers=32,
                verbose=False,
                n_ctx=32000
            )
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise
    
    async def generate_response_stream(self, messages: list[ChatMessage], temperature: float = 0.15, max_tokens: int = 150) -> AsyncGenerator[str, None]:
        try:
            # Get the last user message to fetch relevant context
            last_user_message = next((msg.content for msg in reversed(messages) if msg.role == "user"), None)
            context = None
            
            if last_user_message:
                # Fetch context for the last user message
                context = await self.get_context(last_user_message)
                if context:
                    logging.info("Context found and will be used for response")
                    logging.debug(f"Context preview: {context[:200]}...")
                else:
                    logging.info("No relevant context found")

            # Build the prompt with system message and context
            formatted_messages = [f"System: {self.system_prompt}"]
            
            if context:
                formatted_messages.append(f"\nRelevant Context:\n{context}\n")
            
            # Add conversation history
            for msg in messages:
                if msg.role == "user":
                    formatted_messages.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    formatted_messages.append(f"Assistant: {msg.content}")
            
            prompt = "\n".join(formatted_messages)
            prompt += "\nAssistant:"

            # Generate streaming response
            stream = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.76,
                top_k=10,
                repeat_penalty=1.2,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                stop=["User:", "Context:", "System:"],
                stream=True
            )
            
            for output in stream:
                if output and 'choices' in output and len(output['choices']) > 0:
                    text = output['choices'][0]['text']
                    if text:
                        yield text

        except Exception as e:
            logging.error(f"Error in generate_response_stream: {str(e)}")
            logging.exception("Full traceback:")
            yield f"Error generating response: {str(e)}"

    async def get_context(self, query: str) -> Optional[str]:
        try:
            # Make request to docstore with new query format
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.docstore_url}/query",
                    json={
                        "query": query,
                        "num_results": 2,
                        "min_similarity": 0.1
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Check if we have results using new response format
                        if result.get("has_results") and result.get("results"):
                            # Use dict to deduplicate by source
                            unique_contexts = {}
                            
                            for doc_result in result["results"]:
                                source = doc_result["metadata"]["source"]
                                # Only add if we haven't seen this source before
                                if source not in unique_contexts:
                                    full_doc = doc_result["metadata"]["full_document"]
                                    unique_contexts[source] = f"Source: {source}\n\n{full_doc}"
                            
                            if not unique_contexts:
                                return None
                            
                            # Combine unique contexts with separators
                            context = "\n\n---\n\n".join(unique_contexts.values())
                            logging.info(f"Found {len(unique_contexts)} unique documents for context")
                            return context
                            
                        return None
                    else:
                        logging.error(f"Error fetching context: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"Error getting context: {str(e)}", exc_info=True)
            return None

    async def process_prompt(self, prompt: str) -> str:
        """Process a prompt with context from the document store"""
        try:
            context = await self.get_context(prompt)
            
            if context:
                full_prompt = f"""{self.system_prompt}

Context:
{context}

Question: {prompt}
Answer (based strictly on the above context):"""
            else:
                full_prompt = f"""{self.system_prompt}

Question: {prompt}
Answer: I don't have any relevant information in my context to answer this question."""

            response = self.llm(
                full_prompt,
                max_tokens=150,
                temperature=0.1,
                top_p=0.1,
                top_k=10,
                repeat_penalty=1.2,
                stop=["Question:", "Context:", "System:"],
            )

            return response['choices'][0]['text'].strip()

        except Exception as e:
            logging.error(f"Error processing prompt: {str(e)}")
            return f"Error processing prompt: {str(e)}"