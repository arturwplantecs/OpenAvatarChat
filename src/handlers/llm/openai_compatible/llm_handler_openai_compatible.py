

import os
import re
from typing import Dict, Optional, cast
from loguru import logger
from pydantic import BaseModel, Field
from abc import ABC
from openai import OpenAI
from chat_engine.contexts.handler_context import HandlerContext
from chat_engine.data_models.chat_engine_config_data import ChatEngineConfigModel, HandlerBaseConfigModel
from chat_engine.common.handler_base import HandlerBase, HandlerBaseInfo, HandlerDataInfo, HandlerDetail
from chat_engine.data_models.chat_data.chat_data_model import ChatData
from chat_engine.data_models.chat_data_type import ChatDataType
from chat_engine.contexts.session_context import SessionContext
from chat_engine.data_models.runtime_data.data_bundle import DataBundle, DataBundleDefinition, DataBundleEntry
from handlers.llm.openai_compatible.chat_history_manager import ChatHistory, HistoryMessage


class LLMConfig(HandlerBaseConfigModel, BaseModel):
    model_name: str = Field(default="qwen-plus")
    system_prompt: str = Field(default="请你扮演一个 AI 助手，用简短的对话来回答用户的问题，并在对话内容中加入合适的标点符号，不需要加入标点符号相关的内容")
    api_key: str = Field(default=os.getenv("DASHSCOPE_API_KEY"))
    api_url: str = Field(default=None)
    enable_video_input: bool = Field(default=False)
    language: str = Field(default="en")


class LLMContext(HandlerContext):
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.config = None
        self.local_session_id = 0
        self.model_name = None
        self.system_prompt = None
        self.api_key = None
        self.api_url = None
        self.client = None
        self.input_texts = ""
        self.output_texts = ""
        self.current_image = None
        self.history = ChatHistory()
        self.enable_video_input = False
        self.language = "en"


