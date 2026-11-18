import re
from typing import Dict, Any, Tuple

class PostingRulesEngine:
    @staticmethod
    def evaluate_rules(rendition: Dict[str, Any], destination: Dict[str, Any], state: Dict[str, Any]) -> Tuple[bool, str, str, bool]:
        """
        Evaluates destination rules against content rendition and posting state.
        Returns: (is_allowed, error_code, reason, retryable)
        """
        # 1. Frequency Cap Check
        recent_posts = state.get("posts_in_window", 0)
        max_allowed = destination.get("frequency_cap_max", 5)
        if recent_posts >= max_allowed:
            return False, "DEST_RULE_FREQUENCY_CAP", "Frequency cap reached; reschedule after the cap window.", True

        # 2. Self-Promotion Policy Check
        if rendition.get("is_promotional", False) and not destination.get("self_promo_allowed", True):
            return False, "DEST_SPEC_VIOLATION", "Destination bans self-promotional content.", False

        # 3. Link Policy Check
        body = rendition.get("body", "")
        has_links = bool(re.search(r"https?://", body)) or bool(rendition.get("canonical_url"))
        link_policy = destination.get("link_policy", "allowed")
        if has_links and link_policy == "banned":
            return False, "DEST_SPEC_VIOLATION", "Destination link policy forbids external URLs.", False

        # 4. AI-Content Disclosure Check
        if rendition.get("is_ai_generated", False) and destination.get("disclosure_required", False):
            if not rendition.get("ai_disclosed", False):
                return False, "DEST_SPEC_VIOLATION", "Destination requires explicit AI-content disclosure.", False

        # 5. Character Limits Check
        title_max = destination.get("title_max_chars", 255)
        body_max = destination.get("body_max_chars", 32000)
        if len(rendition.get("title", "")) > title_max:
            return False, "DEST_SPEC_VIOLATION", f"Title exceeds {title_max} characters.", False
        if len(body) > body_max:
            return False, "DEST_SPEC_VIOLATION", f"Body exceeds {body_max} characters.", False

        return True, "", "", False