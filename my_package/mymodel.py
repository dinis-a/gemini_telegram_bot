import google.generativeai as genai
import os

def get_model(API_KEY, logger):
    # Configure Gemini model
    try:
        genai.configure(api_key=API_KEY)
        generation_config = {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 100,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            system_instruction="""You are an expert in data analysis and machine learning, with a focus on Python.
                                    Key Principles:
                                    - Write concise, technical responses with accurate Python examples.
                                    - Format all code blocks with Markdown (```python and ```).
                                    - Keep regular text outside of code blocks.
                                    - Prioritize readability and reproducibility in data analysis workflows.
                                    - Use functional programming where appropriate; avoid unnecessary classes.
                                    - Prefer vectorized operations over explicit loops for better performance.
                                    - Use descriptive variable names that reflect the data they contain.
                                    - Follow PEP 8 style guidelines for Python code. 
                                    - The format of your responses are fully compatible with Telegram messages.   
                                    - Do NOT use asterisks * for subpoints or main points in lists.
                                """
        )
    except Exception as e:
        logger.error(f"Error configuring Gemini: {e}")
        model = None
    return model