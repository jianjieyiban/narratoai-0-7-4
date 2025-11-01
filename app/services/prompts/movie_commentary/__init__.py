#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Project: NarratoAI
@File   : __init__.py
@Description: 影视解说提示词模块
"""

from .narration_generation import MovieCommentaryNarrationPrompt


def register_prompts():
    """注册影视解说相关提示词"""
    from ..registry import get_registry
    
    registry = get_registry()
    registry.register(MovieCommentaryNarrationPrompt(), is_default=True)


__all__ = [
    "MovieCommentaryNarrationPrompt",
    "register_prompts"
]
