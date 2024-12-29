import streamlit as st
import openai
from pathlib import Path
import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import re

load_dotenv()

# 提取视频 ID
def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)',
        r'youtube\.com\/shorts\/([\w-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# 获取字幕
def get_transcript(video_id, languages):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return ' '.join([item['text'] for item in transcript_list])
    except Exception as e:
        st.error(f"无法获取字幕: {str(e)}")
        return None

# 获取摘要
def get_summary(transcript):
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        client = openai.OpenAI(
            api_key=openai.api_key,
            base_url="https://urchin-app-tetq2.ondigitalocean.app/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "请用繁体中文总结以下内容，大约 2000 字:"},
                {"role": "user", "content": transcript}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API 错误: {str(e)}")
        return None

# 获取字幕提问的回答
def get_answer(question, transcript):
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        client = openai.OpenAI(
            api_key=openai.api_key,
            base_url="https://urchin-app-tetq2.ondigitalocean.app/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "请根据以下字幕内容回答问题。"},
                {"role": "user", "content": transcript},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API 错误: {str(e)}")
        return None

# 主函数
def main():
    st.title("YouTube 影片摘要工具")
    st.write("输入 YouTube 网页，获取影片内容摘要")

    # 添加 OpenAI API Key 输入框
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""

    api_key = st.text_input("请输入 OpenAI API Key:", type="password", value=st.session_state.api_key)
    if api_key:
        st.session_state.api_key = api_key
        os.environ['OPENAI_API_KEY'] = api_key

    # 添加上次输入的视频 URL
    if 'last_url' not in st.session_state:
        st.session_state.last_url = ""

    url = st.text_input("请输入 YouTube 网页:", value=st.session_state.last_url)

    # 添加语言选择下拉菜单
    language_options = {
        "中文 (繁体)": "zh-TW",
        "中文 (简体)": "zh-CN",
        "英文": "en",
        "西班牙文": "es",
        "法文": "fr",
        "德文": "de"
    }
    selected_language = st.selectbox("选择字幕语言:", list(language_options.keys()))

    if st.button("生成摘要"):
        if not api_key:
            st.warning("请先输入 OpenAI API Key")
            return
            
        if url:
            st.session_state.last_url = url  # 保存上次输入的 URL
            with st.spinner("处理中..."):
                # 获取影片 ID
                video_id = extract_video_id(url)
                if not video_id:
                    st.error("无效的 YouTube 网页")
                    return

                # 显示视频
                st.video(url)

                # 获取字幕
                transcript = get_transcript(video_id, [language_options[selected_language]])
                if transcript:
                    st.subheader("字幕内容")
                    st.text_area("完整字幕", transcript, height=200)

                    # 生成摘要
                    summary = get_summary(transcript)
                    if summary:
                        st.subheader("影片摘要")
                        st.write(summary)

                    # 提问功能
                    question = st.sidebar.text_input("对字幕提问:")
                    if st.sidebar.button("提问"):
                        if question:
                            answer = get_answer(question, transcript)
                            if answer:
                                st.sidebar.subheader("回答")
                                st.sidebar.write(answer)
                        else:
                            st.sidebar.warning("请输入你的问题")
        else:
            st.warning("请输入 YouTube 网页")

if __name__ == '__main__':
    main()