import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class GuardrailValidationResult(BaseModel):
    is_valid: bool
    sanitized_query: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def validate_and_sanitize_input(query: str, max_chars: int = 1500) -> GuardrailValidationResult:
    """
    Validates and sanitizes raw user query string before ingestion into LangGraph pipeline.
    Checks:
    1. Non-empty / non-whitespace
    2. Minimum and maximum length bounds
    3. Injection / adversarial character sequence filtering
    4. Numeric sanity checks for inline budgets / days
    """
    errors = []
    warnings = []
    
    if not query or not query.strip():
        return GuardrailValidationResult(
            is_valid=False,
            sanitized_query="",
            errors=["User query cannot be empty. Please provide your travel preferences."]
        )
    
    cleaned = query.strip()
    
    if len(cleaned) < 5:
        return GuardrailValidationResult(
            is_valid=False,
            sanitized_query=cleaned,
            errors=["Query is too short. Please describe destination, duration, budget, or preferred activities."]
        )
        
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars]
        warnings.append(f"Query exceeded maximum character limit ({max_chars}) and was truncated.")

    # Check for obvious harmful prompt injection patterns
    injection_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)system\s+prompt\s+override",
        r"(?i)drop\s+table",
        r"(?i)<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, cleaned):
            errors.append("Malicious instruction or script detected in input. Request blocked by security guardrail.")
            return GuardrailValidationResult(
                is_valid=False,
                sanitized_query="",
                errors=errors
            )

    # Sanitize control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    # Basic entity detection for metadata hints
    metadata = {}
    day_match = re.search(r"(\d+)\s*(?:-|to\s*)?(?:\d+)?\s*(?:day|days|night|nights|d\b)", cleaned, re.IGNORECASE)
    if day_match:
        days = int(day_match.group(1))
        if days > 30:
            warnings.append(f"Extracted duration ({days} days) is unusually long for a standard itinerary; capped at 30 days.")
            metadata["extracted_days"] = min(days, 30)
        elif days < 1:
            warnings.append("Extracted duration was 0; defaulting to 1 day.")
            metadata["extracted_days"] = 1
        else:
            metadata["extracted_days"] = days
            
    # Budget pattern
    budget_match = re.search(r"(?:₹|rs\.?|inr|\$|eur|usd)\s*([\d,]+(?:\.\d+)?)\s*(k|lakh|lac|m|thousand|million)?", cleaned, re.IGNORECASE)
    if budget_match:
        val_str = budget_match.group(1).replace(",", "")
        try:
            val = float(val_str)
            multiplier = budget_match.group(2)
            if multiplier:
                multiplier = multiplier.lower()
                if multiplier in ["k", "thousand"]:
                    val *= 1000
                elif multiplier in ["lakh", "lac"]:
                    val *= 100000
                elif multiplier in ["m", "million"]:
                    val *= 1000000
            metadata["extracted_budget"] = val
        except ValueError:
            pass

    return GuardrailValidationResult(
        is_valid=len(errors) == 0,
        sanitized_query=cleaned,
        errors=errors,
        warnings=warnings,
        metadata=metadata
    )
