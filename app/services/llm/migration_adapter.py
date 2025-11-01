"""
迁移适配器

为现有代码提供向后兼容的接口，方便逐步迁移到新的LLM服务架构
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import PIL.Image
from loguru import logger

from .unified_service import UnifiedLLMService
from .exceptions import LLMServiceError
# 导入新的提示词管理系统
from app.services.prompts import PromptManager

# 提供商注册由 webui.py:main() 显式调用（见 LLM 提供商注册机制重构）
# 这样更可靠，错误也更容易调试


def _run_async_safely(coro_func, *args, **kwargs):
    """
    安全地运行异步协程，处理各种事件循环情况

    Args:
        coro_func: 协程函数（不是协程对象）
        *args: 协程函数的位置参数
        **kwargs: 协程函数的关键字参数

    Returns:
        协程的执行结果
    """
    def run_in_new_loop():
        """在新的事件循环中运行协程"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro_func(*args, **kwargs))
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的事件循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            return run_in_new_loop()
    except Exception as e:
        logger.error(f"异步执行失败: {str(e)}")
        raise LLMServiceError(f"异步执行失败: {str(e)}")


class LegacyLLMAdapter:
    """传统LLM接口适配器"""
    
    @staticmethod
    def create_vision_analyzer(provider: str, api_key: str, model: str, base_url: str = None):
        """
        创建视觉分析器实例 - 兼容原有接口
        
        Args:
            provider: 提供商名称
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL
            
        Returns:
            适配器实例
        """
        return VisionAnalyzerAdapter(provider, api_key, model, base_url)
    
    @staticmethod
    def generate_narration(markdown_content: str, api_key: str, base_url: str, model: str, video_type: str = "documentary") -> str:
        """
        生成解说文案 - 兼容原有接口

        Args:
            markdown_content: Markdown格式的视频帧分析内容
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            video_type: 视频类型，支持: documentary(纪录片), outdoor_food(野外美食), movie_commentary(影视解说), movie_mashup(影视混剪), animal_world(动物世界)

        Returns:
            生成的解说文案JSON字符串
        """
        try:
            # 确保提示词已初始化（防止Streamlit重载时提示词未注册）
            try:
                # 先检查提示词是否存在
                if not PromptManager.exists(category=video_type, name="narration_generation"):
                    logger.warning(f"提示词 {video_type}.narration_generation 未找到，尝试重新初始化")
                    from app.services.prompts import initialize_prompts
                    initialize_prompts()
                    logger.info(f"提示词重新初始化完成")
            except Exception as init_error:
                logger.warning(f"提示词初始化检查失败: {init_error}，尝试重新初始化")
                try:
                    from app.services.prompts import initialize_prompts
                    initialize_prompts()
                except Exception as reinit_error:
                    logger.error(f"提示词重新初始化失败: {reinit_error}")
                    # 如果重新初始化失败，使用默认的documentary类型
                    if video_type != "documentary":
                        logger.warning(f"无法初始化 {video_type} 类型的提示词，回退到 documentary 类型")
                        video_type = "documentary"
            
            # 使用新的提示词管理系统，根据视频类型选择对应的提示词
            prompt = PromptManager.get_prompt(
                category=video_type,  # 根据视频类型选择提示词分类
                name="narration_generation",
                parameters={
                    "video_frame_description": markdown_content
                }
            )

            # 使用统一服务生成文案（添加超时控制）
            async def generate_with_timeout():
                """带超时的文本生成包装函数"""
                try:
                    result = await asyncio.wait_for(
                        UnifiedLLMService.generate_text(
                            prompt=prompt,
                            system_prompt="你是一名专业的短视频解说文案撰写专家。",
                            temperature=1.5,
                            response_format="json"
                        ),
                        timeout=180  # 3分钟超时（文本生成通常比视觉分析快）
                    )
                    return result
                except asyncio.TimeoutError:
                    logger.error("文本生成超时（超过3分钟）")
                    raise Exception("解说文案生成超时，可能API响应过慢。请检查网络连接或API配置。")
            
            result = _run_async_safely(generate_with_timeout)

            # 检查markdown_content是否为空
            if not markdown_content or not markdown_content.strip():
                logger.warning("视频帧描述为空，无法生成准确的解说文案")
                return json.dumps({
                    "items": [
                        {
                            "_id": 1,
                            "timestamp": "00:00:00,000-00:00:05,500",
                            "picture": "视频帧分析未完成，请重新执行'AI生成画面解说脚本'功能进行视频帧分析",
                            "narration": "视频帧分析未完成，无法生成解说文案。请确保已成功完成视频帧分析步骤。"
                        }
                    ]
                }, ensure_ascii=False)
            
            # 使用增强的JSON解析器
            from webui.tools.generate_short_summary import parse_and_fix_json
            parsed_result = parse_and_fix_json(result)

            if not parsed_result:
                logger.error("无法解析LLM返回的JSON数据")
                # 检查是否有video_frame_description，如果没有，说明是视频帧分析问题
                if not markdown_content or not markdown_content.strip():
                    return json.dumps({
                        "items": [
                            {
                                "_id": 1,
                                "timestamp": "00:00:00,000-00:00:05,500",
                                "picture": "视频帧分析未完成，请重新执行'AI生成画面解说脚本'功能进行视频帧分析",
                                "narration": "视频帧分析未完成，无法生成解说文案。请确保已成功完成视频帧分析步骤。"
                            }
                        ]
                    }, ensure_ascii=False)
                # 返回一个基本的JSON结构而不是错误字符串
                return json.dumps({
                    "items": [
                        {
                            "_id": 1,
                            "timestamp": "00:00:00,000-00:00:10,000",
                            "picture": "解析失败，请检查LLM输出",
                            "narration": "解说文案生成失败，请重试"
                        }
                    ]
                }, ensure_ascii=False)

            # 确保返回的是JSON字符串
            return json.dumps(parsed_result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"生成解说文案失败: {str(e)}")
            # 返回一个基本的JSON结构而不是错误字符串
            return json.dumps({
                "items": [
                    {
                        "_id": 1,
                        "timestamp": "00:00:00-00:00:10",
                        "picture": "生成失败",
                        "narration": f"解说文案生成失败: {str(e)}"
                    }
                ]
            }, ensure_ascii=False)


