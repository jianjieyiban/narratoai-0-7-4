#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Project: NarratoAI
@File   : __init__.py
@Author : viccy同学
@Date   : 2025/1/7
@Description: 统一提示词管理模块
"""

from .manager import PromptManager
from .base import BasePrompt, VisionPrompt, TextPrompt, ParameterizedPrompt
from .registry import PromptRegistry
from .template import TemplateRenderer
from .validators import PromptOutputValidator
from .exceptions import (
    PromptError,
    PromptNotFoundError,
    PromptValidationError,
    TemplateRenderError
)

# 版本信息
__version__ = "1.0.0"
__author__ = "viccy同学"

# 导出的公共接口
__all__ = [
    # 核心管理器
    "PromptManager",
    
    # 基础类
    "BasePrompt",
    "VisionPrompt", 
    "TextPrompt",
    "ParameterizedPrompt",
    
    # 工具类
    "PromptRegistry",
    "TemplateRenderer",
    "PromptOutputValidator",
    
    # 异常类
    "PromptError",
    "PromptNotFoundError",
    "PromptValidationError",
    "TemplateRenderError",
    
    # 版本信息
    "__version__",
    "__author__"
]

# 模块初始化
# 注意：提示词初始化需要在 LLM 提供商注册之后进行
# 因此不在模块导入时自动初始化，而是在需要时手动调用

def initialize_prompts():
    """初始化提示词模块，注册所有提示词"""
    from . import documentary
    from . import short_drama_editing  
    from . import short_drama_narration
    from . import outdoor_food
    from . import movie_commentary
    from . import movie_mashup
    from . import animal_world
    
    # 注册各模块的提示词
    documentary.register_prompts()
    short_drama_editing.register_prompts()
    short_drama_narration.register_prompts()
    outdoor_food.register_prompts()
    movie_commentary.register_prompts()
    movie_mashup.register_prompts()
    animal_world.register_prompts()
