import os
import glob
import json
import time
import traceback
import shutil
import streamlit as st
from loguru import logger

from app.config import config
from app.models.schema import VideoClipParams
from app.utils import utils, check_script
from webui.tools.generate_script_docu import generate_script_docu
from webui.tools.generate_script_short import generate_script_short
from webui.tools.generate_short_summary import generate_script_short_sunmmary


def render_script_panel(tr):
    """渲染脚本配置面板"""
    with st.container(border=True):
        st.write(tr("Video Script Configuration"))
        params = VideoClipParams()

        # 渲染脚本文件选择
        render_script_file(tr, params)

        # 渲染视频文件选择
        render_video_file(tr, params)

        # 获取当前选择的脚本类型
        script_path = st.session_state.get('video_clip_json_path', '')

        # 根据脚本类型显示不同的布局
        if script_path == "auto":
            # 画面解说
            render_video_details(tr)
        elif script_path == "short":
            # 短剧混剪
            render_short_generate_options(tr)
        elif script_path == "summary":
            # 短剧解说
            short_drama_summary(tr)
        else:
            # 默认为空
            pass

        # 渲染脚本操作按钮
        render_script_buttons(tr, params)


def render_script_file(tr, params):
    """渲染脚本文件选择"""
    script_list = [
        (tr("None"), ""),
        (tr("Auto Generate"), "auto"),
        (tr("Short Generate"), "short"),
        (tr("Short Drama Summary"), "summary"),
        (tr("Upload Script"), "upload_script")
    ]

    # 获取已有脚本文件
    suffix = "*.json"
    script_dir = utils.script_dir()
    files = glob.glob(os.path.join(script_dir, suffix))
    file_list = []

    for file in files:
        file_list.append({
            "name": os.path.basename(file),
            "file": file,
            "ctime": os.path.getctime(file)
        })
        
    # 获取模板目录中的文件
    template_dir = os.path.join(config.root_dir, "resource", "templates")
    if os.path.exists(template_dir):
        template_files = glob.glob(os.path.join(template_dir, suffix))
        for file in template_files:
            file_list.append({
                "name": os.path.basename(file),
                "file": file,
                "ctime": os.path.getctime(file)
            })

    file_list.sort(key=lambda x: x["ctime"], reverse=True)
    for file in file_list:
        # 处理显示名称，去除路径前缀和文件扩展名
        full_path = file['file']
        # 去除根目录路径
        display_name = full_path.replace(config.root_dir, "")
        # 如果是模板文件，进一步简化显示名称
        if "\\templates\\" in display_name or "\\scripts\\模板-" in display_name:
            # 提取文件名并去除.json扩展名
            filename = os.path.basename(display_name)
            if filename.endswith('.json'):
                display_name = filename[:-5]  # 去除.json扩展名
        else:
            # 对于普通脚本文件，仍然显示相对路径
            display_name = full_path.replace(config.root_dir, "")
        script_list.append((display_name, full_path))

    # 找到保存的脚本文件在列表中的索引
    saved_script_path = st.session_state.get('video_clip_json_path', '')
    selected_index = 0
    for i, (_, path) in enumerate(script_list):
        if path == saved_script_path:
            selected_index = i
            break

    selected_script_index = st.selectbox(
        tr("Script Files"),
        index=selected_index,
        options=range(len(script_list)),
        format_func=lambda x: script_list[x][0],
        key="script_file_selectbox"
    )

    script_path = script_list[selected_script_index][1]
    previous_script_path = st.session_state.get('video_clip_json_path', '')
    
    # 如果脚本路径发生变化，清空旧的脚本内容
    if script_path != previous_script_path:
        # 清空旧的脚本内容，等待加载新的
        st.session_state['video_clip_json'] = []
        st.session_state['script_needs_generation'] = False
    
    st.session_state['video_clip_json_path'] = script_path
    params.video_clip_json_path = script_path
    
    # 如果选择了模板文件，给出提示
    if script_path and ("\\templates\\" in script_path or "模板-" in script_path or "/templates/" in script_path):
        st.info("📋 **模板文件提示：** 模板仅作为格式参考，请点击上方 **'AI生成画面解说脚本'** 按钮生成真实脚本")

    # 处理脚本上传
    if script_path == "upload_script":
        uploaded_file = st.file_uploader(
            tr("Upload Script File"),
            type=["json"],
            accept_multiple_files=False,
        )

        if uploaded_file is not None:
            try:
                # 读取上传的JSON内容并验证格式
                script_content = uploaded_file.read().decode('utf-8')
                json_data = json.loads(script_content)

                # 保存到脚本目录
                script_file_path = os.path.join(script_dir, uploaded_file.name)
                file_name, file_extension = os.path.splitext(uploaded_file.name)

                # 如果文件已存在,添加时间戳
                if os.path.exists(script_file_path):
                    timestamp = time.strftime("%Y%m%d%H%M%S")
                    file_name_with_timestamp = f"{file_name}_{timestamp}"
                    script_file_path = os.path.join(script_dir, file_name_with_timestamp + file_extension)

                # 写入文件
                with open(script_file_path, "w", encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                # 更新状态
                st.success(tr("Script Uploaded Successfully"))
                st.session_state['video_clip_json_path'] = script_file_path
                params.video_clip_json_path = script_file_path
                time.sleep(1)
                st.rerun()

            except json.JSONDecodeError:
                st.error(tr("Invalid JSON format"))
            except Exception as e:
                st.error(f"{tr('Upload failed')}: {str(e)}")


def render_video_file(tr, params):
    """渲染视频文件选择"""
    video_list = [(tr("None"), ""), (tr("Upload Local Files"), "upload_local")]

    # 获取已有视频文件
    for suffix in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
        video_files = glob.glob(os.path.join(utils.video_dir(), suffix))
        for file in video_files:
            display_name = file.replace(config.root_dir, "")
            video_list.append((display_name, file))

    selected_video_index = st.selectbox(
        tr("Video File"),
        index=0,
        options=range(len(video_list)),
        format_func=lambda x: video_list[x][0]
    )

    video_path = video_list[selected_video_index][1]
    previous_video_path = st.session_state.get('video_origin_path', '')
    
    # 关键修复：如果视频文件发生变化，清理旧的脚本和缓存
    if video_path != previous_video_path and previous_video_path:
        logger.info(f"视频文件已更改: {previous_video_path} -> {video_path}")
        # 清空旧的脚本内容
        st.session_state['video_clip_json'] = []
        st.session_state['video_clip_json_path'] = ''
        st.session_state['script_needs_generation'] = True
        # 清空旧的脚本路径
        params.video_clip_json_path = ''
        
        # 关键修复：清理旧视频的所有缓存（关键帧、分析结果）
        try:
            # 清理关键帧缓存
            keyframes_dir = os.path.join(utils.temp_dir(), "keyframes")
            if os.path.exists(keyframes_dir):
                try:
                    old_video_hash = None
                    if previous_video_path and os.path.exists(previous_video_path):
                        old_video_hash = utils.md5(
                            os.path.abspath(previous_video_path) + str(os.path.getmtime(previous_video_path))
                        )

                    if old_video_hash:
                        old_keyframes_dir = os.path.join(keyframes_dir, old_video_hash)
                        if os.path.exists(old_keyframes_dir):
                            shutil.rmtree(old_keyframes_dir)
                            logger.info(f"已删除旧视频的关键帧缓存: {old_keyframes_dir}")
                    else:
                        shutil.rmtree(keyframes_dir)
                        logger.info("旧视频文件不存在，已清空全部关键帧缓存目录")
                except Exception as e:
                    logger.warning(f"按哈希清理关键帧缓存失败，将清空整个缓存目录: {e}")
                    try:
                        shutil.rmtree(keyframes_dir)
                        logger.info("已清空关键帧缓存目录")
                    except Exception as remove_err:
                        logger.error(f"删除关键帧缓存目录失败: {remove_err}")

            # 清理分析结果缓存（直接清空目录，避免遗留）
            analysis_dir = os.path.join(utils.storage_dir(), "temp", "analysis")
            if os.path.exists(analysis_dir):
                try:
                    shutil.rmtree(analysis_dir)
                    logger.info("已清空分析结果缓存目录")
                except Exception as e:
                    logger.warning(f"删除分析结果缓存目录失败: {e}")
        except Exception as cleanup_error:
            logger.error(f"清理旧视频缓存时出错: {cleanup_error}")
        
        logger.info("已清空旧视频的脚本数据和路径")
        # 显示提示信息
        st.info("🔄 **检测到视频文件已更换**\n\n"
                "已自动清空旧视频的脚本数据和缓存。\n"
                "请点击 **'AI生成画面解说脚本'** 按钮为新视频生成脚本。")
    
    st.session_state['video_origin_path'] = video_path
    params.video_origin_path = video_path

    if video_path == "upload_local":
        uploaded_file = st.file_uploader(
            tr("Upload Local Files"),
            type=["mp4", "mov", "avi", "flv", "mkv"],
            accept_multiple_files=False,
        )

        if uploaded_file is not None:
            video_file_path = os.path.join(utils.video_dir(), uploaded_file.name)
            file_name, file_extension = os.path.splitext(uploaded_file.name)

            if os.path.exists(video_file_path):
                timestamp = time.strftime("%Y%m%d%H%M%S")
                file_name_with_timestamp = f"{file_name}_{timestamp}"
                video_file_path = os.path.join(utils.video_dir(), file_name_with_timestamp + file_extension)

            with open(video_file_path, "wb") as f:
                f.write(uploaded_file.read())
                st.success(tr("File Uploaded Successfully"))
                st.session_state['video_origin_path'] = video_file_path
                params.video_origin_path = video_file_path
                time.sleep(1)
                st.rerun()


def render_short_generate_options(tr):
    """
    渲染Short Generate模式下的特殊选项
    在Short Generate模式下，替换原有的输入框为自定义片段选项
    """
    short_drama_summary(tr)
    # 显示自定义片段数量选择器
    custom_clips = st.number_input(
        tr("自定义片段"),
        min_value=1,
        max_value=20,
        value=st.session_state.get('custom_clips', 5),
        help=tr("设置需要生成的短视频片段数量"),
        key="custom_clips_input"
    )
    st.session_state['custom_clips'] = custom_clips


def render_video_details(tr):
    """画面解说 渲染视频主题和提示词"""
    video_theme = st.text_input(tr("Video Theme"))
    custom_prompt = st.text_area(
        tr("Generation Prompt"),
        value=st.session_state.get('video_plot', ''),
        help=tr("Custom prompt for LLM, leave empty to use default prompt"),
        height=180
    )
    # 非短视频模式下显示原有的三个输入框
    input_cols = st.columns(2)

    with input_cols[0]:
        st.number_input(
            tr("Frame Interval (seconds)"),
            min_value=0,
            value=st.session_state.get('frame_interval_input', config.frames.get('frame_interval_input', 3)),
            help=tr("Frame Interval (seconds) (More keyframes consume more tokens)"),
            key="frame_interval_input"
        )

    with input_cols[1]:
        st.number_input(
            tr("Batch Size"),
            min_value=0,
            value=st.session_state.get('vision_batch_size', config.frames.get('vision_batch_size', 10)),
            help=tr("Batch Size (More keyframes consume more tokens)"),
            key="vision_batch_size"
        )
    st.session_state['video_theme'] = video_theme
    st.session_state['custom_prompt'] = custom_prompt
    return video_theme, custom_prompt


def short_drama_summary(tr):
    """短剧解说 渲染视频主题和提示词"""
    # 检查是否已经处理过字幕文件
    if 'subtitle_file_processed' not in st.session_state:
        st.session_state['subtitle_file_processed'] = False
    
    subtitle_file = st.file_uploader(
        tr("上传字幕文件"),
        type=["srt"],
        accept_multiple_files=False,
        key="subtitle_file_uploader"  # 添加唯一key
    )
    
    # 显示当前已上传的字幕文件路径
    if 'subtitle_path' in st.session_state and st.session_state['subtitle_path']:
        st.info(f"已上传字幕: {os.path.basename(st.session_state['subtitle_path'])}")
        if st.button(tr("清除已上传字幕")):
            st.session_state['subtitle_path'] = None
            st.session_state['subtitle_file_processed'] = False
            st.rerun()
    
    # 只有当有文件上传且尚未处理时才执行处理逻辑
    if subtitle_file is not None and not st.session_state['subtitle_file_processed']:
        try:
            # 读取上传的SRT内容
            script_content = subtitle_file.read().decode('utf-8')

            # 保存到字幕目录
            script_file_path = os.path.join(utils.subtitle_dir(), subtitle_file.name)
            file_name, file_extension = os.path.splitext(subtitle_file.name)

            # 如果文件已存在,添加时间戳
            if os.path.exists(script_file_path):
                timestamp = time.strftime("%Y%m%d%H%M%S")
                file_name_with_timestamp = f"{file_name}_{timestamp}"
                script_file_path = os.path.join(utils.subtitle_dir(), file_name_with_timestamp + file_extension)

            # 直接写入SRT内容，不进行JSON转换
            with open(script_file_path, "w", encoding='utf-8') as f:
                f.write(script_content)

            # 更新状态
            st.success(tr("字幕上传成功"))
            st.session_state['subtitle_path'] = script_file_path
            st.session_state['subtitle_file_processed'] = True  # 标记已处理
            
            # 避免使用rerun，使用更新状态的方式
            # st.rerun()
            
        except Exception as e:
            st.error(f"{tr('Upload failed')}: {str(e)}")

    # 名称输入框
    video_theme = st.text_input(tr("短剧名称"))
    st.session_state['video_theme'] = video_theme
    # 数字输入框
    temperature = st.slider("temperature", 0.0, 2.0, 0.7)
    st.session_state['temperature'] = temperature
    return video_theme


def render_script_buttons(tr, params):
    """渲染脚本操作按钮"""
    # 获取当前选择的脚本类型
    script_path = st.session_state.get('video_clip_json_path', '')

    # 生成/加载按钮
    if script_path == "auto":
        button_name = tr("Generate Video Script")
    elif script_path == "short":
        button_name = tr("Generate Short Video Script")
    elif script_path == "summary":
        button_name = tr("生成短剧解说脚本")
    elif script_path.endswith("json"):
        # 检查是否是模板文件，如果是则显示AI生成按钮
        if "\\templates\\" in script_path or "模板-" in script_path:
            # 根据模板文件名确定生成类型
            if "野外美食" in script_path:
                button_name = tr("Generate Video Script")  # 使用画面解说生成器
            elif "影视解说" in script_path:
                button_name = tr("Generate Video Script")  # 使用画面解说生成器
            elif "影视混剪" in script_path:
                button_name = tr("Generate Short Video Script")  # 使用短剧混剪生成器
            elif "动物世界" in script_path:
                button_name = tr("Generate Video Script")  # 使用画面解说生成器
            elif "纪录片" in script_path:
                button_name = tr("Generate Video Script")  # 使用画面解说生成器
            else:
                button_name = tr("Load Video Script")
        else:
            button_name = tr("Load Video Script")
    else:
        button_name = tr("Please Select Script File")

    if st.button(button_name, key="script_action", disabled=not script_path):
        if script_path == "auto":
            # 执行纪录片视频脚本生成（视频无字幕无配音）
            generate_script_docu(params)
        elif script_path == "short":
            # 执行 短剧混剪 脚本生成
            custom_clips = int(st.session_state.get('custom_clips', 5))  # 确保是整数类型
            generate_script_short(tr, params, custom_clips)
        elif script_path == "summary":
            # 执行 短剧解说 脚本生成
            subtitle_path = st.session_state.get('subtitle_path')
            video_theme = st.session_state.get('video_theme')
            temperature = st.session_state.get('temperature')
            generate_script_short_sunmmary(params, subtitle_path, video_theme, temperature)
        elif script_path.endswith("json") and ("\\templates\\" in script_path or "模板-" in script_path):
            # 处理模板文件的AI生成
            if "影视混剪" in script_path:
                # 影视混剪使用短剧混剪生成器
                custom_clips = int(st.session_state.get('custom_clips', 5))  # 确保是整数类型
                generate_script_short(tr, params, custom_clips)
            else:
                # 其他模板使用画面解说生成器
                generate_script_docu(params)
        else:
            # 加载脚本前，先清空旧的脚本内容
            st.session_state['video_clip_json'] = []
            load_script(tr, script_path)

    # 视频脚本编辑区
    video_clip_json_details = st.text_area(
        tr("Video Script"),
        value=json.dumps(st.session_state.get('video_clip_json', []), indent=2, ensure_ascii=False),
        height=500
    )

    # 操作按钮行 - 合并格式检查和保存功能
    if st.button(tr("Save Script"), key="save_script", use_container_width=True):
        save_script_with_validation(tr, video_clip_json_details)


def load_script(tr, script_path):
    """加载脚本文件"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()
            script = utils.clean_model_output(script)
            loaded_script = json.loads(script)
            
            # 检查是否是模板文件
            is_template = "\\templates\\" in script_path or "模板-" in script_path or "/templates/" in script_path
            
            if is_template:
                # 如果是模板文件，检查是否包含占位符
                from app.utils import check_script
                validation_result = check_script.check_format(json.dumps(loaded_script, ensure_ascii=False))
                
                if not validation_result.get('success'):
                    # 模板文件包含占位符，提示用户使用AI生成
                    error_msg = validation_result.get('message', '')
                    error_details = validation_result.get('details', '')
                    
                    st.warning("⚠️ **模板文件检测**")
                    st.info(f"**{error_msg}**\n\n{error_details}")
                    st.info("💡 **解决方案：**\n"
                           "1. 点击上方 **'AI生成画面解说脚本'** 按钮\n"
                           "2. 等待AI分析视频并生成真实脚本\n"
                           "3. 生成完成后再点击'生成视频'按钮")
                    
                    # 仍然加载模板，但标记为需要生成
                    st.session_state['video_clip_json'] = loaded_script
                    st.session_state['script_needs_generation'] = True
                    return
            
            # 普通脚本文件，直接加载
            st.session_state['video_clip_json'] = loaded_script
            st.session_state['script_needs_generation'] = False
            st.success(tr("Script loaded successfully"))
            st.rerun()
    except Exception as e:
        logger.error(f"加载脚本文件时发生错误\n{traceback.format_exc()}")
        st.error(f"{tr('Failed to load script')}: {str(e)}")


def save_script_with_validation(tr, video_clip_json_details):
    """保存视频脚本（包含格式验证）"""
    if not video_clip_json_details:
        st.error(tr("请输入视频脚本"))
        st.stop()

    # 第一步：格式验证
    with st.spinner("正在验证脚本格式..."):
        try:
            result = check_script.check_format(video_clip_json_details)
            if not result.get('success'):
                # 格式验证失败，显示详细错误信息
                error_message = result.get('message', '未知错误')
                error_details = result.get('details', '')

                st.error(f"**脚本格式验证失败**")
                st.error(f"**错误信息：** {error_message}")
                if error_details:
                    st.error(f"**详细说明：** {error_details}")

                # 显示正确格式示例
                st.info("**正确的脚本格式示例：**")
                example_script = [
                    {
                        "_id": 1,
                        "timestamp": "00:00:00,600-00:00:07,559",
                        "picture": "工地上，蔡晓艳奋力救人，场面混乱",
                        "narration": "灾后重建，工地上险象环生！泼辣女工蔡晓艳挺身而出，救人第一！",
                        "OST": 0
                    },
                    {
                        "_id": 2,
                        "timestamp": "00:00:08,240-00:00:12,359",
                        "picture": "领导视察，蔡晓艳不屑一顾",
                        "narration": "播放原片4",
                        "OST": 1
                    }
                ]
                st.code(json.dumps(example_script, ensure_ascii=False, indent=2), language='json')
                st.stop()

        except Exception as e:
            st.error(f"格式验证过程中发生错误: {str(e)}")
            st.stop()

    # 第二步：检查 picture 字段是否有占位符
    try:
        data = json.loads(video_clip_json_details)
        if isinstance(data, list):
            picture_warnings = []
            for i, item in enumerate(data, 1):
                picture_value = item.get('picture', '')
                # 检查是否为占位符或空值
                if not picture_value or picture_value.strip() in ['$', '', '画面描述示例', '画面描述', '画面描述示例：']:
                    picture_warnings.append((i, picture_value))
            
            if picture_warnings:
                warning_msg = f"⚠️ **警告：发现 {len(picture_warnings)} 个片段的 picture 字段为空或占位符**\n\n"
                warning_msg += "**受影响的片段编号**："
                for idx, val in picture_warnings:
                    warning_msg += f" {idx}"
                warning_msg += "\n\n"
                warning_msg += "**picture 字段说明**：\n"
                warning_msg += "- `picture` 字段用于描述视频画面内容，对视频剪辑非常重要\n"
                warning_msg += "- 如果使用模板文件，请点击 'AI生成画面解说脚本' 按钮自动填充\n"
                warning_msg += "- 或手动编辑，将占位符替换为实际的画面描述\n\n"
                warning_msg += "**示例**：\n"
                warning_msg += "- ❌ 错误：`\"picture\": \"$\"` 或 `\"picture\": \"画面描述示例\"`\n"
                warning_msg += "- ✅ 正确：`\"picture\": \"在遥远的非洲草原，一只狮子正在巡视领地\"`\n"
                st.warning(warning_msg)
    except:
        pass  # JSON 解析失败时跳过，格式验证会处理

    # 第三步：保存脚本
    with st.spinner(tr("Save Script")):
        script_dir = utils.script_dir()
        timestamp = time.strftime("%Y-%m%d-%H%M%S")
        save_path = os.path.join(script_dir, f"{timestamp}.json")

        try:
            data = json.loads(video_clip_json_details)
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                st.session_state['video_clip_json'] = data
                st.session_state['video_clip_json_path'] = save_path

                # 更新配置
                config.app["video_clip_json_path"] = save_path

                # 显示成功消息
                st.success("✅ 脚本格式验证通过，保存成功！")

                # 强制重新加载页面更新选择框
                time.sleep(0.5)  # 给一点时间让用户看到成功消息
                st.rerun()

        except Exception as err:
            st.error(f"{tr('Failed to save script')}: {str(err)}")
            st.stop()


# crop_video函数已移除 - 现在使用统一裁剪策略，不再需要预裁剪步骤


def get_script_params():
    """获取脚本参数"""
    return {
        'video_language': st.session_state.get('video_language', ''),
        'video_clip_json_path': st.session_state.get('video_clip_json_path', ''),
        'video_origin_path': st.session_state.get('video_origin_path', ''),
        'video_name': st.session_state.get('video_name', ''),
        'video_plot': st.session_state.get('video_plot', '')
    }
