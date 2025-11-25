from time import time
from typing import Dict
from collections import Counter
from datetime import datetime
import os

import ollama
import yaml
import json
import re
from rich.live import Live

from .tools import ToolExecutor
from . import ui
from .image_utils import extract_and_validate_images
from .utils import StatsManager


class Model:

    def __init__(
        self,
        name: str,
        image_mode: bool,
        tool_executor: ToolExecutor | None,
        system_prompt: str,
        ollama_client: ollama.Client,
        max_token_context: int,
    ) -> None:
        self.name = name
        self.image_mode = image_mode
        self.tool_executor = tool_executor
        self.system_prompt = system_prompt
        self.ollama_client = ollama_client
        self.max_token_context = max_token_context
        self.stats_manager = StatsManager()

    def _get_max_thinking_tokens(self) -> int:
        """
        Get maximum thinking tokens based on model name.
        Models with explicit reasoning capabilities get higher limits.
        """
        model_name_lower = self.name.lower()

        # Reasoning models get higher limits
        if "r1" in model_name_lower or "deepseek-r1" in model_name_lower:
            if "1.5b" in model_name_lower or "1b" in model_name_lower:
                return 2048  # Smaller reasoning model
            elif "7b" in model_name_lower:
                return 4096  # Larger reasoning model
            else:
                return 4096  # Default for reasoning models

        # Regular models get stricter limits
        if "30b" in model_name_lower or "32b" in model_name_lower:
            return 3000  # Large models
        elif "14b" in model_name_lower or "16b" in model_name_lower:
            return 2000  # Medium models
        else:
            return 1500  # Small models (4b, 6.7b, 8b)

    @staticmethod
    def _detect_circular_thinking(thinking_content: str) -> bool:
        """
        Detect circular reasoning patterns in thinking content.
        Returns True if circular patterns are detected.
        """
        # Split into sentences
        sentences = thinking_content.split(".")
        if len(sentences) < 10:
            return False  # Too short to detect patterns

        # Look for repetitive phrases (last 20% of content)
        recent_portion = int(len(sentences) * 0.2)
        recent_sentences = (
            sentences[-recent_portion:] if recent_portion > 0 else sentences
        )

        # Check for common circular reasoning indicators
        circular_indicators = [
            "wait",
            "actually",
            "but then",
            "on second thought",
            "however",
            "let me reconsider",
            "thinking about it",
            "on the other hand",
            "but wait",
            "hmm",
        ]

        # Count occurrences of circular indicators in recent portion
        indicator_count = sum(
            1
            for sentence in recent_sentences
            for indicator in circular_indicators
            if indicator in sentence.lower()
        )

        # If more than 40% of recent sentences have circular indicators, flag it
        threshold = len(recent_sentences) * 0.4
        if indicator_count > threshold:
            return True

        # Check for repeated similar sentences (cosine similarity would be better, but this is simpler)
        # Look for sentences that appear multiple times
        normalized_sentences = [
            s.strip().lower() for s in recent_sentences if s.strip()
        ]
        sentence_counts = Counter(normalized_sentences)

        # If any sentence appears more than 3 times, it's likely circular
        for count in sentence_counts.values():
            if count >= 3:
                return True

        return False

    @staticmethod
    def _parse_function_call_text(content: str) -> dict | None:
        """
        Parse function calls from text like: web_search('query') or execute_command("ls")

        Returns:
            dict with 'function' key containing 'name' and 'arguments', or None if not found
        """
        import re

        # Pattern to match function calls: function_name('arg') or function_name("arg")
        # Supports single or double quotes, and handles escaped quotes
        pattern = r"(\w+)\s*\(\s*['\"]([^'\"]*)['\"](?:\s*,\s*(\{.*?\}))?\s*\)"

        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            func_name = match.group(1)
            arg = match.group(2)

            # Common tool names to look for
            tool_names = [
                "web_search",
                "execute_command",
                "read_file",
                "write_file",
                "edit_file",
                "list_directory",
                "ask_user",
                "get_current_time",
            ]

            if func_name in tool_names:
                # Build arguments based on function
                if func_name == "web_search":
                    arguments = {"query": arg}
                elif func_name == "execute_command":
                    arguments = {"command": arg}
                elif func_name == "read_file":
                    arguments = {"file_path": arg}
                elif func_name == "write_file":
                    arguments = {
                        "file_path": arg,
                        "content": "",
                    }  # Will need refinement
                elif func_name == "edit_file":
                    arguments = {"file_path": arg}  # Will need old_string, new_string
                elif func_name == "list_directory":
                    arguments = {"path": arg}
                elif func_name == "ask_user":
                    arguments = {"question": arg}
                else:
                    arguments = {}

                return {"function": {"name": func_name, "arguments": arguments}}

        return None

    @staticmethod
    def _find_json_blocks(content: str) -> list[str]:
        """
        Find all potential JSON blocks in content by matching braces.
        Returns list of JSON string candidates.
        """
        json_blocks = []
        i = 0
        while i < len(content):
            if content[i] == "{":
                # Found opening brace, find matching closing brace
                brace_count = 1
                j = i + 1
                while j < len(content) and brace_count > 0:
                    if content[j] == "{":
                        brace_count += 1
                    elif content[j] == "}":
                        brace_count -= 1
                    j += 1

                if brace_count == 0:
                    # Found matching closing brace
                    json_blocks.append(content[i:j])
                    i = j
                else:
                    i += 1
            else:
                i += 1

        return json_blocks

    @staticmethod
    def _parse_json_tool_call(content: str) -> dict | None:
        """
        Parse JSON tool call from content when model generates JSON instead of using tool_calls.
        Also handles XML-like format: <function=tool_name>{"arg": "value"}</tool_call>

        Returns:
            dict with 'function' key containing 'name' and 'arguments', or None if not a tool call
        """
        if not content.strip():
            return None

        # Try to parse XML-like format: <function=tool_name>...</tool_call>
        xml_pattern = r"<function=([^>]+)>\s*(.*?)\s*</tool_call>"
        xml_match = re.search(xml_pattern, content, re.DOTALL)
        if xml_match:
            tool_name = xml_match.group(1).strip()
            args_str = xml_match.group(2).strip()

            # Parse arguments if present (JSON format)
            arguments = {}
            if args_str:
                try:
                    arguments = json.loads(args_str)
                except json.JSONDecodeError:
                    pass  # Empty arguments

            return {"function": {"name": tool_name, "arguments": arguments}}

        # Find all JSON blocks in the content
        json_blocks = Model._find_json_blocks(content)

        # Try to parse each JSON block
        for json_str in json_blocks:
            try:
                parsed = json.loads(json_str)

                # Check if it looks like a tool call (has 'name' and 'arguments' keys)
                if (
                    isinstance(parsed, dict)
                    and "name" in parsed
                    and "arguments" in parsed
                ):
                    return {
                        "function": {
                            "name": parsed["name"],
                            "arguments": parsed["arguments"],
                        }
                    }
            except (json.JSONDecodeError, KeyError):
                continue

        # Fallback: Try to parse the whole content as JSON (for code blocks)
        try:
            # Remove markdown code blocks if present
            json_str = content.strip()
            if json_str.startswith("```"):
                json_str = re.sub(r"^```(?:json)?\s*", "", json_str)
                json_str = re.sub(r"\s*```$", "", json_str)

            parsed = json.loads(json_str)

            # Check if it looks like a tool call (has 'name' and 'arguments' keys)
            if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
                return {
                    "function": {
                        "name": parsed["name"],
                        "arguments": parsed["arguments"],
                    }
                }
        except (json.JSONDecodeError, KeyError):
            pass

        return None

    def get_stream(
        self,
        conversation_history: list,
        keep_alive_duration: str = "15m",
        temperature: float = 0,
        max_tokens: int | None = None,
        enable_thinking: bool = True,
    ):
        options = {"temperature": temperature}

        # Add max token limit if specified
        if max_tokens:
            options["num_predict"] = max_tokens

        stream = self.ollama_client.chat(
            model=self.name,
            messages=conversation_history,
            tools=self.tool_executor.tools_definition if self.tool_executor else None,
            stream=True,
            keep_alive=keep_alive_duration,
            options=options,
            think=enable_thinking,
        )
        return stream

    def _track_and_return(
        self,
        conversation_history: list,
        tokens_before: int,
        elapsed_time: float,
        response: str,
        thinking_content: str,
    ) -> (str, float, str):
        """Helper to track stats and return response"""
        # Calculate total tokens used in this request
        tokens_after = ui.get_conversation_token_count(conversation_history)
        total_tokens_used = tokens_after - tokens_before

        # Calculate thinking tokens (approximate: 4 chars per token)
        thinking_tokens = len(thinking_content) // 4 if thinking_content else 0

        # Response tokens = total - thinking tokens
        response_tokens = max(0, total_tokens_used - thinking_tokens)

        # Update stats with separate thinking and response tokens
        self.stats_manager.update_stats(
            self.name, thinking_tokens, response_tokens, elapsed_time
        )

        return response, elapsed_time, thinking_content

    def process_message(
        self,
        conversation_history: list,
        live: Live,
        temperature: float = 0,
        enable_thinking: bool = True,
    ) -> (str, float):
        start_time = time()
        # Track tokens before request
        tokens_before = ui.get_conversation_token_count(conversation_history)

        # Configuration: Maximum thinking tokens allowed (configurable per model size)
        MAX_THINKING_TOKENS = self._get_max_thinking_tokens()

        # Set a hard token limit: thinking + response buffer
        # This prevents the model from generating indefinitely
        MAX_TOTAL_TOKENS = MAX_THINKING_TOKENS + 2000  # +2000 for actual response

        thinking_loop_count = 0
        MAX_THINKING_LOOPS = (
            1  # Only retry once if model gives only thinking without answer
        )

        while True:
            full_content = ""
            thinking_content = ""
            tool_calls = []

            ui.show_thinking(full_content, live, start_time)

            # Use num_predict to hard-limit total generation
            for chunk in self.get_stream(
                conversation_history,
                temperature=temperature,
                max_tokens=MAX_TOTAL_TOKENS,
                enable_thinking=enable_thinking,
            ):
                message = chunk.get("message", {})

                # Check for content
                if content := message.get("content"):
                    full_content += content
                    ui.show_thinking(full_content, live, start_time, thinking_content)

                # Check for thinking (independent of content)
                if thinking := message.get("thinking"):
                    thinking_content += thinking
                    ui.show_thinking(full_content, live, start_time, thinking_content)

                # Check for tool calls (independent of content/thinking)
                if message.get("tool_calls"):
                    tool_calls = message["tool_calls"]

                # Update UI even if nothing new
                if not content and not thinking and not message.get("tool_calls"):
                    ui.show_thinking(full_content, live, start_time, thinking_content)

            # Check if we got a response or just endless thinking
            current_thinking_tokens = len(thinking_content) // 4

            # If we got mostly thinking and little/no content, retry with stricter prompt
            if (
                current_thinking_tokens > MAX_THINKING_TOKENS * 0.9
                and not full_content
                and not tool_calls
            ):
                thinking_loop_count += 1

                if thinking_loop_count >= MAX_THINKING_LOOPS:
                    # Force conclusion - model is stuck
                    elapsed = time() - start_time
                    response = f"[⚠️ Model exceeded thinking limit ({current_thinking_tokens} tokens) - provide a direct answer next time]\n\nBased on the analysis, I need to provide a direct answer but got stuck in thinking.\n"
                    return self._track_and_return(
                        conversation_history,
                        tokens_before,
                        elapsed,
                        response,
                        thinking_content,
                    )

                # Try again with NO thinking allowed - force direct answer
                conversation_history.append(
                    {
                        "role": "system",
                        "content": "STOP THINKING. Your previous response had excessive thinking. Answer the question DIRECTLY and CONCISELY now.",
                    }
                )
                # Lower token limit drastically for retry
                MAX_TOTAL_TOKENS = 1000
                continue

            # If no native tool_calls but content looks like a JSON tool call, parse it
            if not tool_calls and full_content and self.tool_executor:
                # Try parsing JSON format first
                parsed_tool = self._parse_json_tool_call(full_content)
                if parsed_tool:
                    ui.show_warning(
                        f"⚠️  Model used raw JSON instead of native tool calling. Parsing fallback applied."
                    )
                    tool_calls = [parsed_tool]
                    full_content = ""  # Clear content since it was a tool call
                else:
                    # Try parsing function call text format: web_search('query')
                    parsed_tool = self._parse_function_call_text(full_content)
                    if parsed_tool:
                        ui.show_warning(
                            f"⚠️  Model wrote function call as text instead of using native tool calling. Parsing fallback applied."
                        )
                        tool_calls = [parsed_tool]
                        # Remove the function call from content but keep explanation text
                        import re

                        # Remove patterns like: web_search('query') or execute_command("cmd")
                        cleaned_content = re.sub(
                            r'\b\w+\s*\(\s*[\'"][^\'"]*[\'"]\s*\)', "", full_content
                        ).strip()
                        full_content = cleaned_content if cleaned_content else ""

            # Create the complete message for history
            assistant_message = self.get_assistant_message(full_content, tool_calls)

            # Add assistant response to history
            conversation_history.append(assistant_message)

            if not tool_calls:
                elapsed = time() - start_time
                response = f"{full_content}\n"
                return self._track_and_return(
                    conversation_history,
                    tokens_before,
                    elapsed,
                    response,
                    thinking_content,
                )

            # Stop Live display before processing tool calls (some tools need user input)
            live.stop()

            # Process tool calls
            for tool_call in tool_calls:
                tool_result = self.call_tool(tool_call)
                conversation_history.append(self.tool_result_message(tool_result))

            # Restart Live display for next model response
            live.start()
            # Continue the loop to get the next response from the model

    def get_assistant_message(self, full_content, tool_calls):
        assistant_message = {"role": "assistant", "content": full_content}
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        return assistant_message

    def tool_result_message(self, tool_result):
        return {"role": "tool", "content": tool_result}

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
        return {"role": "user", "content": user_message}

    def get_system_prompt(self) -> dict:
        # Get current date and time for temporal context
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        day_of_week = now.strftime("%A")

        # Inject temporal context into system prompt
        temporal_context = f"""
CURRENT TEMPORAL CONTEXT:
- Date: {current_date}
- Day of Week: {day_of_week}
- Timezone: System local time

Use this temporal information to understand the current context when the user refers to time-sensitive concepts like "today", "yesterday", "this week", "this month", "recently", etc.
"""

        return {
            "role": "system",
            "content": temporal_context + "\n" + self.system_prompt,
        }


