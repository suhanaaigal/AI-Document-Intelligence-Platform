from urllib import response
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_groq import ChatGroq

from typing import Tuple, List, Dict, Any
import json
import logging
import re


logger = logging.getLogger(__name__)

class QASystem:
    def __init__(self, services):
        self.services = services
        # Optional services use get() to avoid KeyError when not configured
        self.search = services.get('search')
        self.embeddings = services.get('embeddings')
        self.youtube = services.get('youtube')

    def classify_document_and_analyze(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return self._build_fallback_analysis("Others", "No readable content found in the uploaded document.")

        try:
            llm = self.services.get("llm")
            if not llm:
                return self._build_fallback_analysis("Others", "AI service is currently unavailable.")

            response = llm.invoke(self._document_classification_prompt(text))
            content = response.content if hasattr(response, "content") else str(response)
            payload = self._extract_json_payload(content)

            if not payload:
                return self._build_fallback_analysis("Others", content[:600])

            return self._normalize_analysis_payload(payload)
        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            return self._build_fallback_analysis("Others", f"Classification failed: {str(e)}")

    def _build_fallback_analysis(self, category: str, summary: str) -> Dict[str, Any]:
        return {
            "category": category,
            "confidence": "low",
            "title": "Document Analysis",
            "summary": summary,
            "sections": {"Summary": summary}
        }

    def _normalize_analysis_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        category = str(payload.get("category", "Others")).strip() or "Others"
        if category not in self._category_sections():
            category = "Others"

        sections_raw = payload.get("sections") if isinstance(payload.get("sections"), dict) else {}
        default_sections = self._default_sections_for_category(category)
        normalized_sections = {}

        for key in default_sections:
            if key in sections_raw:
                normalized_sections[key] = sections_raw[key]

        if not normalized_sections and payload.get("summary"):
            normalized_sections["Summary"] = payload.get("summary")

        return {
            "category": category,
            "confidence": payload.get("confidence", "medium"),
            "title": payload.get("title") or f"{category} Analysis",
            "summary": payload.get("summary") or "The document was analyzed successfully.",
            "sections": normalized_sections or {"Summary": payload.get("summary") or "The document was analyzed successfully."}
        }

    def _extract_json_payload(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}

        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.S)
            if not match:
                return {}
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}

    def _document_classification_prompt(self, text: str) -> str:
        categories = self._category_sections()
        options = ", ".join(categories.keys())
        return f"""You are classifying uploaded document content for a document intelligence platform.

Return ONLY valid JSON with this exact structure:
{{
  "category": "{options}",
  "confidence": "high|medium|low",
  "title": "Short descriptive title",
  "summary": "2-sentence overview",
  "sections": {{
    "Field Name": ["value 1", "value 2"] or "single value string"
  }}
}}

Rules:
- Pick the single best category.
- Use the most relevant field names for that category.
- Keep values concise, structured, and useful.
- If a field is not found, omit it.
- Do not include markdown or commentary.

Category-specific field names:
- Resume: Candidate Details, Skills, Education, Experience, ATS Score, Strengths, Weaknesses, Missing Skills, Improvement Suggestions, Suitable Job Roles, Interview Questions
- Legal Agreement: Parties Involved, Agreement Type, Payment Terms, Important Dates, Obligations, Confidentiality, Termination Clause, Risks, Missing Clauses, Summary
- Notes: Main Topics, Key Concepts, Definitions, Formulas, Revision Points, Quiz Questions, Flashcards, Summary
- Research Paper: Title, Authors, Problem Statement, Methodology, Dataset, Results, Limitations, Future Work, Simple Explanation
- Invoice: Vendor, Customer, Invoice Number, Dates, Taxes, Total Amount, Payment Status, Due Date
- Medical Report: Diagnosis, Medicines, Test Results, Abnormal Values, Recommendations, Follow-up Details
- Meeting Minutes: Agenda, Participants, Discussion Points, Decisions, Action Items, Responsibilities, Deadlines
- Financial Report: Company, Period, Revenue, Expenses, Profitability, Risks, Recommendations
- Government Document: Agency, Subject, Key Requirements, Important Dates, Obligations, Summary
- Others: Key Points, Summary

Document text:
{text[:12000]}
"""

    def _category_sections(self) -> Dict[str, List[str]]:
        return {
            "Resume": ["Candidate Details", "Skills", "Education", "Experience", "ATS Score", "Strengths", "Weaknesses", "Missing Skills", "Improvement Suggestions", "Suitable Job Roles", "Interview Questions"],
            "Legal Agreement": ["Parties Involved", "Agreement Type", "Payment Terms", "Important Dates", "Obligations", "Confidentiality", "Termination Clause", "Risks", "Missing Clauses", "Summary"],
            "Notes": ["Main Topics", "Key Concepts", "Definitions", "Formulas", "Revision Points", "Quiz Questions", "Flashcards", "Summary"],
            "Research Paper": ["Title", "Authors", "Problem Statement", "Methodology", "Dataset", "Results", "Limitations", "Future Work", "Simple Explanation"],
            "Invoice": ["Vendor", "Customer", "Invoice Number", "Dates", "Taxes", "Total Amount", "Payment Status", "Due Date"],
            "Medical Report": ["Diagnosis", "Medicines", "Test Results", "Abnormal Values", "Recommendations", "Follow-up Details"],
            "Meeting Minutes": ["Agenda", "Participants", "Discussion Points", "Decisions", "Action Items", "Responsibilities", "Deadlines"],
            "Financial Report": ["Company", "Period", "Revenue", "Expenses", "Profitability", "Risks", "Recommendations"],
            "Government Document": ["Agency", "Subject", "Key Requirements", "Important Dates", "Obligations", "Summary"],
            "Others": ["Key Points", "Summary"]
        }

    def _default_sections_for_category(self, category: str) -> List[str]:
        return self._category_sections().get(category, self._category_sections()["Others"])
    
    def get_answer(self, query: str, vector_store) -> Tuple[str, str, List[Dict]]:
        """Retrieve the most relevant document chunks and answer the user's specific question."""
        try:
            if not query or not query.strip():
                return "Please ask a specific question about the uploaded documents.", "error", []

            docs_with_scores = vector_store.similarity_search_with_score(query, k=6)
            if not docs_with_scores:
                return "No relevant information was found in the uploaded documents for that question.", "error", []

            yt_links = self._get_youtube_links(query)
            web_links = self._get_web_links(query)
            all_links = self._combine_links(yt_links, web_links)

            answer = self._generate_answer_with_references(query, docs_with_scores, all_links)
            return answer, "combined", all_links
        except Exception as e:
            return f"Error processing query: {str(e)}", "error", []
        
    def _get_youtube_links(self, query: str) -> List[Dict]:
        """Search YouTube using API"""
        try:
            if not self.youtube:
                return []
                
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=3,
                type='video',
                relevanceLanguage='en',
                videoEmbeddable='true'
            ).execute()
            
            return [{
                'type': 'youtube',
                'title': item['snippet']['title'],
                'url': f"https://youtu.be/{item['id']['videoId']}",
                'description': item['snippet']['description'][:200] + '...',
                'thumbnail': item['snippet']['thumbnails']['default']['url']
            } for item in search_response.get('items', [])]
            
        except Exception as e:
            logger.error(f"YouTube search failed: {str(e)}")
            return []
        
    def _get_web_links(self, query: str) -> List[Dict]:
        """Get web search results"""
        try:
            if not self.search:
                return []
                
            results = self.search.results(query, 3)
            return [{
                'type': 'web',
                'title': res['title'],
                'url': res['link'],
                'description': res['snippet'][:200] + '...'
            } for res in results]
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return []

    def generate_summary(self, vector_store, focus: str = None) -> Tuple[str, List[Dict]]:
        """Generate a focused summary for the requested topic or a general summary if no focus is provided."""
        try:
            if focus and focus.strip():
                query = focus.strip()
                instruction = f"Focus the summary on this topic: {query}"
            else:
                query = "Provide comprehensive summary of key points"
                instruction = "Provide a comprehensive summary of the document"

            docs = vector_store.similarity_search(query, k=7)
            context = "\n".join([doc.page_content for doc in docs][:3])

            if not docs:
                return "No relevant document content was found to summarize.", []

            prompt = f"""You are summarizing uploaded document content.

            IMPORTANT:
            - Follow the user's requested focus area closely.
            - If the user provided a focus topic like 'types of biomass', give the answer centered on that topic.
            - Do not give a broad general introduction unless the focus area is empty.
            - If the topic is present, explain it directly and concisely.

            Instruction: {instruction}

            Document context:
            {context}

            Write a concise but useful summary that stays on the requested topic.
            """

            response = self.services["llm"].invoke(prompt)
            summary = response.content if hasattr(response, "content") else str(response)

            links = self._generate_contextual_links(query, context)
            return summary, links

        except Exception as e:
            return f"Summary generation failed: {str(e)}", []

    def _generate_contextual_links(self, query: str, context: str) -> List[Dict]:
        if not self.search:
            return []

        try:
            search_query = f"{query} {context[:500]}".strip()
            # Use the search wrapper's built-in results method
            results = self.search.results(search_query, 5)
            
            curated_links = []
            for res in results:
                link_type = "youtube" if "youtube.com" in res['link'] else "web"
                curated_links.append({
                    'type': link_type,
                    'title': res['title'],
                    'url': res['link'],
                    'snippet': res['snippet'][:150] + '...'
                })
            
            return sorted(curated_links, 
                key=lambda x: x['type'] == 'youtube', 
                reverse=True
            )[:3]
            
        except Exception as e:
            return []

    def _web_search(self, query: str) -> Tuple[str, List[Dict]]:
        """Enhanced web search with link aggregation"""
        try:
            results = self.search.results(query, 3)
            docs = [Document(page_content=res['snippet']) for res in results]
            links = [{
                'type': "youtube" if "youtube.com" in res['link'] else "web",
                'title': res['title'],
                'url': res['link'],
                'snippet': res['snippet']
            } for res in results]
            
            chain = load_qa_chain(
                self.services["llm"],
                prompt=self._web_prompt()
            )
            answer = chain.run({"input_documents": docs, "question": query})
            return answer, links
            
        except Exception as e:
            return f"Web search failed: {str(e)}", []
        
    def _combine_links(self, yt_links: List[Dict], web_links: List[Dict]) -> List[Dict]:
        """Combine and prioritize relevant links"""
        # Prioritize YouTube links if query seems to ask for video content
        combined = yt_links + web_links
        return sorted(combined, key=lambda x: x['type'] == 'youtube', reverse=True)[:5]

    def _generate_answer_with_references(self, query: str, docs, links: List[Dict]) -> str:
        """Generate a direct answer to the user's question from the most relevant retrieved chunks."""
        try:
            relevant_chunks = []
            for doc, score in docs[:4]:
                chunk_text = doc.page_content.strip()
                if chunk_text:
                    metadata = doc.metadata or {}
                    source_name = metadata.get("source") or "uploaded document"
                    relevant_chunks.append(
                        f"[Source: {source_name}] [Relevance score: {score:.3f}]\n{chunk_text}"
                    )

            context = "\n\n---\n\n".join(relevant_chunks)

            resource_section = ""
            if links:
                resource_section = "\n\n🔗 Relevant Resources:\n"
                for i, link in enumerate(links, 1):
                    icon = "🎥" if link['type'] == 'youtube' else "🌐"
                    resource_section += f"{i}. {icon} [{link['title']}]({link['url']})\n"

            prompt = f"""You are answering a question from uploaded document content.

            IMPORTANT:
            - Answer the user's question directly and briefly.
            - Do not write a general summary unless the user asked for one.
            - Use only the provided context to answer.
            - Mention the source file name when relevant.
            - If the answer is not in the context, say that clearly.
            - Format the response in a structured way.

            Required format:
            1. Short Answer: one or two sentences directly answering the question.
            2. Evidence: quote or paraphrase the most relevant sentence from the document context.
            3. Source: mention the document file name from the context.
            4. Notes: add one brief note if helpful.

            Question: {query}

            Relevant document context:
            {context}

            {resource_section}

            Return the response in the exact structure above.
            """

            model = self.services["llm"]
            response = model.invoke(prompt)
            return response.content

        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            return f"Failed to generate answer: {str(e)}"

    # Prompt templates remain the same as previous
    def _qa_prompt(self):
        return PromptTemplate.from_template("""
        Context Information:
        {context}
        
        User Question: {question}
        
        Provide detailed, evidence-based answer. Include markdown formatting when appropriate:
        """)

    def _summary_prompt(self):
        return PromptTemplate.from_template("""
        Synthesize key information from these documents:
        {text}
        
        Include in summary:
        - Core concepts and themes
        - Critical details and data points
        - Technical terminology explanations
        - Conclusions and implications
        
        Structured Summary (use markdown headings):
        """)

    def _web_prompt(self):
        return PromptTemplate.from_template("""
        Integrate information from these web results:
        {context}
        
        Original Query: {question}
        
        Generate comprehensive answer with source citations:
        """)
        
    # def generate_image_caption(self, image_bytes, prompt=None):
    #     """
    #     Image captioning disabled because Gemini was removed.
    #     """
    #     return "Image captioning is currently disabled because Gemini is not configured."
        
        
    def process_extracted_text(self, text, query=None):
        """Analyze extracted text with optional user query"""
        try:
            if not query:
                return text
                
            model = self.services["llm"]
            prompt = f"""Extracted Text:
            {text}
            
            User Instruction: {query}
            
            Generate comprehensive response:"""

            response = model.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Text analysis failed: {str(e)}"























