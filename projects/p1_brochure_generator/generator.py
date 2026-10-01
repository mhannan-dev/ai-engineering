"""
Enterprise Brochure Generator - Structured Output & Self-Healing Generator
Uses Instructor and Pydantic v2 to enforce 100% type-safe JSON extraction
with automated schema validation error correction and retries.
"""

from typing import Optional
import instructor
from litellm import completion
from openai import OpenAI

try:
    from .config import DEFAULT_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL
    from .models import EnterpriseBrochure
except ImportError:
    from config import DEFAULT_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL
    from models import EnterpriseBrochure


class BrochureGenerator:
    """
    Structured output generator powered by Instructor and Pydantic v2.
    Implements automated self-healing retry mechanism for schema violations.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, max_retries: int = 3):
        self.model_name = model_name
        self.max_retries = max_retries
        self.client = self._initialize_instructor_client()

    def _initialize_instructor_client(self):
        """
        Initializes Instructor client wrapped around OpenAI client or litellm.
        Provides compatibility across OpenAI, DeepSeek, Anthropic, or local Ollama/vLLM.
        """
        if OPENAI_BASE_URL:
            # Custom base URL (e.g. DeepSeek or local vLLM/Ollama)
            base_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            return instructor.from_openai(base_client)

        try:
            return instructor.from_litellm(completion)
        except Exception:
            base_client = OpenAI(api_key=OPENAI_API_KEY)
            return instructor.from_openai(base_client)

    def generate_brochure(
        self, scraped_content: str, company_hint: Optional[str] = None
    ) -> EnterpriseBrochure:
        """
        Generates an EnterpriseBrochure instance from scraped and compressed website content.

        Features:
        - 100% Type-Safe: Guaranteed schema adherence to EnterpriseBrochure Pydantic model.
        - Automated Error Correction: Automatically retries on validation failure (up to max_retries).
        """
        system_prompt = (
            "You are an Elite Enterprise B2B Analyst and Copywriter. "
            "Your task is to analyze the provided extracted website content and generate "
            "a comprehensive, high-converting, professional Enterprise Brochure. "
            "Ensure all extracted information is grounded in the source text. "
            "Strictly adhere to the required JSON schema without omission."
        )

        user_prompt = f"""
Please generate an enterprise brochure from the following curated website content.

{f'Target Enterprise Hint: {company_hint}' if company_hint else ''}

=== EXTRACTED & COMPRESSED WEBSITE DATA ===
{scraped_content}
==========================================

Extract and structure the data strictly according to the EnterpriseBrochure schema.
If specific data (like founded year or phone number) is not mentioned in the source, set it to null.
Do not hallucinate pricing numbers—if not explicitly listed, specify 'Custom Enterprise / Contact Sales'.
"""

        # Instructor call with response_model and max_retries
        brochure: EnterpriseBrochure = self.client.chat.completions.create(
            model=self.model_name,
            response_model=EnterpriseBrochure,
            max_retries=self.max_retries,  # Automated Error Correction mechanism
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,  # Low temperature for factual precision
        )

        return brochure
