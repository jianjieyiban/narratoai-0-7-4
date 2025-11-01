#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Project: NarratoAI
@File   : __init__.py
@Description: 影视混剪提示词模块
"""

from .narration_generation import MovieMashupNarrationPrompt


def register_prompts():
    """注册影视混剪相关提示词"""
    from ..registry import get_registry
    
    registry = get_registry()
    registry.register(MovieMashupNarrationPrompt(), is_default=True)


__all__ = [
    "MovieMashupNarrationPrompt",
    "register_prompts"
]