class VisionModel(Model):
    def get_user_message(self, user_message: str) -> Dict[str, str]:
        message = {"role": "user", "content": user_message}
        images_path = extract_and_validate_images(user_message)
        if images_path:
            message["images"] = images_path
            ui.show_image_found(images_path, user_message)
            # Remove image paths from content
            for image_path in images_path:
                message["content"] = message["content"].replace(image_path, "")
        return message


class ModelFactory:
    """Factory to create model instances based on model name"""

    @staticmethod
    def _load_config(name: str) -> dict | None:
        """Load model configuration from YAML file and merge with common prompts"""
        # Use XDG-compliant path resolution
        from .utils.paths import get_models_config_path

        config_path = str(get_models_config_path())

        # Only try this one path (it already handles the hierarchy)
        for config_path in [config_path]:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                models = config.get("models", {})
                if name in models:
                    model_config = models[name].copy()

                    # Merge common prompts if they exist
                    if "system_prompt" in model_config:
                        common_prompts = config.get("common_prompts", {})
                        if common_prompts:
                            # Build the full system prompt
                            full_prompt = model_config["system_prompt"]

                            # Append common sections in order
                            if "tool_usage_protocol" in common_prompts:
                                full_prompt += (
                                    "\n\n" + common_prompts["tool_usage_protocol"]
                                )

                            if "current_events_protocol" in common_prompts:
                                full_prompt += (
                                    "\n\n" + common_prompts["current_events_protocol"]
                                )

                            if "verification_protocol" in common_prompts:
                                full_prompt += (
                                    "\n\n" + common_prompts["verification_protocol"]
                                )

                            if "anti_loop_safeguards" in common_prompts:
                                full_prompt += (
                                    "\n\n" + common_prompts["anti_loop_safeguards"]
                                )

                            if "generic_instructions" in common_prompts:
                                # Only append if it contains actual instructions (not just placeholder)
                                generic = common_prompts["generic_instructions"].strip()
                                if (
                                    generic
                                    and not "(This section is reserved" in generic
                                ):
                                    full_prompt += (
                                        "\n\n" + common_prompts["generic_instructions"]
                                    )

                            model_config["system_prompt"] = full_prompt

                    return model_config

            except FileNotFoundError:
                continue  # Try next path
            except Exception as e:
                print(
                    f"Warning: Failed to load models_config.yaml from {config_path}: {e}"
                )
                continue

        return None

    @staticmethod
    def _get_model_info_from_ollama(model_name: str, ollama_client: object) -> dict:
        """Get model information from Ollama"""
        try:
            model_info = ollama_client.show(model_name)

            # Extract context length
            context_length = 2048  # default
            modelinfo = model_info.get("modelinfo", {})
            for key in modelinfo.keys():
                if "context_length" in key:
                    context_length = modelinfo[key]
                    break

            # Extract capabilities
            capabilities = model_info.get("capabilities", [])
            has_vision = "vision" in capabilities
            has_tools = "tools" in capabilities or "function_calling" in capabilities

            return {
                "max_token_context": context_length,
                "supports_vision": has_vision,
                "supports_tools": has_tools,
            }
        except Exception as e:
            print(f"Warning: Failed to get model info from Ollama: {e}")
            return {
                "max_token_context": 2048,
                "supports_vision": False,
                "supports_tools": False,
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
        ollama_info = ModelFactory._get_model_info_from_ollama(
            model_name, ollama_client
        )

        # Use default values if config not found
        system_prompt = (
            config.get("system_prompt", "You are a helpful AI assistant.")
            if config
            else "You are a helpful AI assistant."
        )

        # Determine if should use VisionModel
        use_vision_model = ollama_info["supports_vision"]

        # Create the appropriate model instance
        klass_model = VisionModel if use_vision_model else Model

        return klass_model(
            name=model_name,
            image_mode=use_vision_model,
            tool_executor=tool_executor if ollama_info["supports_tools"] else None,
            system_prompt=system_prompt,
            ollama_client=ollama_client,
            max_token_context=ollama_info["max_token_context"],
        )

    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available model names from config"""

        # Use XDG-compliant path resolution
        from .utils.paths import get_models_config_path

        config_path = str(get_models_config_path())

        # Only try this one path (it already handles the hierarchy)
        for config_path in [config_path]:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                return list(config.get("models", {}).keys())
            except FileNotFoundError:
                continue  # Try next path
            except:
                continue

        return []

    @staticmethod
    def is_model_ready(name: str) -> bool:
        """Check if a model is configured in Claudette"""
        return name in ModelFactory.get_available_models()
