#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
@Project: NarratoAI
@File   : 生成介绍文案
@Author : Viccy同学
@Date   : 2025/5/8 上午11:33 
'''

import json
import os
import traceback
import asyncio
from openai import OpenAI
from loguru import logger

# 导入新的LLM服务模块 - 确保提供商被注册
import app.services.llm  # 这会触发提供商注册
from app.services.llm.migration_adapter import generate_narration as generate_narration_new
# 导入新的提示词管理系统
from app.services.prompts import PromptManager


def parse_frame_analysis_to_markdown(json_file_path):
    """
    解析视频帧分析JSON文件并转换为Markdown格式
    
    :param json_file_path: JSON文件路径
    :return: Markdown格式的字符串
    """
    # 检查文件是否存在
    if not os.path.exists(json_file_path):
        logger.error(f"视频帧分析文件不存在: {json_file_path}")
        return ""  # 返回空字符串，让调用者处理
    
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 检查数据是否为空
        if not data:
            logger.warning("视频帧分析JSON文件为空")
            return ""
        
        # 初始化Markdown字符串
        markdown = ""
        
        # 获取总结和帧观察数据
        summaries = data.get('overall_activity_summaries', [])
        frame_observations = data.get('frame_observations', [])
        
        # 如果没有任何数据，返回空字符串
        if not summaries and not frame_observations:
            logger.warning("视频帧分析数据为空，没有可用的帧观察或总结")
            return ""
        
        # 按批次组织数据
        batch_frames = {}
        for frame in frame_observations:
            batch_index = frame.get('batch_index')
            if batch_index not in batch_frames:
                batch_frames[batch_index] = []
            batch_frames[batch_index].append(frame)
        
        # 生成Markdown内容
        for i, summary in enumerate(summaries, 1):
            batch_index = summary.get('batch_index')
            time_range = summary.get('time_range', '')
            batch_summary = summary.get('summary', '')
            
            markdown += f"## 片段 {i}\n"
            markdown += f"- 时间范围：{time_range}\n"
            
            # 添加片段描述
            markdown += f"- 片段描述：{batch_summary}\n" if batch_summary else f"- 片段描述：\n"
            
            markdown += "- 详细描述：\n"
            
            # 添加该批次的帧观察详情
            frames = batch_frames.get(batch_index, [])
            if frames:
                for frame in frames:
                    timestamp = frame.get('timestamp', '')
                    observation = frame.get('observation', '')
                    
                    # 直接使用原始文本，不进行分割
                    markdown += f"  - {timestamp}: {observation}\n" if observation else f"  - {timestamp}: \n"
            else:
                # 如果没有帧观察，至少添加时间范围
                markdown += f"  - {time_range}: 暂无详细描述\n"
            
            markdown += "\n"
        
        # 如果没有任何总结但有帧观察，至少基于帧观察生成基本内容
        if not summaries and frame_observations:
            logger.info("没有总结数据，基于帧观察生成基本Markdown内容")
            markdown = "## 视频帧分析\n\n"
            for frame in frame_observations[:10]:  # 最多显示前10帧
                timestamp = frame.get('timestamp', '')
                observation = frame.get('observation', '')
                if observation:
                    markdown += f"- {timestamp}: {observation}\n"
        
        # 验证生成的markdown是否为空
        if not markdown.strip():
            logger.warning("生成的Markdown内容为空")
            return ""
        
        return markdown
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件格式错误: {str(e)}")
        return ""  # 返回空字符串
    except Exception as e:
        logger.error(f"处理JSON文件时出错: {traceback.format_exc()}")
        return ""  # 返回空字符串，而不是错误信息


def generate_narration(markdown_content, api_key, base_url, model, video_type="documentary"):
    """
    调用大模型API根据视频帧分析的Markdown内容生成解说文案 - 已重构为使用新的LLM服务架构

    :param markdown_content: Markdown格式的视频帧分析内容
    :param api_key: API密钥
    :param base_url: API基础URL
    :param model: 使用的模型名称
    :param video_type: 视频类型，支持: documentary(纪录片), outdoor_food(野外美食), movie_commentary(影视解说), movie_mashup(影视混剪)
    :return: 生成的解说文案
    """
    # 检查markdown_content是否为空或无效
    if not markdown_content or not markdown_content.strip():
        logger.warning("视频帧描述为空，无法生成准确的解说文案")
        # 返回一个基本的错误提示JSON，但格式正确
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
    
    try:
        # 优先使用新的LLM服务架构
        logger.info(f"使用新的LLM服务架构生成解说文案，视频类型: {video_type}")
        result = generate_narration_new(markdown_content, api_key, base_url, model, video_type)
        
        # 验证返回的结果
        if not result or result.strip() == "":
            logger.warning("LLM返回结果为空")
            raise Exception("LLM返回结果为空")
        
        return result

    except Exception as e:
        logger.warning(f"使用新LLM服务失败，回退到旧实现: {str(e)}")

        # 回退到旧的实现以确保兼容性
        return _generate_narration_legacy(markdown_content, api_key, base_url, model, video_type)


def _generate_narration_legacy(markdown_content, api_key, base_url, model, video_type="documentary"):
    """
    旧的解说文案生成实现 - 保留作为备用方案

    :param markdown_content: Markdown格式的视频帧分析内容
    :param api_key: API密钥
    :param base_url: API基础URL
    :param model: 使用的模型名称
    :param video_type: 视频类型
    :return: 生成的解说文案
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
        
        # 使用新的提示词管理系统构建提示词
        prompt = PromptManager.get_prompt(
            category=video_type,  # 根据视频类型选择对应的提示词
            name="narration_generation",
            parameters={
                "video_frame_description": markdown_content
            }
        )







        # 使用OpenAI SDK初始化客户端
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 使用SDK发送请求
        if model not in ["deepseek-reasoner"]:
            # deepseek-reasoner 不支持 json 输出
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一名专业的短视频解说文案撰写专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.5,
                response_format={"type": "json_object"},
            )
            # 提取生成的文案
            if response.choices and len(response.choices) > 0:
                narration_script = response.choices[0].message.content
                # 打印消耗的tokens
                logger.debug(f"消耗的tokens: {response.usage.total_tokens}")
                return narration_script
            else:
                return "生成解说文案失败: 未获取到有效响应"
        else:
            # 不支持 json 输出，需要多一步处理 ```json ``` 的步骤
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一名专业的短视频解说文案撰写专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.5,
            )
            # 提取生成的文案
            if response.choices and len(response.choices) > 0:
                narration_script = response.choices[0].message.content
                # 打印消耗的tokens
                logger.debug(f"文案消耗的tokens: {response.usage.total_tokens}")
                # 清理 narration_script 字符串前后的 ```json ``` 字符串
                narration_script = narration_script.replace("```json", "").replace("```", "")
                return narration_script
            else:
                return "生成解说文案失败: 未获取到有效响应"
    
    except Exception as e:
        return f"调用API生成解说文案时出错: {traceback.format_exc()}"


if __name__ == '__main__':
    text_provider = 'openai'
    text_api_key = "sk-xxx"
    text_model = "deepseek-reasoner"
    text_base_url = "https://api.deepseek.com"
    video_frame_description_path = "/Users/apple/Desktop/home/NarratoAI/storage/temp/analysis/frame_analysis_20250508_1139.json"

    # 测试新的JSON文件
    test_file_path = "/Users/apple/Desktop/home/NarratoAI/storage/temp/analysis/frame_analysis_20250508_2258.json"
    markdown_output = parse_frame_analysis_to_markdown(test_file_path)
    # print(markdown_output)
    
    # 输出到文件以便检查格式
    output_file = "/Users/apple/Desktop/home/NarratoAI/storage/temp/家里家外1-5.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    # print(f"\n已将Markdown输出保存到: {output_file}")
    
    # # 生成解说文案
    # narration = generate_narration(
    #     markdown_output,
    #     text_api_key,
    #     base_url=text_base_url,
    #     model=text_model
    # )
    #
    # # 保存解说文案
    # print(narration)
    # print(type(narration))
    # narration_file = "/Users/apple/Desktop/home/NarratoAI/storage/temp/final_narration_script.json"
    # with open(narration_file, 'w', encoding='utf-8') as f:
    #     f.write(narration)
    # print(f"\n已将解说文案保存到: {narration_file}")
