import streamlit as st
import os
import shutil
import glob
from loguru import logger

from app.utils.utils import storage_dir


def clear_directory(dir_path, tr):
    """清理指定目录"""
    if os.path.exists(dir_path):
        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    logger.error(f"Failed to delete {item_path}: {e}")
            st.success(tr("Directory cleared"))
            logger.info(f"Cleared directory: {dir_path}")
        except Exception as e:
            st.error(f"{tr('Failed to clear directory')}: {str(e)}")
            logger.error(f"Failed to clear directory {dir_path}: {e}")
    else:
        st.warning(tr("Directory does not exist"))

def render_system_panel(tr):
    """渲染系统设置面板"""
    with st.expander(tr("System settings"), expanded=False):
        col1, col2, col3, col4 = st.columns(4)
                
        with col1:
            if st.button(tr("Clear frames"), use_container_width=True):
                clear_directory(os.path.join(storage_dir(), "temp/keyframes"), tr)
                
        with col2:
            if st.button(tr("Clear clip videos"), use_container_width=True):
                clear_directory(os.path.join(storage_dir(), "temp/clip_video"), tr)
                
        with col3:
            if st.button(tr("Clear tasks"), use_container_width=True):
                clear_directory(os.path.join(storage_dir(), "tasks"), tr)
        
        with col4:
            # 新增：清理分析结果缓存
            if st.button("清理分析结果", use_container_width=True, help="清理所有视频帧分析结果缓存"):
                analysis_dir = os.path.join(storage_dir(), "temp", "analysis")
                if os.path.exists(analysis_dir):
                    analysis_files = glob.glob(os.path.join(analysis_dir, "frame_analysis_*.json"))
                    analysis_files.append(os.path.join(analysis_dir, "frame_analysis.json"))
                    cleared_count = 0
                    for analysis_file in analysis_files:
                        if os.path.exists(analysis_file):
                            try:
                                os.remove(analysis_file)
                                cleared_count += 1
                            except Exception as e:
                                logger.error(f"删除分析结果文件失败: {e}")
                    if cleared_count > 0:
                        st.success(f"✅ 已清理 {cleared_count} 个分析结果文件")
                    else:
                        st.info("没有找到需要清理的分析结果文件")
                else:
                    st.info("分析结果目录不存在")
        
        # 新增：一键清理所有缓存
        st.divider()
        if st.button("🗑️ 一键清理所有缓存", use_container_width=True, type="primary", 
                    help="清理所有缓存（关键帧、分析结果、剪辑视频等），解决画面与解说不匹配问题"):
            cleared_items = []
            
            # 清理关键帧
            keyframes_dir = os.path.join(storage_dir(), "temp/keyframes")
            if os.path.exists(keyframes_dir):
                try:
                    shutil.rmtree(keyframes_dir)
                    os.makedirs(keyframes_dir, exist_ok=True)
                    cleared_items.append("关键帧缓存")
                except Exception as e:
                    logger.error(f"清理关键帧缓存失败: {e}")
            
            # 清理分析结果
            analysis_dir = os.path.join(storage_dir(), "temp", "analysis")
            if os.path.exists(analysis_dir):
                analysis_files = glob.glob(os.path.join(analysis_dir, "frame_analysis_*.json"))
                analysis_files.append(os.path.join(analysis_dir, "frame_analysis.json"))
                count = 0
                for analysis_file in analysis_files:
                    if os.path.exists(analysis_file):
                        try:
                            os.remove(analysis_file)
                            count += 1
                        except Exception as e:
                            logger.error(f"删除分析结果文件失败: {e}")
                if count > 0:
                    cleared_items.append(f"{count} 个分析结果文件")
            
            # 清理剪辑视频
            clip_video_dir = os.path.join(storage_dir(), "temp/clip_video")
            if os.path.exists(clip_video_dir):
                try:
                    shutil.rmtree(clip_video_dir)
                    os.makedirs(clip_video_dir, exist_ok=True)
                    cleared_items.append("剪辑视频缓存")
                except Exception as e:
                    logger.error(f"清理剪辑视频缓存失败: {e}")
            
            if cleared_items:
                st.success(f"✅ 已清理: {', '.join(cleared_items)}")
                st.info("💡 **提示**：请重新点击'AI生成画面解说脚本'按钮生成新脚本")
            else:
                st.info("没有找到需要清理的缓存文件")
