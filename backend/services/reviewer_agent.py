import os
import json
from typing import Tuple
from config import OPENAI_API_KEY


def _call_chat_compat(model: str, messages: list, max_tokens: int = 200, temperature: float = 0.0):
    """Call chat completions in a way that's compatible across openai versions.

    Tries the new `OpenAI` client (openai>=1.0) first, then falls back to the older
    `openai.ChatCompletion.create` interface if available.
    Returns the response object (could be dict-like).
    """
    # Try new OpenAI client
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        return resp
    except Exception:
        pass

    # Fallback to old interface if present
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        return resp
    except Exception as e:
        raise


validator_system_message = """
You are an expert prompt evaluator.

Your job is to score a user’s input describing a data pipeline or DAG task.
Evaluate clarity, completeness, and logical flow, and give a score from 0 to 10.

Return ONLY a JSON object in the following format:
{
  "score": <float>,
  "feedback": "<short feedback or suggestion>"
}
"""


class ReviewerAgent:
    def __init__(self, model: str = None):
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        if not OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY is not set in environment')
        # The openai API key is applied inside the compatibility caller when needed.

    def validate(self, input_text: str) -> Tuple[bool, str, dict]:
        """Validate input using the model. Returns (is_valid, feedback, raw_result).

        is_valid: True when score >= 7.5 (configurable)
        feedback: short human-readable suggestion
        raw_result: parsed JSON response from model (if available)
        """
        try:
            messages = [
                {"role": "system", "content": validator_system_message},
                {"role": "user", "content": input_text},
            ]

            resp = _call_chat_compat(self.model, messages, max_tokens=200, temperature=0.0)

            # Normalize response text extraction for both clients
            try:
                # OpenAI (new client) shape
                text = resp.choices[0].message.content.strip()
            except Exception:
                # Older dict-like response
                text = resp['choices'][0]['message']['content'].strip()

            # Try to parse JSON from the model
            try:
                parsed = json.loads(text)
                score = float(parsed.get('score', 0))
                feedback = parsed.get('feedback', '')
            except Exception:
                # If parsing fails, fall back to a simple heuristic
                parsed = {'raw': text}
                score = 0.0
                feedback = 'Could not parse validator response; please make your input more explicit (include tasks, dependencies, schedule)'

            is_valid = score >= 7.5
            return is_valid, feedback, parsed

        except Exception as e:
            # On API or other errors, fall back to lightweight local validation
            fallback_feedback = self._local_validate(input_text)
            return False, fallback_feedback, {'error': str(e)}

    def _local_validate(self, input_text: str) -> str:
        """Simple local validation used as a fallback."""
        reqs = ['tasks', 'dependencies', 'schedule']
        missing = [r for r in reqs if r not in input_text.lower()]
        if missing:
            return f"Missing required information: {', '.join(missing)}"
        return 'Input looks OK but model validation failed; retry or refine input.'