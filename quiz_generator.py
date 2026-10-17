import time
import os

from configs import build_chat_model


class QuizGenerator:
    def __init__(self):
        self.text_splitter = None
        self.retry_delay = 5
        self.max_retries = 3

        self.model = None

    def generate_quiz(self, pdf_text):
        """
        Generate a quiz from PDF text with error handling and retry logic.
        
        Args:
            pdf_text (str): Text extracted from PDF documents.
        
        Returns:
            list: List of structured quiz questions.
        
        Raises:
            RuntimeError: If quiz generation fails after retries.
        """
        if not pdf_text or not pdf_text.strip():
            raise RuntimeError("Quiz generation failed: no readable text was found.")

        try:
            if self.text_splitter is None:
                from langchain_text_splitters import RecursiveCharacterTextSplitter

                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=10000,
                    chunk_overlap=500
                )
            if self.model is None:
                self.model = build_chat_model(temperature=0.7)
            if self.model is None:
                raise RuntimeError(
                    "No AI API key configured. Set OPENROUTER_API_KEY or GROQ_API_KEY."
                )

            # Split text into manageable chunks
            chunks = self.text_splitter.split_text(pdf_text)
            context = "\n".join(chunks[:3])  # Use first 3 chunks for context

            # Define quiz generation prompt
            prompt = f"""Generate 5 MCQ questions from this context:
            {context}
            
            Follow this EXACT format:
            
            Question 1: [question text]
            A) [option 1]
            B) [option 2]
            C) [option 3]
            D) [option 4]
            Answer: [letter]
            
            [Repeat for Questions 2-5]"""

            # Retry logic for rate limits
            for attempt in range(self.max_retries):
                try:
                    response = self.model.invoke(prompt)

                    content = response.content if hasattr(response, "content") else str(response)
                    quiz = self.parse_quiz(content)
                    if len(quiz) < 5:
                        raise ValueError(
                            f"The model returned only {len(quiz)} valid questions; expected 5."
                        )
                    return quiz
                except Exception as e:
                    if "429" in str(e) and attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise

        except Exception as e:
            raise RuntimeError(f"Quiz generation failed: {str(e)}")

    def parse_quiz(self, response_text):
        """
        Parse the model's response into structured quiz questions.
        
        Args:
            response_text (str): Raw response text from the model.
        
        Returns:
            list: List of structured quiz questions.
        """
        questions = []
        current_q = {}
        
        # Split and clean response text
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        # Parse each line
        for line in lines:
            if line.lower().startswith("question"):
                if current_q:
                    questions.append(current_q)
                current_q = {"question": "", "options": [], "answer": ""}
                current_q["question"] = line.split(":", 1)[-1].strip()
            elif len(line) >= 3 and line[0].upper() in "ABCD" and line[1] in ").:":
                current_q["options"].append(line[2:].strip())
            elif line.lower().startswith("answer:"):
                answer = line.split(":", 1)[-1].strip().lower()
                if answer:
                    current_q["answer"] = answer[0]

        if current_q:
            questions.append(current_q)

        # Filter and return valid questions
        return [q for q in questions if self._is_valid_question(q)][:5]

    def _is_valid_question(self, question):
        """
        Validate the structure of a quiz question.
        
        Args:
            question (dict): Quiz question to validate.
        
        Returns:
            bool: True if the question is valid, False otherwise.
        """
        return (
            len(question.get("options", [])) == 4 and 
            question.get("answer") in ['a', 'b', 'c', 'd'] and 
            bool(question.get("question"))
        )