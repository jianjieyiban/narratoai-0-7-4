#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Project: NarratoAI
@File   : __init__.py
@Description: 野外美食制作提示词模块
"""

from .narration_generation import OutdoorFoodNarrationPrompt


def register_prompts():
    """注册野外美食制作相关提示词"""
    from ..registry import get_registry
    
    registry = get_registry()
    registry.register(OutdoorFoodNarrationPrompt(), is_default=True)


__all__ = [
    "OutdoorFoodNarrationPrompt",
    "register_prompts"
]
