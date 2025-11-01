#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Project: NarratoAI
@File   : __init__.py
@Description: 动物世界解说提示词模块
"""

from .narration_generation import AnimalWorldNarrationPrompt


def register_prompts():
    """注册动物世界解说相关提示词"""
    from ..registry import get_registry
    
    registry = get_registry()
    registry.register(AnimalWorldNarrationPrompt(), is_default=True)


__all__ = [
    "AnimalWorldNarrationPrompt",
    "register_prompts"
]
