# 纪录片脚本生成
import os
import json
import time
import asyncio
import traceback
import streamlit as st
from loguru import logger
from datetime import datetime

from app.config import config
from app.utils import utils, video_processor
from webui.tools.base import create_vision_analyzer, get_batch_files, get_batch_timestamps, chekc_video_config


def generate_script_docu(params):
    """
    生成 纪录片 视频脚本
    要求: 原视频无字幕无配音
    适合场景: 纪录片、动物搞笑解说、荒野建造等
    """
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(progress: float, message: str = ""):
        progress_bar.progress(progress)
        if message:
            status_text.text(f"🎬 {message}")
        else:
            status_text.text(f"📊 进度: {progress}%")

    try:
        with st.spinner("正在生成脚本..."):
            if not params.video_origin_path:
                st.error("请先选择视频文件")
                return
            """
            1. 提取键帧
            """
            update_progress(10, "正在提取关键帧...")

            # 创建临时目录用于存储关键帧
            keyframes_dir = os.path.join(utils.temp_dir(), "keyframes")
            
            # 关键修复：使用视频文件的完整路径和修改时间生成唯一哈希
            # 确保即使文件名相同，但文件内容不同时也能正确识别
            video_path_normalized = os.path.abspath(params.video_origin_path)
            video_mtime = os.path.getmtime(video_path_normalized) if os.path.exists(video_path_normalized) else 0
            video_hash = utils.md5(video_path_normalized + str(video_mtime))
            video_keyframes_dir = os.path.join(keyframes_dir, video_hash)
            
            logger.info(f"视频文件: {video_path_normalized}, 修改时间: {video_mtime}, 哈希: {video_hash}")

            # 检查是否已经提取过关键帧（必须完全匹配当前视频文件）
            keyframe_files = []
            if os.path.exists(video_keyframes_dir):
                # 验证缓存目录是否属于当前视频文件
                # 双重验证：检查目录中的标记文件（如果存在）
                cache_valid = True
                cache_marker_file = os.path.join(video_keyframes_dir, ".video_info.txt")
                if os.path.exists(cache_marker_file):
                    try:
                        with open(cache_marker_file, 'r', encoding='utf-8') as f:
                            cached_info = f.read().strip()
                            if cached_info != video_path_normalized:
                                logger.warning(f"缓存目录的视频路径不匹配: {cached_info} != {video_path_normalized}")
                                cache_valid = False
                    except Exception as e:
                        logger.warning(f"读取缓存标记文件失败: {e}")
                        cache_valid = False
                
                if cache_valid:
                    # 取已有的关键帧文件
                    for filename in sorted(os.listdir(video_keyframes_dir)):
                        if filename.endswith('.jpg'):
                            keyframe_files.append(os.path.join(video_keyframes_dir, filename))

                    if keyframe_files:
                        logger.info(f"使用已缓存的关键帧: {video_keyframes_dir}")
                        st.info(f"✅ 使用已缓存关键帧，共 {len(keyframe_files)} 帧")
                        update_progress(20, f"使用已缓存关键帧，共 {len(keyframe_files)} 帧")
                else:
                    # 缓存无效，删除旧缓存目录
                    logger.warning(f"检测到无效缓存，删除旧缓存目录: {video_keyframes_dir}")
                    import shutil
                    try:
                        shutil.rmtree(video_keyframes_dir)
                        logger.info("已删除无效缓存目录")
                    except Exception as e:
                        logger.error(f"删除无效缓存目录失败: {e}")

            # 如果没有缓存的关键帧，则进行提取
            if not keyframe_files:
                try:
                    # 确保目录存在
                    os.makedirs(video_keyframes_dir, exist_ok=True)
                    
                    # 关键修复：保存视频文件信息到缓存目录，用于后续验证
                    cache_marker_file = os.path.join(video_keyframes_dir, ".video_info.txt")
                    try:
                        with open(cache_marker_file, 'w', encoding='utf-8') as f:
                            f.write(video_path_normalized)
                        logger.info(f"已保存视频信息到缓存标记文件: {cache_marker_file}")
                    except Exception as marker_error:
                        logger.warning(f"保存缓存标记文件失败: {marker_error}")

                    # 初始化视频处理器
                    processor = video_processor.VideoProcessor(params.video_origin_path)

                    # 验证视频信息是否有效
                    if processor.fps is None or processor.fps <= 0:
                        raise ValueError(f"无法获取有效的视频帧率信息，请检查视频文件: {params.video_origin_path}")
                    if processor.duration is None or processor.duration <= 0:
                        raise ValueError(f"无法获取有效的视频时长信息，请检查视频文件: {params.video_origin_path}")

                    # 显示视频信息
                    st.info(f"📹 视频信息: {processor.width}x{processor.height}, {processor.fps:.1f}fps, {processor.duration:.1f}秒")

                    # 处理视频并提取关键帧 - 直接使用超级兼容性方案
                    update_progress(15, "正在提取关键帧（使用超级兼容性方案）...")

                    # 获取帧间隔，确保不是 None
                    frame_interval = st.session_state.get('frame_interval_input')
                    if frame_interval is None:
                        frame_interval = 5.0  # 默认值
                        logger.warning(f"帧间隔未设置，使用默认值: {frame_interval}秒")
                    
                    # 确保 frame_interval 是有效的数字
                    try:
                        frame_interval = float(frame_interval)
                        if frame_interval <= 0:
                            frame_interval = 5.0
                            logger.warning(f"帧间隔无效，使用默认值: {frame_interval}秒")
                    except (ValueError, TypeError):
                        frame_interval = 5.0
                        logger.warning(f"帧间隔格式错误，使用默认值: {frame_interval}秒")

                    try:
                        # 使用优化的关键帧提取方法
                        processor.extract_frames_by_interval_ultra_compatible(
                            output_dir=video_keyframes_dir,
                            interval_seconds=frame_interval,
                        )
                    except Exception as extract_error:
                        logger.error(f"关键帧提取失败: {extract_error}")
                        
                        # 提供详细的错误信息和解决建议
                        error_msg = str(extract_error)
                        if "权限" in error_msg or "permission" in error_msg.lower():
                            suggestion = "建议：检查输出目录权限，或更换输出位置"
                        elif "空间" in error_msg or "space" in error_msg.lower():
                            suggestion = "建议：检查磁盘空间是否足够"
                        else:
                            suggestion = "建议：检查视频文件是否损坏，或尝试转换为标准格式"

                        raise Exception(f"关键帧提取失败: {error_msg}\n{suggestion}")

                    # 获取所有关键文件路径
                    for filename in sorted(os.listdir(video_keyframes_dir)):
                        if filename.endswith('.jpg'):
                            keyframe_files.append(os.path.join(video_keyframes_dir, filename))

                    if not keyframe_files:
                        # 检查目录中是否有其他文件
                        all_files = os.listdir(video_keyframes_dir)
                        logger.error(f"关键帧目录内容: {all_files}")
                        raise Exception("未提取到任何关键帧文件，请检查视频文件格式")

                    update_progress(20, f"关键帧提取完成，共 {len(keyframe_files)} 帧")
                    st.success(f"✅ 成功提取 {len(keyframe_files)} 个关键帧")

                except Exception as e:
                    # 如果提取失败，清理创建的目录
                    try:
                        if os.path.exists(video_keyframes_dir):
                            import shutil
                            shutil.rmtree(video_keyframes_dir)
                    except Exception as cleanup_err:
                        logger.error(f"清理失败的关键帧目录时出错: {cleanup_err}")

                    raise Exception(f"关键帧提取失败: {str(e)}")

            """
            2. 视觉分析(批量分析每一帧)
            """
            # 确保LLM提供商已注册（防止Streamlit重载时提供商未注册）
            try:
                from app.services.llm.manager import LLMServiceManager
                if not LLMServiceManager.is_registered():
                    logger.warning("LLM提供商未注册，尝试重新注册...")
                    from app.services.llm.providers import register_all_providers
                    register_all_providers()
                    logger.info("LLM提供商重新注册成功")
            except Exception as reg_error:
                logger.warning(f"LLM提供商注册检查失败: {reg_error}，继续尝试创建分析器")
            
            # 最佳实践：使用 get() 的默认值参数 + 从 config 获取备用值
            vision_llm_provider = (
                st.session_state.get('vision_llm_provider') or
                config.app.get('vision_llm_provider', 'litellm')
            ).lower()

            logger.info(f"使用 {vision_llm_provider.upper()} 进行视觉分析")

            try:
                # ===================初始化视觉分析器===================
                update_progress(30, "正在初始化视觉分析器...")

                # 使用统一的配置键格式获取配置（支持所有 provider）
                vision_api_key = (
                    st.session_state.get(f'vision_{vision_llm_provider}_api_key') or
                    config.app.get(f'vision_{vision_llm_provider}_api_key')
                )
                vision_model = (
                    st.session_state.get(f'vision_{vision_llm_provider}_model_name') or
                    config.app.get(f'vision_{vision_llm_provider}_model_name')
                )
                vision_base_url = (
                    st.session_state.get(f'vision_{vision_llm_provider}_base_url') or
                    config.app.get(f'vision_{vision_llm_provider}_base_url', '')
                )

                # 验证必需配置
                if not vision_api_key or not vision_model:
                    raise ValueError(
                        f"未配置 {vision_llm_provider} 的 API Key 或模型名称。"
                        f"请在设置页面配置 vision_{vision_llm_provider}_api_key 和 vision_{vision_llm_provider}_model_name"
                    )

                # 创建视觉分析器实例（使用统一接口）
                llm_params = {
                    "vision_provider": vision_llm_provider,
                    "vision_api_key": vision_api_key,
                    "vision_model_name": vision_model,
                    "vision_base_url": vision_base_url,
                }

                logger.debug(f"视觉分析器配置: provider={vision_llm_provider}, model={vision_model}")

                analyzer = create_vision_analyzer(
                    provider=vision_llm_provider,
                    api_key=vision_api_key,
                    model=vision_model,
                    base_url=vision_base_url
                )

                # 计算批处理参数
                vision_batch_size = st.session_state.get('vision_batch_size') or config.frames.get("vision_batch_size")
                total_frames = len(keyframe_files)
                estimated_batches = (total_frames + vision_batch_size - 1) // vision_batch_size
                
                # 对于少量帧，可以减少批处理大小以提高效率
                if total_frames <= 10 and vision_batch_size > 10:
                    vision_batch_size = min(10, total_frames)
                    logger.info(f"帧数较少({total_frames}帧)，调整批处理大小为{vision_batch_size}")
                
                logger.info(f"开始视觉分析: 共{total_frames}帧，批处理大小={vision_batch_size}，预计{estimated_batches}个批次")
                update_progress(40, f"正在分析关键帧 ({total_frames}帧，预计{estimated_batches}个批次)...")

                # ===================创建异步事件循环===================
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                vision_analysis_prompt = """
我提供了 %s 张视频帧，它们按时间顺序排列，代表一个连续的视频片段。请仔细分析每一帧的内容，并关注帧与帧之间的变化，以理解整个片段的活动。

**关键要求（必须严格遵守）**：
1. **真实客观**：只能描述画面里看得见的内容，严禁猜测或沿用模板经验。
2. **动物识别**：
   - 请结合体型、毛色、花纹、耳朵形状、尾巴形状、是否有胡须/条纹/爪子等特征来判断具体动物种类。
   - 例如：松鼠/花栗鼠（条纹背、蓬松大尾巴、啃坚果）、兔子（长耳、短尾）、小猪（无条纹、扁平猪鼻子、皮肤粉色或灰色）、狗/猫（明显的吻部、爪子）。
   - **若无法百分百确认物种，务必描述外貌特征，不要随意写“小猪”“小狗”等农场动物。**
3. **行为与环境**：
   - 具体描述动物或人物正在做的动作（如“抱着坚果啃食”“低头舔水”“抬头张望”）。
   - 准确描述场景：森林、树桩、户外木桌、室内客厅、农场猪圈等。若场景不像养殖场，就不要写“猪圈、食槽”。
4. **严禁误判**：
   - 看到条纹背的小型啮齿动物时，不能写成“小猪”。
   - 如果画面显示自然森林或木桩，请写成“森林/林地/户外”，不要写成“水泥地面、养殖场”。
   - 如有疑问，可说明“不确定的物种，具备××特征”。比随意猜成农场动物更好。

首先，请详细描述每一帧的关键视觉信息（必须基于实际画面，严禁虚构）：
- **准确识别内容**：人物、动物、物体、场景类型
- **准确描述行为**：实际发生的动作和行为
- **准确描述环境**：实际地点和场景

然后，基于所有帧的分析，请用**简洁的语言**总结整个视频片段中发生的主要活动或事件流程（必须基于实际画面内容，不能虚构）。

请务必使用 JSON 格式输出你的结果。JSON 结构应如下：
{
  "frame_observations": [
    {
      "frame_number": 1,
      "observation": "准确描述每张视频帧中的实际内容：主要内容、人物/动物、动作和场景。必须基于实际画面，不能虚构。"
    },
    // ... 更多帧的观察 ...
  ],
  "overall_activity_summary": "基于实际画面总结的主要活动，保持简洁，不能虚构。"
}

请务必不要遗漏视频帧，我提供了 %s 张视频帧，frame_observations 必须包含 %s 个元素

请只返回 JSON 字符串，不要包含任何其他解释性文字。
                """
                # 格式化提示词，填充帧数量
                formatted_prompt = vision_analysis_prompt % (len(keyframe_files), len(keyframe_files), len(keyframe_files))
                
                # 添加带进度的批处理包装
                async def analyze_with_progress():
                    """带进度显示的批处理分析"""
                    all_results = []
                    batch_count = (len(keyframe_files) + vision_batch_size - 1) // vision_batch_size
                    
                    for batch_idx in range(0, len(keyframe_files), vision_batch_size):
                        batch_files = keyframe_files[batch_idx:batch_idx + vision_batch_size]
                        current_batch = batch_idx // vision_batch_size + 1
                        
                        # 更新进度
                        progress_pct = 40 + int((current_batch / batch_count) * 20)  # 40-60%
                        update_progress(progress_pct, f"正在分析第{current_batch}/{batch_count}批次 ({len(batch_files)}帧)...")
                        logger.info(f"处理批次 {current_batch}/{batch_count}: {len(batch_files)}张图片")
                        
                        try:
                            batch_result = None
                            max_retries = 2
                            for attempt in range(max_retries):
                                try:
                                    # 使用asyncio.wait_for添加超时控制
                                    batch_result = await asyncio.wait_for(
                                        analyzer.analyze_images(
                                            images=batch_files,
                                            prompt=formatted_prompt,
                                            batch_size=len(batch_files),  # 这个批次的实际大小
                                            timeout=600,
                                            retries=2
                                        ),
                                        timeout=600  # 10分钟超时
                                    )
                                    break
                                except asyncio.TimeoutError:
                                    logger.warning(f"批次{current_batch}在第{attempt + 1}次尝试时超时，正在重试...")
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(2)
                                        continue
                                    raise
                            if batch_result is None:
                                raise asyncio.TimeoutError()
                            
                            # analyzer.analyze_images返回List[Dict]，对于单个批次通常只有一个元素
                            # 处理返回结果
                            if isinstance(batch_result, list) and len(batch_result) > 0:
                                # 取第一个结果（单个批次应该只有一个结果）
                                batch_result_dict = batch_result[0] if isinstance(batch_result[0], dict) else {
                                    'batch_index': current_batch - 1,
                                    'response': str(batch_result[0]) if batch_result[0] else '',
                                    'images_processed': len(batch_files)
                                }
                                batch_result_dict['batch_index'] = current_batch - 1
                                all_results.append(batch_result_dict)
                            elif isinstance(batch_result, dict):
                                batch_result['batch_index'] = current_batch - 1
                                all_results.append(batch_result)
                            else:
                                logger.warning(f"批次{current_batch}返回格式异常: {type(batch_result)}")
                                # 尝试转换
                                all_results.append({
                                    'batch_index': current_batch - 1,
                                    'response': str(batch_result) if batch_result else '',
                                    'images_processed': len(batch_files)
                                })
                                
                        except asyncio.TimeoutError:
                            logger.error(f"批次{current_batch}处理超时（超过5分钟）")
                            all_results.append({
                                'batch_index': current_batch - 1,
                                'error': f'处理超时（超过5分钟），可能API响应过慢',
                                'images_processed': len(batch_files)
                            })
                        except Exception as e:
                            logger.error(f"批次{current_batch}处理失败: {str(e)}")
                            all_results.append({
                                'batch_index': current_batch - 1,
                                'error': str(e),
                                'images_processed': len(batch_files)
                            })
                        
                        # 批次间短暂停顿，避免API限流
                        if current_batch < batch_count:
                            await asyncio.sleep(0.5)
                    
                    return all_results
                
                try:
                    results = loop.run_until_complete(analyze_with_progress())
                except Exception as e:
                    logger.exception(f"视觉分析API调用失败: {str(e)}")
                    raise Exception(f"视觉分析API调用失败: {str(e)}\n\n请检查：\n1. API配置是否正确\n2. 网络连接是否正常\n3. API密钥是否有效\n4. 如果长时间无响应，可能是API服务异常")
                finally:
                    loop.close()
                
                # 验证results不为空
                if not results:
                    raise Exception("视觉分析未返回任何结果，可能API调用失败")
                
                # 统计成功和失败的批次
                success_count = sum(1 for r in results if 'error' not in r)
                error_count = sum(1 for r in results if 'error' in r)
                
                logger.info(f"视觉分析完成: 共{len(results)}个批次，成功{success_count}个，失败{error_count}个")
                update_progress(60, f"视觉分析完成 ({success_count}/{len(results)}批次成功)")
                
                if error_count > 0 and success_count == 0:
                    # 所有批次都失败了
                    error_messages = [r.get('error', '未知错误') for r in results if 'error' in r]
                    raise Exception(f"所有批次处理失败。错误信息: {error_messages[0] if error_messages else '未知错误'}")

                """
                3. 处理分析结果（格式化为 json 数据）
                """
                # ===================处理分析结果===================
                update_progress(60, "正在整理分析结果...")

                # 合并所有批次的分析结果
                frame_analysis = ""
                merged_frame_observations = []  # 合并所有批次的帧观察
                overall_activity_summaries = []  # 合并所有批次的整体总结
                prev_batch_files = None
                frame_counter = 1  # 初始化帧计数器，用于给所有帧分配连续的序号
                
                # 确保分析目录存在
                analysis_dir = os.path.join(utils.storage_dir(), "temp", "analysis")
                os.makedirs(analysis_dir, exist_ok=True)
                origin_res = os.path.join(analysis_dir, "frame_analysis.json")
                with open(origin_res, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                # 开始处理
                for result in results:
                    if 'error' in result:
                        logger.warning(f"批次 {result['batch_index']} 处理出现警告: {result['error']}")
                        continue
                        
                    # 获取当前批次的文件列表
                    batch_files = get_batch_files(keyframe_files, result, vision_batch_size)
                    
                    # 获取批次的时间戳范围
                    first_timestamp, last_timestamp, timestamp_range = get_batch_timestamps(batch_files, prev_batch_files)
                    
                    # 解析响应中的JSON数据
                    response_text = result['response']
                    try:
                        # 处理可能包含```json```格式的响应
                        if "```json" in response_text:
                            json_content = response_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in response_text:
                            json_content = response_text.split("```")[1].split("```")[0].strip()
                        else:
                            json_content = response_text.strip()
                            
                        response_data = json.loads(json_content)
                        
                        # 提取frame_observations和overall_activity_summary
                        if "frame_observations" in response_data:
                            frame_obs = response_data["frame_observations"]
                            overall_summary = response_data.get("overall_activity_summary", "")
                            
                            # 添加时间戳信息到每个帧观察
                            for i, obs in enumerate(frame_obs):
                                if i < len(batch_files):
                                    # 从文件名中提取时间戳
                                    file_path = batch_files[i]
                                    file_name = os.path.basename(file_path)
                                    # 提取时间戳字符串 (格式如: keyframe_000675_000027000.jpg)
                                    # 格式解析: keyframe_帧序号_毫秒时间戳.jpg
                                    timestamp_parts = file_name.split('_')
                                    if len(timestamp_parts) >= 3:
                                        timestamp_str = timestamp_parts[-1].split('.')[0]
                                        try:
                                            # 修正时间戳解析逻辑
                                            # 格式为000100000，表示00:01:00,000，即1分钟
                                            # 需要按照对应位数进行解析:
                                            # 前两位是小时，中间两位是分钟，后面是秒和毫秒
                                            if len(timestamp_str) >= 9:  # 确保格式正确
                                                hours = int(timestamp_str[0:2])
                                                minutes = int(timestamp_str[2:4])
                                                seconds = int(timestamp_str[4:6])
                                                milliseconds = int(timestamp_str[6:9])
                                                
                                                # 计算总秒数
                                                timestamp_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
                                                formatted_time = utils.format_time(timestamp_seconds)  # 格式化时间戳
                                            else:
                                                # 兼容旧的解析方式
                                                timestamp_seconds = int(timestamp_str) / 1000  # 转换为秒
                                                formatted_time = utils.format_time(timestamp_seconds)  # 格式化时间戳
                                        except ValueError:
                                            logger.warning(f"无法解析时间戳: {timestamp_str}")
                                            timestamp_seconds = 0
                                            formatted_time = "00:00:00,000"
                                    else:
                                        logger.warning(f"文件名格式不符合预期: {file_name}")
                                        timestamp_seconds = 0
                                        formatted_time = "00:00:00,000"
                                    
                                    # 添加额外信息到帧观察
                                    obs["frame_path"] = file_path
                                    obs["timestamp"] = formatted_time
                                    obs["timestamp_seconds"] = timestamp_seconds
                                    obs["batch_index"] = result['batch_index']
                                    
                                    # 使用全局递增的帧计数器替换原始的frame_number
                                    if "frame_number" in obs:
                                        obs["original_frame_number"] = obs["frame_number"]  # 保留原始编号作为参考
                                    obs["frame_number"] = frame_counter  # 赋值连续的帧编号
                                    frame_counter += 1  # 增加帧计数器
                                    
                                    # 添加到合并列表
                                    merged_frame_observations.append(obs)
                            
                            # 添加批次整体总结信息
                            if overall_summary:
                                # 从文件名中提取时间戳数值
                                first_time_str = first_timestamp.split('_')[-1].split('.')[0]
                                last_time_str = last_timestamp.split('_')[-1].split('.')[0]
                                
                                # 转换为毫秒并计算持续时间（秒）
                                try:
                                    # 修正解析逻辑，与上面相同的方式解析时间戳
                                    if len(first_time_str) >= 9 and len(last_time_str) >= 9:
                                        # 解析第一个时间戳
                                        first_hours = int(first_time_str[0:2])
                                        first_minutes = int(first_time_str[2:4])
                                        first_seconds = int(first_time_str[4:6])
                                        first_ms = int(first_time_str[6:9])
                                        first_time_seconds = first_hours * 3600 + first_minutes * 60 + first_seconds + first_ms / 1000
                                        
                                        # 解析第二个时间戳
                                        last_hours = int(last_time_str[0:2])
                                        last_minutes = int(last_time_str[2:4])
                                        last_seconds = int(last_time_str[4:6])
                                        last_ms = int(last_time_str[6:9])
                                        last_time_seconds = last_hours * 3600 + last_minutes * 60 + last_seconds + last_ms / 1000
                                        
                                        batch_duration = last_time_seconds - first_time_seconds
                                    else:
                                        # 兼容旧的解析方式
                                        first_time_ms = int(first_time_str)
                                        last_time_ms = int(last_time_str)
                                        batch_duration = (last_time_ms - first_time_ms) / 1000
                                except ValueError:
                                    # 使用 utils.time_to_seconds 函数处理格式化的时间戳
                                    first_time_seconds = utils.time_to_seconds(first_time_str.replace('_', ':').replace('-', ','))
                                    last_time_seconds = utils.time_to_seconds(last_time_str.replace('_', ':').replace('-', ','))
                                    batch_duration = last_time_seconds - first_time_seconds
                                
                                overall_activity_summaries.append({
                                    "batch_index": result['batch_index'],
                                    "time_range": f"{first_timestamp}-{last_timestamp}",
                                    "duration_seconds": batch_duration,
                                    "summary": overall_summary
                                })
                    except Exception as e:
                        logger.error(f"解析批次 {result['batch_index']} 的响应数据失败: {str(e)}")
                        # 添加原始响应作为回退
                        frame_analysis += f"\n=== {first_timestamp}-{last_timestamp} ===\n"
                        frame_analysis += response_text
                        frame_analysis += "\n"
                    
                    # 更新上一个批次的文件
                    prev_batch_files = batch_files
                
                # 验证分析结果是否有效
                if not merged_frame_observations and not overall_activity_summaries:
                    logger.error("视觉分析未返回有效数据")
                    logger.error(f"分析结果详情: results数量={len(results)}, 包含错误的批次={sum(1 for r in results if 'error' in r)}")
                    
                    # 尝试诊断问题
                    error_details = []
                    for result in results:
                        if 'error' in result:
                            error_details.append(f"批次{result['batch_index']}: {result['error']}")
                        else:
                            # 检查响应内容
                            response_text = result.get('response', '')
                            if not response_text or not response_text.strip():
                                error_details.append(f"批次{result['batch_index']}: 响应为空")
                            elif "frame_observations" not in response_text:
                                error_details.append(f"批次{result['batch_index']}: 响应中缺少frame_observations字段")
                    
                    error_msg = "❌ 视频帧分析失败：未获取到有效的帧分析结果。\n\n"
                    error_msg += "**可能的原因：**\n"
                    error_msg += "1. 视觉分析API调用失败或返回错误\n"
                    error_msg += "2. API返回的JSON格式不符合预期\n"
                    error_msg += "3. 网络连接问题导致请求超时\n"
                    error_msg += "4. API密钥权限不足或已过期\n\n"
                    
                    if error_details:
                        error_msg += "**详细错误信息：**\n"
                        for detail in error_details[:5]:  # 最多显示5个错误
                            error_msg += f"- {detail}\n"
                    
                    error_msg += "\n**建议：**\n"
                    error_msg += "1. 检查视觉分析API配置是否正确（已测试连接成功不代表实际调用成功）\n"
                    error_msg += "2. 查看日志文件获取更详细的错误信息\n"
                    error_msg += "3. 尝试减少批处理大小（Batch Size）\n"
                    error_msg += "4. 检查网络连接和API配额\n"
                    
                    st.error(error_msg)
                    logger.exception("视频帧分析完整错误信息")
                    st.stop()
                    return
                
                # 将合并后的结果转为JSON字符串
                merged_results = {
                    "frame_observations": merged_frame_observations,
                    "overall_activity_summaries": overall_activity_summaries
                }
                
                logger.info(f"成功合并分析结果: {len(merged_frame_observations)}个帧观察, {len(overall_activity_summaries)}个总结")
                
                # 使用当前时间创建文件名
                now = datetime.now()
                timestamp_str = now.strftime("%Y%m%d_%H%M")
                
                # 保存完整的分析结果为JSON（关键修复：关联视频文件信息）
                analysis_filename = f"frame_analysis_{timestamp_str}.json"
                analysis_json_path = os.path.join(analysis_dir, analysis_filename)
                
                # 关键修复：在分析结果中添加视频文件信息，用于后续验证
                merged_results_with_video_info = {
                    **merged_results,
                    "video_file_path": video_path_normalized,
                    "video_file_hash": video_hash,
                    "analysis_timestamp": timestamp_str
                }
                
                with open(analysis_json_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_results_with_video_info, f, ensure_ascii=False, indent=2)
                logger.info(f"分析结果已保存到: {analysis_json_path} (关联视频: {video_path_normalized})")

                """
                4. 生成文案
                """
                logger.info("开始生成解说文案")
                update_progress(80, "正在生成解说文案（这可能需要1-2分钟）...")
                from app.services.generate_narration_script import parse_frame_analysis_to_markdown, generate_narration
                # 从配置中获取文本生成相关配置
                text_provider = config.app.get('text_llm_provider', 'gemini').lower()
                text_api_key = config.app.get(f'text_{text_provider}_api_key')
                text_model = config.app.get(f'text_{text_provider}_model_name')
                text_base_url = config.app.get(f'text_{text_provider}_base_url')
                llm_params.update({
                    "text_provider": text_provider,
                    "text_api_key": text_api_key,
                    "text_model_name": text_model,
                    "text_base_url": text_base_url
                })
                chekc_video_config(llm_params)
                # 整理帧分析数据（关键修复：验证分析结果是否属于当前视频）
                markdown_output = parse_frame_analysis_to_markdown(analysis_json_path)
                
                # 关键修复：验证分析结果是否属于当前视频文件
                try:
                    with open(analysis_json_path, 'r', encoding='utf-8') as f:
                        saved_analysis = json.load(f)
                    saved_video_path = saved_analysis.get('video_file_path', '')
                    saved_video_hash = saved_analysis.get('video_file_hash', '')
                    
                    if saved_video_path and saved_video_path != video_path_normalized:
                        logger.error(f"❌ 严重错误：分析结果文件关联的视频文件不匹配！\n"
                                   f"当前视频: {video_path_normalized}\n"
                                   f"分析结果关联的视频: {saved_video_path}")
                        st.error("❌ **严重错误：检测到分析结果与当前视频不匹配！**\n\n"
                                f"**当前视频文件**: `{os.path.basename(video_path_normalized)}`\n"
                                f"**分析结果关联的视频**: `{os.path.basename(saved_video_path)}`\n\n"
                                "这可能导致画面与解说不匹配！\n\n"
                                "**解决方案：**\n"
                                "1. 删除旧的缓存文件后重新生成\n"
                                "2. 点击系统设置中的'Clear frames'清理缓存\n"
                                "3. 重新点击'AI生成画面解说脚本'按钮")
                        st.stop()
                        return
                    
                    if saved_video_hash and saved_video_hash != video_hash:
                        logger.error(f"❌ 严重错误：分析结果文件的视频哈希不匹配！\n"
                                   f"当前视频哈希: {video_hash}\n"
                                   f"分析结果哈希: {saved_video_hash}")
                        st.error("❌ **严重错误：检测到分析结果与当前视频不匹配！**\n\n"
                                "视频文件可能已被修改或替换。\n\n"
                                "**解决方案：**\n"
                                "1. 清理缓存后重新生成\n"
                                "2. 重新点击'AI生成画面解说脚本'按钮")
                        st.stop()
                        return
                    
                    logger.info(f"✅ 验证通过：分析结果属于当前视频文件")
                except Exception as verify_error:
                    logger.warning(f"验证分析结果关联性时出错: {verify_error}，继续执行")
                
                # 验证markdown输出是否有效
                if not markdown_output or not markdown_output.strip():
                    logger.error("视频帧分析结果为空，无法生成解说文案")
                    st.error("❌ 视频帧分析失败：未获取到有效的帧分析结果。请检查：\n"
                            "1. 视频文件是否可正常读取\n"
                            "2. 视觉分析API配置是否正确\n"
                            "3. 网络连接是否正常\n"
                            "4. 是否已提取到关键帧")
                    st.stop()
                    return

                # 确定视频类型以选择正确的提示词
                # 策略：优先检查用户选择的模板，然后基于视频帧分析结果验证和自动识别
                video_type = None
                
                # 第一步：优先检查用户选择的模板类型（用户选择是最高优先级）
                script_path = st.session_state.get('video_clip_json_path', '')
                logger.info(f"检查用户选择的模板: {script_path}")
                
                if script_path and isinstance(script_path, str):
                    script_path_lower = script_path.lower()
                    if "动物世界" in script_path or "animal" in script_path_lower:
                        # 用户选择了动物世界模板，优先使用动物类型
                        video_type = "animal_world"
                        logger.info(f"✅ 用户选择了动物世界模板，优先使用animal_world类型")
                    elif "野外美食" in script_path or "outdoor" in script_path_lower:
                        video_type = "outdoor_food"
                    elif "影视解说" in script_path or "movie_commentary" in script_path_lower:
                        video_type = "movie_commentary"
                    elif "影视混剪" in script_path or "movie_mashup" in script_path_lower:
                        video_type = "movie_mashup"
                    elif "纪录片" in script_path or "documentary" in script_path_lower:
                        video_type = "documentary"
                
                # 第二步：基于视频帧分析结果自动识别或验证类型
                if merged_frame_observations and len(merged_frame_observations) > 0:
                    # 分析所有帧的观察结果，识别视频内容类型
                    sample_observations = []
                    for obs in merged_frame_observations[:20]:  # 增加样本量到20个帧
                        observation_text = obs.get('observation', '').lower()
                        if observation_text:
                            sample_observations.append(observation_text)
                    
                    combined_text = ' '.join(sample_observations)
                    logger.info(f"分析视频内容关键词（前500字符）: {combined_text[:500]}...")  # 记录更多内容用于调试
                    
                    # 扩展动物关键词，优先级最高
                    animal_keywords = [
                        '动物', '狮子', '草原', '森林', '猩猩', '野生动物', '捕食', '猎物',
                        '松鼠', '花栗鼠', 'chipmunk', 'squirrel', '条纹松鼠',
                        '猪', '小猪', '猪仔', '仔猪', '猪崽', '家猪', '野猪', '猪只',
                        '狗', '小狗', '猫', '小猫', '鸡', '鸭', '鹅', '牛', '羊', '马',
                        '鸟', '鱼', '鸟兽', '牲畜', '宠物', '家畜',
                        '进食', '吃食', '喂食', '觅食', '捕食', '吃东西', '吃饲料',
                        '大自然', '生态', '森林', '林地', '树桩', '木桩', '坚果', '木桌',
                        '农场', '养殖', '畜牧', '饲养',
                        '饲料', '食盆', '食槽', '猪圈', '鸡舍', '牛棚', '食桶'
                    ]
                    
                    food_keywords = ['厨房', '烹饪', '制作', '食材', '美食', '料理', '煮', '炒', '切', '操作台', '灶台', '调味', '调料']
                    
                    movie_keywords = ['电影', '演员', '角色', '剧情', '影片', '拍摄', '镜头']
                    
                    # 统计各类型关键词的出现次数
                    animal_count = sum(1 for keyword in animal_keywords if keyword in combined_text)
                    food_count = sum(1 for keyword in food_keywords if keyword in combined_text)
                    movie_count = sum(1 for keyword in movie_keywords if keyword in combined_text)
                    
                    logger.info(f"关键词统计: 动物={animal_count}, 美食={food_count}, 影视={movie_count}")
                    
                    # 如果没有从模板确定类型，基于内容自动识别
                    if not video_type:
                        # 优先级：动物 > 美食 > 影视 > 生活
                        if animal_count > 0:
                            video_type = "animal_world"
                            detected_keyword = next((kw for kw in animal_keywords if kw in combined_text), '动物相关')
                            logger.info(f"✅ 基于视频内容自动识别：动物世界类（检测到关键词：{detected_keyword}，出现{animal_count}次）")
                            st.info(f"🐷 **内容类型识别**：检测到视频包含动物内容（{detected_keyword}），已自动选择'动物世界'类型")
                        elif food_count > 0:
                            video_type = "outdoor_food"
                            logger.info(f"基于视频内容自动识别：美食/生活类（关键词出现{food_count}次）")
                        elif movie_count > 0:
                            video_type = "movie_commentary"
                            logger.info(f"基于视频内容自动识别：影视解说类")
                        elif any(keyword in combined_text for keyword in ['室内', '客厅', '沙发', '电视', '房间', '家庭']):
                            video_type = "documentary"
                            logger.info(f"基于视频内容自动识别：生活/纪录片类")
                    else:
                        # 如果已从模板确定类型，验证内容是否匹配
                        if video_type == "animal_world":
                            if animal_count == 0:
                                logger.warning(f"用户选择了动物世界模板，但视频内容中未检测到动物关键词")
                                # 不强制改类型，因为用户明确选择了动物世界模板
                                # 但给出警告
                                if food_count > 0 or any(keyword in combined_text for keyword in ['厨房', '烹饪', '制作']):
                                    st.warning(f"⚠️ **注意**：您选择了'动物世界'模板，但视频内容似乎包含美食相关内容。\n"
                                             f"如果视频实际是动物内容，请忽略此提示。\n"
                                             f"如果视频实际是美食内容，请选择对应的模板。")
                            else:
                                logger.info(f"✅ 用户选择的动物世界模板与视频内容匹配（检测到{animal_count}个动物关键词）")
                        elif video_type == "outdoor_food" and animal_count > food_count:
                            # 如果检测到更多动物关键词，给出警告
                            logger.warning(f"用户选择了美食模板，但视频内容中检测到更多动物关键词（动物:{animal_count} > 美食:{food_count}）")
                            st.warning(f"⚠️ **内容类型提示**：您选择了'野外美食'模板，但视频内容似乎包含更多动物相关内容。\n"
                                     f"如果视频实际是动物内容，请选择'动物世界'模板重新生成。")
                
                # 第三步：如果没有自动识别成功，使用默认类型
                if not video_type:
                    logger.info(f"无法基于视频内容自动识别，使用默认纪录片类型")
                    video_type = "documentary"
                
                logger.info(f"✅ 最终确定的视频类型: {video_type}")
                
                # 生成解说文案
                logger.info(f"使用视频类型 '{video_type}' 生成解说文案")
                update_progress(85, f"正在生成解说文案（视频类型：{video_type}）...")
                
                narration = generate_narration(
                    markdown_output,
                    text_api_key,
                    base_url=text_base_url,
                    model=text_model,
                    video_type=video_type
                )
                
                logger.info(f"解说文案生成完成，类型：{video_type}")

                # 使用增强的JSON解析器
                from webui.tools.generate_short_summary import parse_and_fix_json
                narration_data = parse_and_fix_json(narration)
                
                # 验证生成的解说是否与画面匹配
                if narration_data and 'items' in narration_data:
                    # 检查是否存在错误提示文案
                    error_keywords = [
                        '解说文案生成失败',
                        '生成失败:',
                        '视频帧分析未完成',
                        'API调用超时',
                        '请检查网络',
                        '错误信息:'
                    ]
                    for item in narration_data['items']:
                        narration_text = item.get('narration', '') or ''
                        if any(keyword in narration_text for keyword in error_keywords):
                            logger.error(f"解说文案生成失败，检测到错误信息: {narration_text}")
                            st.error("❌ **解说文案生成失败**：大模型返回了错误信息。\n\n"
                                     "请确认文本模型配置 / 网络状态，然后重新点击 'AI生成画面解说脚本'。")
                            st.stop()
                            return

                    mismatch_count = 0
                    mismatch_items = []
                    
                    for item in narration_data['items']:
                        picture = item.get('picture', '').lower()
                        narration = item.get('narration', '').lower()
                        
                        # 检查画面和解说的主题是否匹配
                        # 扩展检测范围：动物相关、生活场景、影视内容、美食等
                        animal_keywords_in_picture = ['动物', '松鼠', '花栗鼠', 'chipmunk', '条纹松鼠', '猪', '小猪', '狗', '猫', '鸡', '鸭', '进食', '吃食', '喂食', '坚果', '树桩', '木桩', '森林', '饲养', '农场', '养殖']
                        animal_keywords_in_narration = ['动物', '松鼠', '花栗鼠', 'chipmunk', '条纹松鼠', '猪', '小猪', '狗', '猫', '鸡', '鸭', '狮子', '草原', '森林', '猩猩', '野生动物', '捕食', '猎物', '大自然', '生态']
                        
                        life_keywords = ['室内', '客厅', '沙发', '电视', '房间', '厨房', '人物', '男子', '女子', '人', '拿水杯', '坐在']
                        movie_keywords = ['电影', '演员', '角色', '剧情', '影片', '拍摄']
                        food_keywords = ['烹饪', '制作', '食材', '美食', '料理', '煮', '炒']
                        
                        # 检测画面类型
                        is_picture_animal = any(keyword in picture.lower() for keyword in animal_keywords_in_picture)
                        is_picture_life = any(keyword in picture.lower() for keyword in life_keywords)
                        is_picture_movie = any(keyword in picture.lower() for keyword in movie_keywords)
                        is_picture_food = any(keyword in picture.lower() for keyword in food_keywords)
                        
                        # 检测解说类型
                        is_narration_animal = any(keyword in narration.lower() for keyword in animal_keywords_in_narration)
                        is_narration_life = any(keyword in narration.lower() for keyword in ['生活', '室内', '沙发', '电视'])
                        is_narration_movie = any(keyword in narration.lower() for keyword in movie_keywords)
                        is_narration_food = any(keyword in narration.lower() for keyword in food_keywords)
                        
                        # 不匹配情况1：画面是动物但解说不是
                        if is_picture_animal and not is_narration_animal:
                            mismatch_count += 1
                            mismatch_items.append({
                                'id': item.get('_id'),
                                'picture': item.get('picture', ''),
                                'narration': item.get('narration', ''),
                                'reason': '画面是动物内容，但解说不匹配'
                            })
                        # 不匹配情况2：画面是生活场景但解说是动物世界
                        elif is_picture_life and is_narration_animal:
                            mismatch_count += 1
                            mismatch_items.append({
                                'id': item.get('_id'),
                                'picture': item.get('picture', ''),
                                'narration': item.get('narration', ''),
                                'reason': '画面是生活场景，但解说是动物世界'
                            })
                        # 不匹配情况3：画面是动物但解说是其他类型
                        elif is_picture_animal and (is_narration_life or is_narration_movie or is_narration_food):
                            mismatch_count += 1
                            mismatch_items.append({
                                'id': item.get('_id'),
                                'picture': item.get('picture', ''),
                                'narration': item.get('narration', ''),
                                'reason': '画面是动物内容，但解说是其他类型'
                            })
                    
                    if mismatch_count > 0:
                        logger.warning(f"检测到{mismatch_count}个片段的画面与解说不匹配")
                        st.warning(f"⚠️ **内容不匹配警告**：\n\n"
                                 f"检测到 {mismatch_count} 个片段的解说与画面内容不匹配！\n"
                                 f"例如：画面描述的是生活场景，但解说却是动物世界的内容。\n\n"
                                 f"**可能原因：**\n"
                                 f"1. 选择的模板类型与视频实际内容不符\n"
                                 f"2. LLM生成了与模板相关但不符合实际画面的内容\n\n"
                                 f"**建议：**\n"
                                 f"1. 检查生成的脚本，确保每个片段的解说都与对应的画面匹配\n"
                                 f"2. 如果发现不匹配，请重新生成脚本\n"
                                 f"3. 如果视频内容与模板类型不符，请选择对应的模板类型")
                        
                        # 显示前3个不匹配的例子
                        if mismatch_items:
                            st.error("**不匹配示例：**")
                            for i, mismatch in enumerate(mismatch_items[:3], 1):
                                st.text(f"片段 {mismatch['id']}:\n"
                                       f"画面: {mismatch['picture'][:50]}...\n"
                                       f"解说: {mismatch['narration'][:50]}...")
                    else:
                        logger.info("画面与解说匹配验证通过")
                        st.success("✅ **内容匹配验证通过**：所有片段的解说都与画面内容匹配")

                if not narration_data or 'items' not in narration_data:
                    logger.error(f"解说文案JSON解析失败，原始内容: {narration[:200]}...")
                    raise Exception("解说文案格式错误，无法解析JSON或缺少items字段")

                narration_dict = narration_data['items']
                
                # 关键修复：确保picture字段从视频帧分析结果中正确提取
                # 如果LLM生成的picture为空或无效，从frame_observations中提取
                if merged_frame_observations:
                    # 创建时间戳到观察结果的映射
                    observation_map = {}
                    for obs in merged_frame_observations:
                        timestamp = obs.get('timestamp', '')
                        observation = obs.get('observation', '')
                        if timestamp and observation:
                            observation_map[timestamp] = observation
                    
                    # 为每个片段补充或修正picture字段
                    for item in narration_dict:
                        picture_value = item.get('picture', '').strip()
                        timestamp_range = item.get('timestamp', '')
                        
                        # 如果picture为空或无效，尝试从frame_observations中提取
                        if not picture_value or picture_value in ['$', '', '画面描述示例', '生成失败', '画面描述未提供']:
                            # 尝试从timestamp中提取起始时间
                            if timestamp_range and '-' in timestamp_range:
                                start_timestamp = timestamp_range.split('-')[0]
                                # 查找匹配的观察结果
                                matched_observation = None
                                for ts, obs in observation_map.items():
                                    if ts.startswith(start_timestamp.split(',')[0]):  # 匹配到秒级别
                                        matched_observation = obs
                                        break
                                
                                if matched_observation:
                                    item['picture'] = matched_observation
                                    logger.info(f"片段 {item.get('_id')} 的picture从frame_observations中提取: {matched_observation[:50]}...")
                                else:
                                    # 如果找不到匹配的，使用该批次的所有观察结果
                                    # 查找时间范围匹配的批次
                                    for summary in overall_activity_summaries:
                                        if timestamp_range and summary.get('time_range', '') in timestamp_range:
                                            # 使用总结作为picture
                                            item['picture'] = summary.get('summary', '画面描述未提供')
                                            logger.info(f"片段 {item.get('_id')} 的picture从summary中提取")
                                            break
                                    if not item.get('picture') or item['picture'] == '画面描述未提供':
                                        item['picture'] = "画面描述未提供，请检查视频帧分析结果"
                                        logger.warning(f"片段 {item.get('_id')} 无法从frame_observations中提取picture")
                
                # 为 narration_dict 中每个 item 新增一个 OST: 2 的字段, 代表保留原声和配音
                narration_dict = [{**item, "OST": 2} for item in narration_dict]
                logger.info(f"解说文案生成完成，共 {len(narration_dict)} 个片段")
                
                # 验证并确保每个片段都有必需的字段
                for i, item in enumerate(narration_dict):
                    # 确保_id存在且是整数
                    if '_id' not in item:
                        item['_id'] = i + 1
                    elif not isinstance(item['_id'], int):
                        try:
                            item['_id'] = int(item['_id'])
                        except:
                            item['_id'] = i + 1
                    
                    # 确保timestamp格式正确
                    if 'timestamp' not in item or not item['timestamp']:
                        logger.warning(f"片段 {item.get('_id', i+1)} 缺少timestamp，使用默认值")
                        item['timestamp'] = "00:00:00,000-00:00:05,000"
                    
                    # 确保picture存在且不是占位符
                    if 'picture' not in item or not item['picture'] or item['picture'].strip() in ['$', '', '画面描述示例', '生成失败']:
                        logger.warning(f"片段 {item.get('_id', i+1)} 的picture字段无效，使用默认值")
                        item['picture'] = "画面描述未提供"
                    
                    # 确保narration存在且不是占位符
                    if 'narration' not in item or not item['narration'] or '生成失败' in item['narration'] or '解说文案示例' in item['narration']:
                        logger.warning(f"片段 {item.get('_id', i+1)} 的narration字段无效")
                        if 'narration' not in item or not item['narration']:
                            item['narration'] = "解说文案未生成"
                    
                    # 确保OST存在且是整数
                    if 'OST' not in item:
                        item['OST'] = 2
                    elif not isinstance(item['OST'], int):
                        try:
                            item['OST'] = int(item['OST'])
                        except:
                            item['OST'] = 2
                
                # 结果转换为JSON字符串
                script = json.dumps(narration_dict, ensure_ascii=False, indent=2)
                
                # 自动保存脚本到文件（关键修复：确保脚本能被视频生成流程使用）
                script_dir = utils.script_dir()
                os.makedirs(script_dir, exist_ok=True)
                
                # 生成文件名（使用时间戳）
                timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
                script_filename = f"script_{timestamp}.json"
                script_file_path = os.path.join(script_dir, script_filename)
                
                # 保存脚本到文件
                try:
                    with open(script_file_path, 'w', encoding='utf-8') as f:
                        json.dump(narration_dict, f, ensure_ascii=False, indent=2)
                    logger.info(f"脚本已自动保存到: {script_file_path}")
                    
                    # 更新session_state中的脚本路径（关键：确保视频生成流程能找到脚本）
                    st.session_state['video_clip_json_path'] = script_file_path
                    params.video_clip_json_path = script_file_path
                    logger.info(f"脚本路径已更新: {script_file_path}")
                except Exception as save_error:
                    logger.error(f"保存脚本文件失败: {save_error}")
                    st.warning(f"⚠️ 脚本已生成，但保存文件时出错: {save_error}。请手动保存脚本。")

            except Exception as e:
                logger.exception(f"大模型处理过程中发生错误\n{traceback.format_exc()}")
                raise Exception(f"分析失败: {str(e)}")

            if script is None:
                st.error("生成脚本失败，请检查日志")
                st.stop()
            logger.info(f"纪录片解说脚本生成完成")
            if isinstance(script, list):
                st.session_state['video_clip_json'] = script
            elif isinstance(script, str):
                st.session_state['video_clip_json'] = json.loads(script)
            update_progress(100, "脚本生成完成")

        time.sleep(0.1)
        progress_bar.progress(100)
        status_text.text("🎉 脚本生成完成！")
        st.success("✅ 视频脚本生成成功！")
        # 刷新页面以显示生成的脚本
        time.sleep(1)  # 给用户一点时间看到成功消息
        st.rerun()

    except Exception as err:
        st.error(f"❌ 生成过程中发生错误: {str(err)}")
        logger.exception(f"生成脚本时发生错误\n{traceback.format_exc()}")
    finally:
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()
