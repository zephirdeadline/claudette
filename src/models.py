from time import time
from typing import Dict

from rich.live import Live

from .tools import ToolExecutor
from . import ui
from .image_utils import extract_and_validate_images


class Model:

    def __init__(self, name: str, image_mode: bool, tool_executor: ToolExecutor | None, system_prompt: str,
                 ollama_client: object) -> None:
        self.name = name
        self.image_mode = image_mode
        self.tool_executor = tool_executor
        self.system_prompt = system_prompt
        self.ollama_client = ollama_client


    def get_stream(self, conversation_history: list):
        stream = self.ollama_client.chat(
            model=self.name,
            messages=conversation_history,
            tools=self.tool_executor.tools_definition if self.tool_executor else None,
            stream=True,
            keep_alive="15m"
        )
        return stream

    def process_message(self, conversation_history: list, live: Live) -> (str, float):
        start_time = time()
        while True:
            full_content = ""
            tool_calls = []

            ui.show_thinking(full_content, live, start_time)
            for chunk in self.get_stream(conversation_history):
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

    def __init__(self, name: str, ollama_client):
        super().__init__(name, image_mode = False, tool_executor = None, system_prompt = "Hello", ollama_client = ollama_client)

class Qwen3_4b(Model):

    def __init__(self, ollama_client, tool_executor):
        super().__init__("qwen3:4b", image_mode = False, tool_executor = tool_executor, system_prompt = "Hello", ollama_client = ollama_client)