class HandlerLLM(HandlerBase, ABC):
    def __init__(self):
        super().__init__()

    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(
            config_model=LLMConfig,
        )

    def get_handler_detail(self, session_context: SessionContext,
                           context: HandlerContext) -> HandlerDetail:
        definition = DataBundleDefinition()
        definition.add_entry(DataBundleEntry.create_text_entry("avatar_text"))
        inputs = {
            ChatDataType.HUMAN_TEXT: HandlerDataInfo(
                type=ChatDataType.HUMAN_TEXT,
            ),
            ChatDataType.CAMERA_VIDEO: HandlerDataInfo(
                type=ChatDataType.CAMERA_VIDEO,
            ),
        }
        outputs = {
            ChatDataType.AVATAR_TEXT: HandlerDataInfo(
                type=ChatDataType.AVATAR_TEXT,
                definition=definition,
            )
        }
        return HandlerDetail(
            inputs=inputs, outputs=outputs,
        )

    def load(self, engine_config: ChatEngineConfigModel, handler_config: Optional[BaseModel] = None):
        if isinstance(handler_config, LLMConfig):
            if handler_config.api_key is None or len(handler_config.api_key) == 0:
                error_message = 'api_key is required in config/xxx.yaml, when use handler_llm'
                logger.error(error_message)
                raise ValueError(error_message)

    def create_context(self, session_context, handler_config=None):
        if not isinstance(handler_config, LLMConfig):
            handler_config = LLMConfig()
        context = LLMContext(session_context.session_info.session_id)
        context.model_name = handler_config.model_name
        context.system_prompt = {'role': 'system', 'content': handler_config.system_prompt}
        context.api_key = handler_config.api_key
        context.api_url = handler_config.api_url
        context.enable_video_input = handler_config.enable_video_input
        context.language = handler_config.language
        
        context.client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=context.api_key,
            base_url=context.api_url,
        )
        return context
    
    def start_context(self, session_context, handler_context):
        pass

    def handle(self, context: HandlerContext, inputs: ChatData,
               output_definitions: Dict[ChatDataType, HandlerDataInfo]):
        output_definition = output_definitions.get(ChatDataType.AVATAR_TEXT).definition
        context = cast(LLMContext, context)
        text = None
        if inputs.type == ChatDataType.CAMERA_VIDEO and context.enable_video_input:
            context.current_image = inputs.data.get_main_data()
            return
        elif inputs.type == ChatDataType.HUMAN_TEXT:
            text = inputs.data.get_main_data()
        else:
            return
        speech_id = inputs.data.get_meta("speech_id")
        if (speech_id is None):
            speech_id = context.session_id

        if text is not None:
            context.input_texts += text

        text_end = inputs.data.get_meta("human_text_end", False)
        if not text_end:
            return

        chat_text = context.input_texts
        chat_text = re.sub(r"<\|.*?\|>", "", chat_text)
        if len(chat_text) < 1:
            return
        logger.info(f'llm input {context.model_name} {chat_text} ')
        
        # Only pass images for explicit visual questions
        images_to_pass = []
        visual_keywords = ['co widzisz', 'opisz obraz', 'co jest na zdjęciu', 'kto to na obrazie', 'powiedz mi co widzisz']
        is_visual_question = any(keyword in chat_text.lower() for keyword in visual_keywords)
        
        logger.info(f"=== VISUAL QUESTION DETECTION ===")
        logger.info(f"Input text: '{chat_text}'")
        logger.info(f"Input text lower: '{chat_text.lower()}'")
        logger.info(f"Visual keywords: {visual_keywords}")
        logger.info(f"Is visual question: {is_visual_question}")
        logger.info(f"Current image available: {context.current_image is not None}")
        
        if context.current_image is not None and is_visual_question:
            images_to_pass = [context.current_image]
            logger.info(f"DECISION: Passing image to LLM - visual question detected")
        else:
            logger.info(f"DECISION: Not passing image to LLM - normal conversation")
        logger.info(f"=== END VISUAL DETECTION ===")
            
        current_content = context.history.generate_next_messages(chat_text, images_to_pass)
        logger.debug(f'llm input {context.model_name} {current_content} ')
        
        # Log what we're sending to OpenAI
        messages_to_send = [context.system_prompt] + current_content
        logger.info(f"=== SENDING TO OPENAI ===")
        logger.info(f"Model: {context.model_name}")
        logger.info(f"Messages count: {len(messages_to_send)}")
        for i, msg in enumerate(messages_to_send):
            logger.info(f"Message {i}: {msg}")
        logger.info(f"=== END SENDING ===")
        
        completion = context.client.chat.completions.create(
            model=context.model_name,  # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[
                context.system_prompt,
            ] + current_content,
            stream=True,
            stream_options={"include_usage": True}
        )
        # Don't clear current_image - keep the latest camera frame available
        # context.current_image = None
        context.input_texts = ''
        context.output_texts = ''
        
        logger.info(f"=== RECEIVING FROM OPENAI ===")
        response_text = ""
        for chunk in completion:
            if (chunk and chunk.choices and chunk.choices[0] and chunk.choices[0].delta.content):
                output_text = chunk.choices[0].delta.content
                context.output_texts += output_text
                response_text += output_text
                logger.info(output_text)
                output = DataBundle(output_definition)
                output.set_main_data(output_text)
                output.add_meta("avatar_text_end", False)
                output.add_meta("speech_id", speech_id)
                yield output
        logger.info(f"Complete response: {response_text}")
        logger.info(f"=== END RECEIVING ===")
        
        context.history.add_message(HistoryMessage(role="avatar", content=context.output_texts))
        context.output_texts = ''
        logger.info('avatar text end')
        end_output = DataBundle(output_definition)
        end_output.set_main_data('')
        end_output.add_meta("avatar_text_end", True)
        end_output.add_meta("speech_id", speech_id)
        yield end_output

    def destroy_context(self, context: HandlerContext):
        pass

