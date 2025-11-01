import streamlit as st
import os
import sys
from loguru import logger
from app.config import config
from webui.components import basic_settings, video_settings, audio_settings, subtitle_settings, script_settings, \
    system_settings
# from webui.utils import cache, file_utils
from app.utils import utils
from app.utils import ffmpeg_utils
from app.models.schema import VideoClipParams, VideoAspect


# 初始化配置 - 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="NarratoAI",
    page_icon="📽️",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Report a bug": "https://github.com/linyqh/NarratoAI/issues",
        'About': f"# Narrato:blue[AI] :sunglasses: 📽️ \n #### Version: v{config.project_version} \n "
                 f"自动化影视解说视频详情请移步：https://github.com/linyqh/NarratoAI"
    },
)

# 设置页面样式
hide_streamlit_style = """
<style>#root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 6px; padding-bottom: 10px; padding-left: 20px; padding-right: 20px;}</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def init_log():
    """初始化日志配置"""
    from loguru import logger
    logger.remove()
    _lvl = "INFO"  # 改为 INFO 级别，过滤掉 DEBUG 日志

    def format_record(record):
        # 简化日志格式化处理，不尝试按特定字符串过滤torch相关内容
        file_path = record["file"].path
        relative_path = os.path.relpath(file_path, config.root_dir)
        record["file"].path = f"./{relative_path}"
        record['message'] = record['message'].replace(config.root_dir, ".")

        _format = '<green>{time:%Y-%m-%d %H:%M:%S}</> | ' + \
                  '<level>{level}</> | ' + \
                  '"{file.path}:{line}":<blue> {function}</> ' + \
                  '- <level>{message}</>' + "\n"
        return _format

    # 添加日志过滤器
    def log_filter(record):
        """过滤不必要的日志消息"""
        # 过滤掉启动时的噪音日志（即使在 DEBUG 模式下也可以选择过滤）
        ignore_patterns = [
            "Examining the path of torch.classes raised",
            "torch.cuda.is_available()",
            "CUDA initialization"
        ]
        return not any(pattern in record["message"] for pattern in ignore_patterns)

    logger.add(
        sys.stdout,
        level=_lvl,
        format=format_record,
        colorize=True,
        filter=log_filter
    )

    # 应用启动后，可以再添加更复杂的过滤器
    def setup_advanced_filters():
        """在应用完全启动后设置高级过滤器"""
        try:
            for handler_id in logger._core.handlers:
                logger.remove(handler_id)

            # 重新添加带有高级过滤的处理器
            def advanced_filter(record):
                """更复杂的过滤器，在应用启动后安全使用"""
                ignore_messages = [
                    "Examining the path of torch.classes raised",
                    "torch.cuda.is_available()",
                    "CUDA initialization"
                ]
                return not any(msg in record["message"] for msg in ignore_messages)

            logger.add(
                sys.stdout,
                level=_lvl,
                format=format_record,
                colorize=True,
                filter=advanced_filter
            )
        except Exception as e:
            # 如果过滤器设置失败，确保日志仍然可用
            logger.add(
                sys.stdout,
                level=_lvl,
                format=format_record,
                colorize=True
            )
            logger.error(f"设置高级日志过滤器失败: {e}")

    # 将高级过滤器设置放到启动主逻辑后
    import threading
    threading.Timer(5.0, setup_advanced_filters).start()


def init_global_state():
    """初始化全局状态"""
    if 'video_clip_json' not in st.session_state:
        st.session_state['video_clip_json'] = []
    if 'video_plot' not in st.session_state:
        st.session_state['video_plot'] = ''
    if 'ui_language' not in st.session_state:
        st.session_state['ui_language'] = config.ui.get("language", utils.get_system_locale())
    # 移除subclip_videos初始化 - 现在使用统一裁剪策略


def tr(key):
    """翻译函数"""
    i18n_dir = os.path.join(os.path.dirname(__file__), "webui", "i18n")
    locales = utils.load_locales(i18n_dir)
    loc = locales.get(st.session_state['ui_language'], {})
    return loc.get("Translation", {}).get(key, key)


def render_generate_button():
    """渲染生成按钮和处理逻辑"""
    if st.button(tr("Generate Video"), use_container_width=True, type="primary"):
        from app.services import task as tm

        # 重置日志容器和记录
        log_container = st.empty()
        log_records = []

        def log_received(msg):
            with log_container:
                log_records.append(msg)
                st.code("\n".join(log_records))

        from loguru import logger
        logger.add(log_received)

        config.save_config()

        # 移除task_id检查 - 现在使用统一裁剪策略，不再需要预裁剪
        # 直接检查必要的文件是否存在
        if not st.session_state.get('video_clip_json_path'):
            st.error(tr("脚本文件不能为空"))
            return
        if not st.session_state.get('video_origin_path'):
            st.error(tr("视频文件不能为空"))
            return

        # 检查脚本内容（从session_state获取，更准确）
        script_json = st.session_state.get('video_clip_json', [])
        script_path = st.session_state.get('video_clip_json_path', '')
        
        if not script_json or len(script_json) == 0:
            st.error("❌ **脚本内容为空**\n\n请先加载脚本或使用'AI生成画面解说脚本'功能生成脚本")
            return
        
        # 验证脚本格式和内容
        try:
            import json
            from app.utils import check_script
            script_content = json.dumps(script_json, ensure_ascii=False)
            
            # 使用检查脚本功能验证（包含占位符检测）
            validation_result = check_script.check_format(script_content)
            if not validation_result.get('success'):
                error_msg = validation_result.get('message', '脚本验证失败')
                error_details = validation_result.get('details', '')
                
                st.error(f"**脚本验证失败：** {error_msg}")
                if error_details:
                    st.error(f"**详细说明：** {error_details}")
                
                # 如果是因为占位符问题，提供解决方案
                if '占位符' in error_msg:
                    st.info("""
                    **解决方案：**
                    1. 如果使用的是模板文件，请先点击 **"AI生成画面解说脚本"** 按钮
                    2. 等待AI生成真实的解说文案（会替换掉模板中的示例文字）
                    3. 生成完成后再点击 **"生成视频"** 按钮
                    
                    **重要提示：** 模板文件仅作为格式参考，不能直接用于生成视频！
                    """)
                return
                
            # 检查模板选择和脚本内容是否匹配（增强版，与generate_script_docu.py保持一致）
            if script_path and ("模板-" in script_path or "\\templates\\" in script_path or "/templates/" in script_path):
                # 检测脚本内容类型（分析所有片段，提高准确性）
                all_text = ""
                for item in script_json[:10]:  # 分析前10个片段
                    picture = item.get('picture', '').lower()
                    narration = item.get('narration', '').lower()
                    all_text += f" {picture} {narration}"
                
                # 扩展的关键词列表（与generate_script_docu.py保持一致）
                animal_keywords = [
                    '动物', '狮子', '草原', '森林', '猩猩', '野生动物', '捕食', '猎物',
                    '猪', '小猪', '猪仔', '仔猪', '猪崽', '家猪', '野猪', '猪只',
                    '狗', '小狗', '猫', '小猫', '鸡', '鸭', '鹅', '牛', '羊', '马',
                    '鸟', '鱼', '鸟兽', '牲畜', '宠物', '家畜',
                    '进食', '吃食', '喂食', '觅食', '捕食', '吃东西', '吃饲料',
                    '大自然', '生态', '农场', '养殖', '畜牧', '饲养',
                    '饲料', '食盆', '食槽', '猪圈', '鸡舍', '牛棚', '食桶'
                ]
                
                food_keywords = ['厨房', '烹饪', '制作', '食材', '美食', '料理', '煮', '炒', '切', '操作台', '灶台', '调味', '调料']
                movie_keywords = ['电影', '演员', '角色', '剧情', '影片', '拍摄', '镜头']
                
                # 统计各类型关键词的出现次数
                animal_count = sum(1 for keyword in animal_keywords if keyword in all_text)
                food_count = sum(1 for keyword in food_keywords if keyword in all_text)
                movie_count = sum(1 for keyword in movie_keywords if keyword in all_text)
                
                # 判断脚本内容类型（优先动物 > 美食 > 影视）
                script_type = "unknown"
                if animal_count > 0:
                    script_type = "animal"
                elif food_count > 0:
                    script_type = "food"
                elif movie_count > 0:
                    script_type = "movie"
                
                # 检查模板类型
                template_type = "unknown"
                script_path_lower = script_path.lower()
                if "野外美食" in script_path or "美食" in script_path or "outdoor" in script_path_lower:
                    template_type = "food"
                elif "动物世界" in script_path or "动物" in script_path or "animal" in script_path_lower:
                    template_type = "animal"
                elif "影视" in script_path or "movie" in script_path_lower:
                    template_type = "movie"
                elif "纪录片" in script_path or "documentary" in script_path_lower:
                    template_type = "documentary"
                
                # 如果类型不匹配且不是占位符，给出警告
                if script_type != "unknown" and template_type != "unknown" and script_type != template_type:
                    template_name = os.path.basename(script_path)
                    st.warning(f"⚠️ **模板与脚本内容不匹配**\n\n"
                             f"您选择的是 **'{template_name}'** 模板\n"
                             f"但脚本内容是 **{script_type}** 类型（检测到：动物={animal_count}次，美食={food_count}次，影视={movie_count}次）\n\n"
                             f"**建议：**\n"
                             f"1. 如果脚本是正确的，请选择对应的模板文件\n"
                             f"2. 如果想重新生成，请点击 **'AI生成画面解说脚本'** 按钮")
                    # 不阻止生成，只给出警告
                elif script_type == "unknown" and template_type != "unknown":
                    # 无法识别脚本类型，但模板类型明确，给出提示
                    template_name = os.path.basename(script_path)
                    logger.info(f"无法从脚本内容识别类型，但用户选择了模板：{template_name} ({template_type})")
                
        except Exception as e:
            logger.warning(f"脚本验证过程出错（继续执行）: {e}")

        st.toast(tr("生成视频"))
        logger.info(tr("开始生成视频"))

        # 获取所有参数
        script_params = script_settings.get_script_params()
        video_params = video_settings.get_video_params()
        audio_params = audio_settings.get_audio_params()
        subtitle_params = subtitle_settings.get_subtitle_params()

        # 合并所有参数
        all_params = {
            **script_params,
            **video_params,
            **audio_params,
            **subtitle_params
        }

        # 创建参数对象
        params = VideoClipParams(**all_params)

        # 使用新的统一裁剪策略，不再需要预裁剪的subclip_videos
        # 生成一个新的task_id用于本次处理
        import uuid
        task_id = str(uuid.uuid4())

        result = tm.start_subclip_unified(
            task_id=task_id,
            params=params
        )

        video_files = result.get("videos", [])
        st.success(tr("视生成完成"))

        try:
            if video_files:
                player_cols = st.columns(len(video_files) * 2 + 1)
                for i, url in enumerate(video_files):
                    player_cols[i * 2 + 1].video(url)
        except Exception as e:
            logger.error(f"播放视频失败: {e}")

        # file_utils.open_task_folder(config.root_dir, task_id)
        logger.info(tr("视频生成完成"))


def main():
    """主函数"""
    init_log()
    init_global_state()

    # ===== 显式注册 LLM 提供商（最佳实践）=====
    # 在应用启动时立即注册，确保所有 LLM 功能可用
    # 检查是否需要注册（避免重复注册，但确保提示词初始化）
    need_registration = 'llm_providers_registered' not in st.session_state or not st.session_state.get('llm_providers_registered', False) or 'prompts_registered' not in st.session_state
    if need_registration:
        try:
            from app.services.llm.providers import register_all_providers
            register_all_providers()
            st.session_state['llm_providers_registered'] = True
            logger.info("✅ LLM 提供商注册成功")
            
            # 注册提示词（必须在 LLM 提供商注册之后）
            try:
                from app.services.prompts import initialize_prompts
                initialize_prompts()
                st.session_state['prompts_registered'] = True
                logger.info("✅ 提示词注册成功")
            except Exception as prompt_error:
                error_msg = str(prompt_error)
                # 如果是版本已存在的错误，这是Streamlit重载的正常情况，不显示错误
                if "版本" in error_msg and "已存在" in error_msg:
                    logger.debug(f"提示词已注册（Streamlit重载时的正常情况）: {error_msg}")
                    st.session_state['prompts_registered'] = True  # 标记为已注册，因为实际上已经注册过了
                else:
                    logger.warning(f"提示词注册出现其他问题: {error_msg}")
                    st.session_state['prompts_registered'] = True  # 尝试继续运行
            
        except Exception as e:
            logger.error(f"❌ LLM 提供商注册失败: {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(error_traceback)
            
            # 检测常见错误类型并给出针对性提示
            error_msg = str(e)
            detailed_msg = f"⚠️ LLM 初始化失败: {error_msg}\n\n"
            
            if "ModuleNotFoundError" in error_msg or "No module named" in error_msg:
                detailed_msg += "**依赖缺失问题**：\n"
                detailed_msg += "1. 请运行 `pip install -r requirements.txt` 安装所有依赖\n"
                if "pyaudioop" in error_msg:
                    detailed_msg += "2. 如果使用 Python 3.13+，需要安装 audioop-lts：`pip install audioop-lts`\n"
                detailed_msg += "3. 安装完成后重启应用\n"
            elif "api_key" in error_msg.lower() or "api key" in error_msg.lower() or "key" in error_msg.lower():
                detailed_msg += "**配置问题**：\n"
                detailed_msg += "1. 请检查 `config.toml` 文件中的 API 密钥配置\n"
                detailed_msg += "2. 确保 `vision_litellm_api_key` 和 `text_litellm_api_key` 已正确填写\n"
                detailed_msg += "3. 参考 `config.example.toml` 查看配置示例\n"
            else:
                detailed_msg += "**请检查以下事项**：\n"
                detailed_msg += "1. 配置文件 `config.toml` 是否正确\n"
                detailed_msg += "2. 所有依赖是否已安装：`pip install -r requirements.txt`\n"
                detailed_msg += "3. Python 版本是否为 3.12+（推荐 3.12，3.13+ 需要额外安装 audioop-lts）\n"
            
            detailed_msg += f"\n**详细错误信息**：\n```\n{error_msg}\n```"
            st.error(detailed_msg)
            # 不抛出异常，允许应用继续运行（但 LLM 功能不可用）

    # 检测FFmpeg硬件加速，但只打印一次日志（使用 session_state 持久化）
    if 'hwaccel_logged' not in st.session_state:
        st.session_state['hwaccel_logged'] = False
    
    hwaccel_info = ffmpeg_utils.detect_hardware_acceleration()
    if not st.session_state['hwaccel_logged']:
        if hwaccel_info["available"]:
            logger.info(f"FFmpeg硬件加速检测结果: 可用 | 类型: {hwaccel_info['type']} | 编码器: {hwaccel_info['encoder']} | 独立显卡: {hwaccel_info['is_dedicated_gpu']}")
        else:
            logger.warning(f"FFmpeg硬件加速不可用: {hwaccel_info['message']}, 将使用CPU软件编码")
        st.session_state['hwaccel_logged'] = True

    # 仅初始化基本资源，避免过早地加载依赖PyTorch的资源
    # 检查是否能分解utils.init_resources()为基本资源和高级资源(如依赖PyTorch的资源)
    try:
        utils.init_resources()
    except Exception as e:
        logger.warning(f"资源初始化时出现警告: {e}")

    st.title(f"Narrato:blue[AI]:sunglasses: 📽️")
    st.write(tr("Get Help"))

    # 首先渲染不依赖PyTorch的UI部分
    # 渲染基础设置面板
    basic_settings.render_basic_settings(tr)

    # 渲染主面板
    panel = st.columns(3)
    with panel[0]:
        script_settings.render_script_panel(tr)
    with panel[1]:
        audio_settings.render_audio_panel(tr)
    with panel[2]:
        video_settings.render_video_panel(tr)
        subtitle_settings.render_subtitle_panel(tr)

    # 放到最后渲染可能使用PyTorch的部分
    # 渲染系统设置面板
    with panel[2]:
        system_settings.render_system_panel(tr)

    # 放到最后渲染生成按钮和处理逻辑
    render_generate_button()


if __name__ == "__main__":
    main()