# from langchain.chains.question_answering import load_qa_chain
# from langchain.chains.summarize import load_summarize_chain
# from langchain.prompts import PromptTemplate
# from langchain.schema import Document
# import io
# from PIL import Image
# import google.generativeai as genai

# class QASystem:
#     def __init__(self, services):
#         self.services = services
#         self.embeddings = services['embeddings']
#         self.search = services['search']
        
#     def get_answer(self, query, vector_store):
#         """Hybrid QA workflow with confidence threshold"""
#         try:
#             docs_with_scores = vector_store.similarity_search_with_score(query, k=5)
            
#             # Use web search if document relevance is low
#             if docs_with_scores and max(score for _, score in docs_with_scores) < 0.5:
#                 return self._web_search(query), "web"
            
#             docs = [doc for doc, _ in docs_with_scores]
            
#             chain = load_qa_chain(
#                 ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3),
#                 prompt=self._qa_prompt()
#             )
#             return chain.run({"input_documents": docs, "question": query}), "pdf"
#         except Exception as e:
#             return f"QA processing failed: {str(e)}", "error"

#     def generate_summary(self, vector_store, focus=None):
#         """Context-aware document summarization"""
#         try:
#             query = focus or "Provide comprehensive summary of key points"
#             docs = vector_store.similarity_search(query, k=7)
            