class VisionAnalyzerAdapter:
    """视觉分析器适配器"""
    
    def __init__(self, provider: str, api_key: str, model: str, base_url: str = None):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    async def analyze_images(self,
                           images: List[Union[str, Path, PIL.Image.Image]],
                           prompt: str,
                           batch_size: int = 10,
                           **kwargs) -> List[Dict[str, Any]]:
        """
        分析图片 - 兼容原有接口

        Args:
            images: 图片列表
            prompt: 分析提示词
            batch_size: 批处理大小

        Returns:
            分析结果列表，格式与旧实现兼容
        """
        try:
            # 使用统一服务分析图片
            results = await UnifiedLLMService.analyze_images(
                images=images,
                prompt=prompt,
                provider=self.provider,
                batch_size=batch_size,
                **kwargs
            )

            # 转换为旧格式以保持向后兼容性
            # 新实现返回 List[str]，需要转换为 List[Dict]
            compatible_results = []
            for i, result in enumerate(results):
                # 计算这个批次处理的图片数量
                start_idx = i * batch_size
                end_idx = min(start_idx + batch_size, len(images))
                images_processed = end_idx - start_idx

                compatible_results.append({
                    'batch_index': i,
                    'images_processed': images_processed,
                    'response': result,
                    'model_used': self.model
                })

            logger.info(f"图片分析完成，共处理 {len(images)} 张图片，生成 {len(compatible_results)} 个批次结果")
            return compatible_results

        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise


class SubtitleAnalyzerAdapter:
    """字幕分析器适配器"""

    def __init__(self, api_key: str, model: str, base_url: str, provider: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.provider = provider or "openai"

    def _run_async_safely(self, coro_func, *args, **kwargs):
        """安全地运行异步协程"""
        return _run_async_safely(coro_func, *args, **kwargs)

    def _clean_json_output(self, output: str) -> str:
        """清理JSON输出，移除markdown标记等"""
        import re

        # 移除可能的markdown代码块标记
        output = re.sub(r'^```json\s*', '', output, flags=re.MULTILINE)
        output = re.sub(r'^```\s*$', '', output, flags=re.MULTILINE)
        output = re.sub(r'^```.*$', '', output, flags=re.MULTILINE)

        # 移除开头和结尾的```标记
        output = re.sub(r'^```', '', output)
        output = re.sub(r'```$', '', output)

        # 移除前后空白字符
        output = output.strip()

        return output
    
    def analyze_subtitle(self, subtitle_content: str) -> Dict[str, Any]:
        """
        分析字幕内容 - 兼容原有接口
        
        Args:
            subtitle_content: 字幕内容
            
        Returns:
            分析结果字典
        """
        try:
            # 使用统一服务分析字幕
            result = self._run_async_safely(
                UnifiedLLMService.analyze_subtitle,
                subtitle_content=subtitle_content,
                provider=self.provider,
                temperature=1.0
            )
            
            return {
                "status": "success",
                "analysis": result,
                "model": self.model,
                "temperature": 1.0
            }
            
        except Exception as e:
            logger.error(f"字幕分析失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "temperature": 1.0
            }
    
    def generate_narration_script(self, short_name: str, plot_analysis: str, subtitle_content: str = "", temperature: float = 0.7) -> Dict[str, Any]:
        """
        生成解说文案 - 兼容原有接口

        Args:
            short_name: 短剧名称
            plot_analysis: 剧情分析内容
            subtitle_content: 原始字幕内容，用于提供准确的时间戳信息
            temperature: 生成温度

        Returns:
            生成结果字典
        """
        try:
            # 使用新的提示词管理系统构建提示词
            prompt = PromptManager.get_prompt(
                category="short_drama_narration",
                name="script_generation",
                parameters={
                    "drama_name": short_name,
                    "plot_analysis": plot_analysis,
                    "subtitle_content": subtitle_content
                }
            )
            
            # 使用统一服务生成文案
            result = self._run_async_safely(
                UnifiedLLMService.generate_text,
                prompt=prompt,
                system_prompt="你是一位专业的短视频解说脚本撰写专家。",
                provider=self.provider,
                temperature=temperature,
                response_format="json"
            )
            
            # 清理JSON输出
            cleaned_result = self._clean_json_output(result)

            # 新的提示词系统返回的是包含items数组的JSON格式
            # 为了保持向后兼容，我们需要直接返回这个JSON字符串
            # 调用方会期望这是一个包含items数组的JSON字符串
            return {
                "status": "success",
                "narration_script": cleaned_result,
                "model": self.model,
                "temperature": temperature
            }
            
        except Exception as e:
            logger.error(f"解说文案生成失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "temperature": temperature
            }


# 为了向后兼容，提供一些全局函数
def create_vision_analyzer(provider: str, api_key: str, model: str, base_url: str = None):
    """创建视觉分析器 - 全局函数"""
    return LegacyLLMAdapter.create_vision_analyzer(provider, api_key, model, base_url)


def generate_narration(markdown_content: str, api_key: str, base_url: str, model: str, video_type: str = "documentary") -> str:
    """生成解说文案 - 全局函数"""
    return LegacyLLMAdapter.generate_narration(markdown_content, api_key, base_url, model, video_type)
