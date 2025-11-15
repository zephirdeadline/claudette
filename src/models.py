from time import time
from typing import Dict
import json
import os
from rich.live import Live

from .tools import ToolExecutor
from . import ui
from .image_utils import extract_and_validate_images


class Model:

    def __init__(self, name: str, image_mode: bool, tool_executor: ToolExecutor | None, system_prompt: str,
                 ollama_client: object, max_token_context: int) -> None:
        self.name = name
        self.image_mode = image_mode
        self.tool_executor = tool_executor
        self.system_prompt = system_prompt
        self.ollama_client = ollama_client
        self.max_token_context = max_token_context


    def get_stream(self, conversation_history: list, keep_alive_duration: str = "15m", temperature: float = 0):
        stream = self.ollama_client.chat(
            model=self.name,
            messages=conversation_history,
            tools=self.tool_executor.tools_definition if self.tool_executor else None,
            stream=True,
            keep_alive=keep_alive_duration,
            options={"temperature": temperature}
        )
        return stream

    def process_message(self, conversation_history: list, live: Live, temperature: float = 0) -> (str, float):
        start_time = time()
        while True:
            full_content = ""
            tool_calls = []

            ui.show_thinking(full_content, live, start_time)
            for chunk in self.get_stream(conversation_history, temperature=temperature):
                message = chunk.get("message", {})
                if content := message.get("content"):
                    full_content += content
                    ui.show_thinking(full_content, live, start_time)
                elif message.get("tool_calls"):
                    tool_calls = message["tool_calls"]
                else:
                    ui.show_thinking(full_content, live, start_time)

            # Create the complete message for history
            assistant_message = self.get_assistant_message(full_content, tool_calls)

            # Add assistant response to history
            conversation_history.append(assistant_message)

            if not tool_calls:
                return f"{full_content}\n", time() - start_time
            # Process tool calls
            for tool_call in tool_calls:
                tool_result = self.call_tool(tool_call)
                conversation_history.append(self.tool_result_message(tool_result))
            # Continue the loop to get the next response from the model


    def get_assistant_message(self, full_content, tool_calls):
        assistant_message = {"role": "assistant", "content": full_content}
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        return assistant_message

    def tool_result_message(self, tool_result):
        return {
            "role": "tool",
            "content": tool_result
        }

    def call_tool(self, tool_call: dict):
        tool_name = tool_call["function"]["name"]
        tool_args = tool_call["function"]["arguments"]
        ui.show_tool_usage(tool_name, tool_args)
        # Execute the tool
        tool_result = self.tool_executor.execute_tool(tool_name, tool_args)
        # Add tool result to conversation

        ui.show_tool_result(tool_result)
        return tool_result


    def get_user_message(self, user_message: str) -> Dict[str, str]:
        return {
            "role": "user",
            "content": user_message
        }

    def get_system_prompt(self) -> dict:
        return {
            "role": "system",
            "content": self.system_prompt
        }


class VisionModel(Model):
    def get_user_message(self, user_message: str) -> Dict[str, str]:
        message = {
            "role": "user",
            "content": user_message
        }
        images_path = extract_and_validate_images(user_message)
        if images_path:
           message["images"] = images_path
           ui.show_image_found(images_path, user_message)
           # Remove image paths from content
           for image_path in images_path:
               message["content"] = message["content"].replace(image_path, "")
        return message



class DeepseekCodeV2(Model):

    def __init__(self, ollama_client):
        super().__init__("deepseek-coder-v2:16b", image_mode = False, tool_executor = None, system_prompt = "Hello", ollama_client = ollama_client, max_token_context=160000)

class Qwen3_4b(Model):

    def __init__(self, ollama_client, tool_executor):
        super().__init__("qwen3:4b", image_mode = False, tool_executor = tool_executor, system_prompt = "Hello", ollama_client = ollama_client, max_token_context=256000)


class ModelFactory:
    """Factory to create model instances based on model name"""

    @staticmethod
    def _load_config(name: str) -> dict | None:
        """Load model configuration from JSON file"""
        import json
        import os

        config_path = os.path.join(".claudette", "models_config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            models = config.get("models", {})
            if name in models:
                return models[name]

        except Exception as e:
            print(f"Warning: Failed to load models_config.json: {e}")

        return None

    @staticmethod
    def _get_model_info_from_ollama(model_name: str, ollama_client: object) -> dict:
        """Get model information from Ollama"""
        try:
            model_info = ollama_client.show(model_name)

            # Extract context length
            context_length = 2048  # default
            modelinfo = model_info.get('modelinfo', {})
            for key in modelinfo.keys():
                if 'context_length' in key:
                    context_length = modelinfo[key]
                    break

            # Extract capabilities
            capabilities = model_info.get('capabilities', [])
            has_vision = 'vision' in capabilities
            has_tools = 'tools' in capabilities or 'function_calling' in capabilities

            return {
                'max_token_context': context_length,
                'supports_vision': has_vision,
                'supports_tools': has_tools
            }
        except Exception as e:
            print(f"Warning: Failed to get model info from Ollama: {e}")
            return {
                'max_token_context': 2048,
                'supports_vision': False,
                'supports_tools': False
            }

    @staticmethod
    def create_model(
        model_name: str,
        ollama_client: object,
        tool_executor: ToolExecutor | None = None,
    ) -> Model | None:
        """
        Create a model instance based on the model name

        Args:
            model_name: Name of the model (e.g., "qwen3:4b")
            ollama_client: Ollama client instance
            tool_executor: Optional tool executor for models that support tools

        Returns:
            Model instance or None if failed
        """
        # Get config from JSON (system_prompt, enable_tools)
        config = ModelFactory._load_config(name=model_name)

        # Get model info from Ollama (context, vision, tools support)
        ollama_info = ModelFactory._get_model_info_from_ollama(model_name, ollama_client)

        # Use default values if config not found
        system_prompt = config.get('system_prompt', 'You are a helpful AI assistant.') if config else 'You are a helpful AI assistant.'
        enable_tools = config.get('enable_tools', False) if config else False

        # Determine if should use VisionModel
        use_vision_model = ollama_info['supports_vision']

        # Create the appropriate model instance
        klass_model = VisionModel if use_vision_model else Model

        return klass_model(
            name=model_name,
            image_mode=ollama_info['supports_vision'],
            tool_executor=tool_executor if enable_tools and ollama_info['supports_tools'] else None,
            system_prompt=system_prompt,
            ollama_client=ollama_client,
            max_token_context=ollama_info['max_token_context'],
        )

    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available model names from config"""
        import json
        import os

        config_path = os.path.join(".claudette", "models_config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return list(config.get("models", {}).keys())
        except:
            return []

    @staticmethod
    def is_model_ready(name: str) -> bool:
        """Check if a model is configured in Claudette"""
        return name in ModelFactory.get_available_models()