#             summary_chain = load_summarize_chain(
#                 ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2),
#                 chain_type="map_reduce",
#                 combine_prompt=self._summary_prompt(),
#                 verbose=False
#             )
#             return summary_chain.run(docs)
#         except Exception as e:
#             return f"Summary generation failed: {str(e)}"

#     def generate_image_caption(self, image, prompt=None):
#         """Generate image captions using Gemini 1.5 Flash"""
#         try:
#             model = self.services['gemini']  # Should be initialized as gemini-1.5-flash
#             base_prompt = """Analyze this image and generate detailed caption covering:
#             1. Main subjects and their relationships
#             2. Contextual environment
#             3. Visual composition
#             4. Atmosphere/tone"""
            
#             response = model.generate_content(
#                 contents=[
#                     prompt or base_prompt,
#                     image  # Direct PIL Image input
#                 ],
#                 generation_config={
#                     "temperature": 0.4,
#                     "max_output_tokens": 512
#                 }
#             )
            
#             # Proper response handling for Gemini 1.5
#             if response.candidates and len(response.candidates) > 0:
#                 if (parts := response.candidates[0].content.parts):
#                     return parts[0].text
#             return "No caption could be generated"
            
#         except Exception as e:
#             return f"Caption error: {str(e)}"

#     def process_extracted_text(self, text, query=None):
#         """Analyze extracted text with optional user query"""
#         try:
#             if not query:
#                 return text  # Return raw text if no query provided
                
