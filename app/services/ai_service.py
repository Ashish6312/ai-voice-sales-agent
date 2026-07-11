"""
AI Service

Handles all communication with Gemini.

Responsibilities
----------------
1. Build prompts
2. Generate AI responses
3. Generate CRM summaries
4. Handle retries
5. Handle API errors
"""

import json
import logging
import re
import time


from google import genai
from typing import Dict, Any

from app.core.config import get_settings
from app.schemas.crm_summary import CRMSummary
from app.services.prompt_manager import PromptManager



logger = logging.getLogger(__name__)


class AIService:

    MAX_RETRIES = 3

    BASE_DELAY = 2

    def __init__(self):

        self.settings = get_settings()

        self.client = genai.Client(
            api_key=self.settings.gemini_api_key
        )

        self.model = self.settings.model_name

        self.prompt_manager = PromptManager()

        self.system_prompt = (
            self.prompt_manager.get_system_prompt()
        )

    # --------------------------------------------------
    # Prompt Builder
    # --------------------------------------------------

    def build_prompt(
        self,
        history,
        current_message,
        context="",
    ):

        conversation = ""

        for message in history:

            role = message["role"].capitalize()

            content = message["content"]

            conversation += (
                f"{role}: {content}\n"
            )

        return f"""
{self.system_prompt}

================================================

Company Knowledge

================================================

{context}

================================================

Conversation History

================================================

{conversation}

================================================

Customer Message

================================================

{current_message}

================================================

Rules

================================================

Answer ONLY using company knowledge.

If information is unavailable,
politely tell the customer you
will confirm with the team.

Keep answers conversational.

Ask only one question at a time.

Do not hallucinate.
"""

    def build_sales_prompt(
        self,
        history,
        customer_message,
        context=""
    ):

        conversation = ""

        for msg in history:

            conversation += (
                f"{msg['role'].capitalize()}: "
                f"{msg['content']}\n"
            )

        return f"""
You are Ashish, an experienced AI Sales Executive.

Your objective is to sell our AI Voice Sales Agent.

You must:
• Answer naturally.
• Use ONLY the company knowledge.
• Never invent information.
• Understand customer requirements.
• Detect buying intent.
• Detect objections.
• Detect if customer wants pricing.
• Detect if customer wants a demo.
• Detect if customer wants a meeting.
• Detect if customer wants to end the call.
• Qualify the customer.

------------------------------------------------
Conversation Flow Rules (CRITICAL)
------------------------------------------------
1. If the customer says they are "not interested", "no interest", or similar:
   - DO NOT end the call immediately (set "end_call" to false).
   - Reply: "No problem. May I ask if you're currently handling this manually or using another tool?"
   - Set "intent" to "not_interested" and "qualification" to "Cold".
   - In "crm_update", set "status" to "Not Interested" and "objection" to "Not interested initially".

2a. If the customer replies they are using a COMPETITOR tool (e.g. "Yes", "we use Salesforce", "we have a tool"):
   - Reply: "Understood. Thank you for your time. Have a wonderful day."
   - Set "end_call" to true.
   - Set "intent" to "end_call" and "qualification" to "Cold".
   - In "crm_update", set "status" to "Not Interested", "objection" to "Already using competitor", "summary" to "Customer already uses another platform.", "requirement" to "None", and "follow_up" to "No follow-up".

2b. If the customer replies they do it MANUALLY (e.g. "it's manual", "we do it ourselves", "no tools", "manually"):
   - This is a WARM lead. Do NOT end the call.
   - Reply: "That's exactly what we solve. Our AI agent automates manual sales calls completely. Would you like to know how it works?"
   - Set "end_call" to false.
   - Set "intent" to "interested" and "qualification" to "Warm".
   - In "crm_update", set "status" to "Warm Lead", "summary" to "Customer currently does sales calls manually. Showed interest when told about automation.", "requirement" to "Sales call automation", and "objection" to "".

------------------------------------------------
Company Knowledge
------------------------------------------------
{context}

------------------------------------------------
Conversation
------------------------------------------------
{conversation}

------------------------------------------------
Customer
------------------------------------------------
{customer_message}

------------------------------------------------
Return ONLY valid JSON.
Never return markdown.

JSON Schema
{{
    "reply": "",
    "intent": "conversation | interested | pricing | objection | meeting | follow_up | not_interested | end_call",
    "qualification": "Hot | Warm | Cold",
    "crm_update": {{
        "status": "",
        "summary": "",
        "requirement": "",
        "objection": "",
        "meeting": "",
        "follow_up": ""
    }},
    "end_call": false
}}
"""

    # --------------------------------------------------
    # Gemini Request
    # --------------------------------------------------

    def _generate(
        self,
        prompt,
    ):
        # --------------------------------------------------
        # Primary: Groq API integration (Super fast & quota-free)
        # --------------------------------------------------
        if self.settings.groq_api_key:
            import urllib.request
            import urllib.error
            import json

            # Llama-3.3-70b is the flagship high-quality model on Groq
            model = "llama-3.3-70b-versatile"
            is_json = "{" in prompt or "json" in prompt.lower()

            headers = {
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            body = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }

            if is_json:
                body["response_format"] = {"type": "json_object"}

            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    logger.info(f"Calling Groq with model {model} (Attempt {attempt})...")
                    # Set 7 second timeout for quick responses
                    with urllib.request.urlopen(req, timeout=7) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        text = res_data["choices"][0]["message"]["content"].strip()
                        logger.info("Groq Response Received successfully.")
                        return text
                except Exception as e:
                    logger.error(f"Error calling Groq model {model}: {e}")
                    if attempt == self.MAX_RETRIES:
                        logger.warning("Groq failed all attempts. Falling back to Gemini...")
                    else:
                        time.sleep(1)

        # --------------------------------------------------
        # Fallback: Gemini API integration
        # --------------------------------------------------
        delay = self.BASE_DELAY
        # Only models confirmed available and working for this API key
        # gemini-2.5-flash-lite: working, separate quota
        # gemini-flash-latest: working (1.5-flash), separate quota
        # gemini-2.0-flash-lite: currently exhausted fallback
        # gemini-2.5-flash: currently exhausted fallback
        models_to_try = [self.model, "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
        models_to_try = list(dict.fromkeys([m for m in models_to_try if m]))

        for attempt in range(
            1,
            self.MAX_RETRIES + 1,
        ):
            has_quota_error = False
            last_error = ""
            for model in models_to_try:
                try:
                    logger.info(
                        f"Calling Gemini with model {model} (Attempt {attempt})..."
                    )
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    logger.info(
                        "Gemini Response Received."
                    )
                    return response.text.strip()
                except Exception as e:
                    error = str(e)
                    last_error = error
                    logger.error(f"Error calling model {model}: {error}")

                    # If it's a 429 rate limit or 404 not found, rotate to next model
                    if "429" in error or "RESOURCE_EXHAUSTED" in error or "404" in error or "NOT_FOUND" in error:
                        if "429" in error or "RESOURCE_EXHAUSTED" in error:
                            has_quota_error = True
                        logger.warning(f"Model {model} failed, trying next fallback model...")
                        continue

                    # Server Busy
                    if "503" in error:
                        logger.warning(
                            f"Server Busy. Retrying model {model} after sleep."
                        )
                        time.sleep(delay)
                        delay *= 2
                        continue

                    # Raise other critical exceptions
                    raise RuntimeError(error)

            if has_quota_error:
                # Quota is exhausted, raise immediately to avoid timeouts
                raise RuntimeError(f"Gemini API Quota Exhausted: {last_error}")

            # Wait a short delay before next full retry attempt
            time.sleep(1)

        raise RuntimeError(
            "Maximum retry attempts exceeded for all fallback models."
        )

    # --------------------------------------------------
    # Chat
    # --------------------------------------------------

    def generate_response(
        self,
        history,
        customer_message,
        context="",
    ):

        prompt = self.build_prompt(

            history=history,

            current_message=customer_message,

            context=context,
        )

        return self._generate(prompt)

    def generate_sales_response(
        self,
        history,
        customer_message,
        context=""
    ):

        prompt = self.build_sales_prompt(
            history,
            customer_message,
            context,
        )

        response = self._generate(prompt)

        response = self._clean_json(response)

        try:

            return json.loads(response)

        except Exception:

            logger.exception("Gemini returned invalid JSON")

            return {

                "reply": response,

                "intent": "conversation",

                "qualification": "Warm",

                "crm_update": {

                    "status": "Follow Up",

                    "summary": customer_message,

                    "requirement": "",

                    "objection": "",

                    "meeting": "",

                    "follow_up": "",

                },

                "end_call": False,

            }

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def generate_summary(
        self,
        conversation,
    ):

        prompt = (
            self.prompt_manager
            .get_summary_prompt()
        )

        from datetime import datetime, timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        current_date_str = datetime.now(ist).strftime("%A, %B %d, %Y")

        final_prompt = f"""
{prompt}

====================================================
Current Call Context
====================================================
Current Date: {current_date_str} (Use this date to convert relative expressions like 'tomorrow', 'day after tomorrow', 'next Monday' into exact calendar dates).

Conversation

{conversation}
"""

        response = self._generate(
            final_prompt
        )

        response = self._clean_json(
            response
        )

        data = json.loads(response)

        return CRMSummary.model_validate(
            data
        )

    # --------------------------------------------------
    # Clean JSON
    # --------------------------------------------------

    @staticmethod
    def _clean_json(
        response,
    ):

        response = response.strip()

        response = response.replace(
            "```json",
            "",
        )

        response = response.replace(
            "```",
            "",
        )

        return response.strip()