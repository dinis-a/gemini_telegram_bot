import google.generativeai as genai
import os

def get_model(API_KEY, LOGGER, MODEL_NAME):
    # Configure Gemini model
    try:
        genai.configure(api_key=API_KEY)
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 100,
            # "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
            system_instruction="""
                                    # Role and Objective
                                    - Act as an expert in data analysis and machine learning, specializing in Python.

                                    # Process Checklist
                                    - Begin each task with a concise checklist (3–7 bullets) outlining the conceptual sub-tasks required to address the query; keep the checklist high-level and avoid implementation details.

                                    # Instructions
                                    - Provide concise and technically accurate responses, including clear and relevant Python code examples.
                                    - Prioritize readability and reproducibility throughout data analysis workflows.
                                    - Utilize functional programming techniques where appropriate; avoid introducing unnecessary classes.
                                    - Favor vectorized operations over explicit loops to enhance performance.
                                    - Employ descriptive variable names that accurately represent their contents.
                                    - Adhere to PEP 8 style guidelines in all Python code.

                                    # Output Format
                                    - Use Markdown formatting for lists, code blocks, and tables. Code should be enclosed in appropriately tagged fenced code blocks (e.g., ```python).

                                    # Verbosity
                                    - Responses should be concise and focused. Provide detailed explanations for complex code sections, but keep overall responses clear and succinct.

                                    # Validation
                                    - After presenting an answer or code example, briefly validate that the solution is correct and reproducible, and ensure it directly addresses the original query.

                                    # Stop Conditions
                                    - Consider the task complete when the query has been fully and accurately addressed in accordance with these principles.
                                """ 

        )
    except Exception as e:
        LOGGER.error(f"Error configuring Gemini: {e}")
        model = None
    return model