#             model = self.services['gemini']
#             prompt = f"""Extracted Text:
#             {text}
            
#             User Instruction: {query}
            
#             Generate comprehensive response:"""
            
#             response = model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             return f"Text analysis failed: {str(e)}"

#     def _web_search(self, query):
#         """Fallback to web search results"""
#         try:
#             results = self.search.results(query, 3)
#             docs = [Document(page_content=res['snippet']) for res in results]
            
#             chain = load_qa_chain(
#                 ChatGoogleGenerativeAI(model="gemini-pro"),
#                 prompt=self._web_prompt()
#             )
#             return chain.run({"input_documents": docs, "question": query})
#         except Exception as e:
#             return f"Web search failed: {str(e)}"

#     def _qa_prompt(self):
#         return PromptTemplate.from_template(
#             """Context Information:
#             {context}
            
#             User Question: {question}
            
#             Provide detailed, evidence-based answer:"""
#         )

#     def _summary_prompt(self):
#         return PromptTemplate.from_template(
#             """Synthesize key information from these documents:
#             {text}
            
#             Include in summary:
#             - Core concepts and themes
#             - Critical details and data points
#             - Technical terminology explanations
#             - Conclusions and implications
            
#             Structured Summary:"""
#         )

#     def _web_prompt(self):
#         return PromptTemplate.from_template(
#             """Integrate information from these web results:
#             {context}
            
#             Original Query: {question}
            
#             Generate comprehensive answer:"""
#         )




































