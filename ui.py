import streamlit as st
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlunparse, quote

class StreamlitUI:
    def __init__(self):
        self._set_page_config()
        self._set_css()

    def _set_page_config(self):
        st.set_page_config(
            page_title="AI Document Intelligence Platform",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def _set_css(self):
        st.markdown("""
        <style>
            .analysis-box {
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1rem 0;
                border: 2px solid #4CAF50;
                background-color: #ffffff;
            }
            .doc-intel-card {
                padding: 1rem 1.1rem;
                border-radius: 12px;
                margin: 1rem 0;
                background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
                border: 1px solid #dbeafe;
            }
            .doc-intel-pill {
                display: inline-block;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: #2563eb;
                color: white;
                font-size: 0.8rem;
                font-weight: 700;
                margin-bottom: 0.6rem;
            }
            .doc-intel-title {
                font-size: 1.15rem;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 0.35rem;
            }
            .doc-intel-summary {
                color: #334155;
                line-height: 1.6;
            }
            .doc-section-card {
                padding: 0.85rem 0.95rem;
                border-radius: 10px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                margin: 0.6rem 0;
            }
            .doc-section-title {
                font-weight: 700;
                color: #1d4ed8;
                margin-bottom: 0.35rem;
            }
            .doc-section-body {
                color: #334155;
                line-height: 1.6;
            }
            .resource-card {
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 12px;
                background: #111827;
                border: 1px solid #374151;
                box-shadow: 0 2px 8px rgba(0,0,0,0.25);
                color: #e5e7eb;
            }
            .resource-card a {
                color: #d1d5db;
                text-decoration: none;
            }
            .resource-card a:hover {
                color: #ffffff;
                text-decoration: underline;
            }
            .resource-card .resource-title {
                margin: 0 0 0.25rem 0;
                font-size: 1.1rem;
                font-weight: 700;
                color: #f8fafc;
            }
            .resource-card .resource-url {
                display: block;
                margin-bottom: 0.5rem;
                color: #9ca3af;
                font-size: 0.92rem;
            }
            .resource-card .resource-snippet {
                color: #d1d5db;
                font-size: 0.92rem;
                line-height: 1.5;
                margin: 0;
            }
            .youtube-card {
                border-left: 4px solid #fb7185;
            }
            .web-card {
                border-left: 4px solid #60a5fa;
            }
            .analysis-header {
                color: #2E7D32;
                font-size: 1.3rem;
                margin-bottom: 1rem;
                font-weight: bold;
            }
            .text-response {
                background-color: #ffffff;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                border: 1px solid #e0e0e0;
                color: #333333;
                font-size: 1.1rem;
                line-height: 1.6;
            }
            .structured-answer {
                background-color: #f8fbf8;
                border: 1px solid #c8e6c9;
                border-radius: 10px;
                padding: 1rem;
                margin: 0.75rem 0;
            }
            .structured-label {
                font-weight: 700;
                color: #2E7D32;
                margin-bottom: 0.25rem;
            }
            .chat-message {
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                color: #333333;
            }
            .stTextInput > div > div > input {
                color: #333333;
                font-size: 1.1rem;
            }
            .stTextArea > div > div > textarea {
                color: #333333;
                font-size: 1.1rem;
            }
        </style>
        """, unsafe_allow_html=True)

    def navigation(self):
        st.sidebar.title("Navigation")
        return st.sidebar.radio(
            "Select Mode",
            ["Document Analysis", "Quiz Generator", "Image Analysis"],
            index=0
        )

    def document_analysis_ui(self):
        st.title("📑 AI Document Intelligence Platform")
        
        # File uploader in a clean container
        with st.container():
            st.markdown("### Upload Documents")
            files = st.file_uploader(
                "Choose PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="doc_upload"
            )
            return files

    def quiz_generation_ui(self):
        st.title("🎯 PDF Quiz Generator")
        with st.expander("Upload Quiz Document", expanded=True):
            return st.file_uploader(
                "Choose a PDF file", 
                type=["pdf"]
            )

    def image_analysis_ui(self):
        st.title("🖼️ Image Extraction")
        with st.container():
            col1, col2 = st.columns([2, 3])
            with col1:
                image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"])
            with col2:
                user_query = st.text_area("Your Question/Instructions:", height=150)
            return image_file, user_query

    def show_processing_status(self, message):
        return st.status(f"{message}...", expanded=True)

    def summary_input(self):
        return st.text_input("Summary Focus Area:", placeholder="Leave blank for general summary")

    def display_document_intelligence(self, analysis: Optional[Dict]):
        if not analysis:
            return

        category = analysis.get("category", "Others")
        title = analysis.get("title") or f"{category} Analysis"
        summary = analysis.get("summary") or "The document was analyzed successfully."
        sections = analysis.get("sections", {}) or {}

        with st.container():
            st.markdown(f"""
            <div class="doc-intel-card">
                <div class="doc-intel-pill">{category}</div>
                <div class="doc-intel-title">{title}</div>
                <div class="doc-intel-summary">{self._escape_html(summary).replace(chr(10), '<br>')}</div>
            </div>
            """, unsafe_allow_html=True)

            for label, value in sections.items():
                if not value:
                    continue
                if isinstance(value, list):
                    body = "".join(f"<li>{self._escape_html(str(item))}</li>" for item in value if str(item).strip())
                    body_html = f"<ul>{body}</ul>" if body else ""
                else:
                    body_html = self._escape_html(str(value)).replace(chr(10), '<br>')

                st.markdown(f"""
                <div class="doc-section-card">
                    <div class="doc-section-title">{self._escape_html(str(label))}</div>
                    <div class="doc-section-body">{body_html}</div>
                </div>
                """, unsafe_allow_html=True)

    def display_summary(self, summary: str, links: List[Dict]):
        with st.container():
            st.markdown("""<div class="analysis-box"><div class="analysis-header">📝 Document Summary</div>""", 
                      unsafe_allow_html=True)
            st.markdown(summary)
            st.markdown("</div>", unsafe_allow_html=True)

    def _display_links(self, links: List[Dict]):
        for link in links:
            if not link.get('title') or not link.get('url'):
                continue
            card_class = "youtube-card" if link.get('type') == 'youtube' else 'web-card'
            st.markdown(f"""
            <div class="resource-card {card_class}">
                <div class="resource-title">{link.get('title')}</div>
                <div class="resource-url">{link.get('url')}</div>
                <div class="resource-snippet">{link.get('snippet', '')}</div>
            </div>
            """, unsafe_allow_html=True)

    def display_chat_message(self, entry: Dict):
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            self._render_structured_answer(entry["answer"])
            self._source_badge(entry["source"], entry.get("links", []))
            self._display_resource_links(entry.get("links", []))

    def _render_structured_answer(self, answer: str):
        try:
            sections = {
                "Short Answer": "",
                "Evidence": "",
                "Source": "",
                "Notes": ""
            }
            lines = [line.strip() for line in answer.splitlines() if line.strip()]
            current_key = None

            for line in lines:
                if line.startswith("Short Answer:"):
                    current_key = "Short Answer"
                    sections[current_key] = line.replace("Short Answer:", "", 1).strip()
                elif line.startswith("Evidence:"):
                    current_key = "Evidence"
                    sections[current_key] = line.replace("Evidence:", "", 1).strip()
                elif line.startswith("Source:"):
                    current_key = "Source"
                    sections[current_key] = line.replace("Source:", "", 1).strip()
                elif line.startswith("Notes:"):
                    current_key = "Notes"
                    sections[current_key] = line.replace("Notes:", "", 1).strip()
                elif current_key:
                    sections[current_key] += ("\n" if sections[current_key] else "") + line

            rendered = False
            for key in ["Short Answer", "Evidence", "Source", "Notes"]:
                if sections[key].strip():
                    rendered = True
                    st.markdown(f"""
                    <div class="structured-answer">
                        <div class="structured-label">{key}</div>
                        <div>{sections[key].replace(chr(10), '<br>')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            if not rendered:
                st.markdown(answer)
        except Exception:
            st.markdown(answer)

    def _source_badge(self, source: str, links: List[Dict]):
        badge_color = "#2E86C1" if source == "pdf" else "#27AE60"
        st.markdown(f'<div style="display: inline-block; padding: 0.25rem 0.75rem; margin: 0.5rem 0; border-radius: 15px; background-color: {badge_color}; color: white;">{source.upper()}</div>', 
                   unsafe_allow_html=True)


    def _display_resource_links(self, links: List[Dict]):
        valid_links = [link for link in links if link.get('title') and link.get('url')]
        for link in valid_links:
            self._display_single_link(link)

    def _display_single_link(self, link: Dict):
        try:
            icon = "🎥" if link.get('type') == 'youtube' else "🌐"
            source_type = "YouTube Video" if link.get('type') == 'youtube' else "Web Article"
            encoded_url = self._validate_url(link['url'])
            card_class = 'youtube-card' if link.get('type') == 'youtube' else 'web-card'
            title = link.get('title', 'Resource')
            snippet = self._truncate_text(link.get('snippet', ''), 200)

            st.markdown(f"""
            <div class="resource-card {card_class}">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <div style="font-size: 1.2rem;">{icon}</div>
                    <div><b>{source_type}</b></div>
                </div>
                <a href="{encoded_url}" target="_blank" rel="noopener noreferrer" class="resource-title">
                    {title}
                </a>
                <div class="resource-url">{encoded_url}</div>
                <div class="resource-snippet">{snippet}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying resource: {str(e)}")

    def _validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        safe_path = quote(parsed.path)
        return urlunparse((
            parsed.scheme or 'https',
            parsed.netloc,
            safe_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

    def _truncate_text(self, text: str, max_length: int) -> str:
        return text[:max_length-3] + '...' if len(text) > max_length else text

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    
    def display_image_analysis(self, text_response: Optional[str] = None, query: Optional[str] = None):
        """Display extracted image text with optional query context"""
        with st.container():
            if text_response:
                st.markdown("""
                <div class="analysis-box">
                    <div class="analysis-header">📄 Extracted Text</div>
                    <div class="content">
                """, unsafe_allow_html=True)
                
                if query:
                    st.markdown(f"**Your Question:** {query}")
                    st.markdown("---")
                
                st.markdown(f'<div class="text-response">{text_response}</div>', 
                          unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)































# import streamlit as st

# class StreamlitUI:
#     def __init__(self):
#         self._set_page_config()
#         self._set_css()

#     def _set_page_config(self):
#         st.set_page_config(
#             page_title="Smart Document Analyzer",
#             page_icon="🤖",
#             layout="wide",
#             initial_sidebar_state="expanded"
#         )

#     def _set_css(self):
#         st.markdown("""
#         <style>
#             .analysis-box {
#                 padding: 1.5rem;
#                 border-radius: 10px;
#                 margin: 1rem 0;
#                 border: 2px solid #4CAF50;
#                 background-color: #f0f4f8;
#             }
#             .analysis-header {
#                 color: #2E7D32;
#                 font-size: 1.3rem;
#                 margin-bottom: 1rem;
#             }
#             .text-response {
#                 background-color: #fff3e0;
#                 padding: 1rem;
#                 border-radius: 8px;
#                 margin: 1rem 0;
#             }
#             .status-box {
#                 padding: 1rem;
#                 border-radius: 0.5rem;
#                 margin: 1rem 0;
#                 background-color: #f8f9fa;
#                 border: 1px solid #dee2e6;
#             }
#             @keyframes fadeIn {
#                 from { opacity: 0; }
#                 to { opacity: 1; }
#             }
#         </style>
#         """, unsafe_allow_html=True)

#     def navigation(self):
#         st.sidebar.title("Navigation")
#         return st.sidebar.radio(
#             "Select Mode",
#             ["Document Analysis", "Quiz Generator", "Image Analysis"],
#             index=0,
#             key="nav_radio"
#         )

#     def document_analysis_ui(self):
#         st.title("📑 Smart Document Analyzer")
#         with st.expander("Upload Documents", expanded=True):
#             return st.file_uploader(
#                 "Choose PDF files", 
#                 type=["pdf"], 
#                 accept_multiple_files=True,
#                 key="doc_uploader",
#                 help="Upload one or multiple PDF documents for analysis"
#             )

#     def quiz_generation_ui(self):
#         st.title("🎯 PDF Quiz Generator")
#         with st.expander("Upload Quiz Document", expanded=True):
#             return st.file_uploader(
#                 "Choose a PDF file", 
#                 type=["pdf"],
#                 key="quiz_uploader",
#                 help="Upload a single PDF document to generate quiz questions"
#             )

#     def image_analysis_ui(self):
#         st.title("🖼️ Image Analysis")
#         with st.container():
#             col1, col2 = st.columns([2, 3])
            
#             with col1:
#                 image_file = st.file_uploader(
#                     "Upload Image",
#                     type=["png", "jpg", "jpeg", "webp"],
#                     key="image_uploader",
#                     help="Upload any image for analysis"
#                 )
#                 analysis_type = st.radio(
#                     "Analysis Mode:",
#                     ["Text Extraction", "Image Captioning"],
#                     index=0,
#                     key="analysis_mode"
#                 )
                
#             with col2:
#                 user_query = st.text_area(
#                     "Your Question/Instructions:",
#                     placeholder="What would you like to know about this image?",
#                     height=150,
#                     key="image_query"
#                 )
            
#             return image_file, user_query, analysis_type

#     def show_processing_status(self, message):
#         return st.status(f"{message}...", expanded=True)

#     def summary_input(self):
#         return st.text_input(
#             "Summary Focus Area:",
#             placeholder="Leave blank for general summary",
#             key="summary_focus"
#         )

#     def display_summary(self, summary):
#         with st.container():
#             st.markdown("""
#             <div class="analysis-box">
#                 <div class="analysis-header">📝 Document Summary</div>
#                 <div class="content">
#             """, unsafe_allow_html=True)
#             st.markdown(summary)
#             st.markdown("</div></div>", unsafe_allow_html=True)

#     def display_quiz(self, quiz_state):
#         total = len(quiz_state["quiz"])
#         current = quiz_state["current_question"]
        
#         if current < total:
#             question = quiz_state["quiz"][current]
#             st.markdown(f"""
#             <div class="analysis-box">
#                 <h3>Question {current+1}/{total}</h3>
#                 <p><strong>{question['question']}</strong></p>
#             </div>
#             """, unsafe_allow_html=True)
            
#             return st.radio(
#                 "Select your answer:",
#                 question["options"],
#                 key=f"quiz_question_{current}",
#                 index=None
#             )
#         else:
#             self._show_quiz_results(quiz_state["user_answers"], total)
#             return None

#     def display_image_analysis(self, text_response=None, caption=None, query=None):
#         """Display image analysis results with optional query context"""
#         with st.container():
#             if text_response:
#                 st.markdown("""
#                 <div class="analysis-box">
#                     <div class="analysis-header">📄 Analysis Results</div>
#                     <div class="content">
#                 """, unsafe_allow_html=True)
                
#                 if query:
#                     st.markdown(f"**Your Question:** {query}")
#                     st.markdown("---")
                
#                 st.markdown("#### Extracted Text")
#                 st.code(text_response.get('raw_text'))
                
#                 if text_response.get('processed_response'):
#                     st.markdown("---")
#                     st.markdown("#### Generated Response")
#                     st.markdown(text_response['processed_response'])
                
#                 st.markdown("</div></div>", unsafe_allow_html=True)
            
#             if caption:
#                 st.markdown("""
#                 <div class="analysis-box">
#                     <div class="analysis-header">📷 Generated Caption</div>
#                     <div class="content">
#                 """, unsafe_allow_html=True)
                
#                 if query:
#                     st.markdown(f"**Your Instruction:** {query}")
#                     st.markdown("---")
                
#                 st.markdown(caption)
#                 st.markdown("</div></div>", unsafe_allow_html=True)

#     def _show_quiz_results(self, user_answers, total):
#         correct = sum(1 for ans in user_answers if ans["selected"] == ans["correct"])
#         st.success(f"🎉 Quiz Complete! Score: {correct}/{total}")
#         st.progress(correct / total)
        
#         with st.expander("📝 Review Answers", expanded=True):
#             for i, ans in enumerate(user_answers):
#                 st.markdown(f"**Question {i+1}**")
#                 st.markdown(f"✅ **Correct:** {ans['correct']}")
#                 st.markdown(f"💡 **Your answer:** {ans['selected']}")
#                 st.divider()

#     def _source_badge(self, source):
#         badge_color = "#2E86C1" if source == "pdf" else "#27AE60"
#         st.markdown(
#             f'<div style="display: inline-block; padding: 0.25rem 0.75rem; '
#             f'margin-top: 0.5rem; border-radius: 15px; '
#             f'background-color: {badge_color}; color: white; '
#             f'font-size: 0.8rem;">{source.upper()}</div>',
#             unsafe_allow_html=True
#         )


















