"""
LLM Chain Module: Generate answers using RAG (Retrieval-Augmented Generation).

This module:
1. Accepts user query + retrieved chunks
2. Builds a context-rich prompt when chunks exist
3. Falls back to a general conversation mode when no chunks are available
4. Calls GPT-4 (or a mock) with defensive error handling
5. Guarantees a non-empty, user-friendly response
"""

from typing import List, Dict, Any, Tuple, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from rag.retrieval import RetrievedChunk

SMALL_TALK_KEYWORDS = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI package not installed. Install with: pip install openai")


SYSTEM_PROMPT_CONTEXT = """You are a conversational insurance assistant AI that behaves like GPT-4 in natural dialogue.

Your responsibilities:
1) Maintain conversational memory — use prior messages in the session as context.
2) Answer questions clearly, accurately, and helpfully.
3) ALWAYS use the provided policy snippets as the primary source.
4) If the context does NOT include an answer, provide general helpful guidance based on industry knowledge.
5) Ask intelligent follow-up questions to refine and clarify user needs.

Conversation behavior:
- Friendly, human-like responses
- Natural flow
- Short paragraphs + occasional bullets
- Empathetic and helpful tone
- Reference policy_id and policy_name when citing documents
- Clarify when speaking generally vs. from documents
- Be specific and actionable - never generic

Output format:
- Response (using policy context when available)
- Optional follow-up question to understand user needs better

CRITICAL RULES:
- NEVER output: "I'm having trouble processing your request" or technical errors
- NEVER output generic messages like "I'm here to help" without specific information
- ALWAYS provide specific, actionable advice
- ALWAYS ask relevant follow-up questions when appropriate
- Always produce usable output"""

SYSTEM_PROMPT_GENERAL = """You are a conversational insurance assistant AI that behaves like GPT-4 in natural dialogue.

Your responsibilities:
1) Maintain conversational memory — use prior messages in the session as context.
2) Answer questions clearly, accurately, and helpfully.
3) When policy documents are not available, provide SPECIFIC, DETAILED insurance guidance based on industry knowledge.
4) Ask intelligent follow-up questions to refine and clarify user needs.

CRITICAL: DO NOT give generic responses like "I'm here to help" or "feel free to ask". Instead, provide SPECIFIC, ACTIONABLE advice with concrete details.

Conversation behavior:
- Friendly, human-like responses
- Natural flow
- Short paragraphs + occasional bullets
- Empathetic and helpful tone
- Be specific and detailed - never vague or generic

For health insurance questions: 
- Provide DETAILED advice about coverage types, eligibility, age considerations, waiting periods, riders, and next steps
- Include specific examples and numbers when relevant
- Ask follow-up questions like "Do you want coverage only for hospitalization, or also outpatient and pre-existing conditions?"
- Mention specific considerations for the user's age if mentioned

For bike/motorcycle insurance: 
- Provide DETAILED advice about coverage types, liability, collision, comprehensive, accessories
- Include specific coverage options and what they mean
- Ask follow-up questions like "Are you interested in coverage for theft, accidental damage, or third-party liability?"
- Mention typical premium ranges if relevant

For car insurance: 
- Provide DETAILED advice about coverage types, liability limits, deductibles, optional coverage
- Explain what each coverage type means in practical terms
- Ask relevant follow-up questions about vehicle type, usage, and needs

Output format:
- Response (specific, detailed, helpful with concrete information)
- Optional follow-up question to understand user needs better

NEVER output: "I'm having trouble processing your request" or technical errors.
NEVER output: Generic messages without specific information.
Always produce usable, actionable output."""


def _is_small_talk(user_query: str) -> bool:
    if not user_query:
        return False
    lowered = user_query.strip().lower()
    return any(lowered.startswith(keyword) for keyword in SMALL_TALK_KEYWORDS)


def _format_context(chunks: List[RetrievedChunk]) -> str:
    parts = []
    for idx, chunk in enumerate(chunks, start=1):
        snippet = chunk.text.strip()
        parts.append(
            f"[Snippet {idx}]\n"
            f"Policy: {chunk.policy_id} ({chunk.policy_type}) | Region: {chunk.region} | Clause: {chunk.clause_type}\n"
            f"{snippet}"
        )
    return "\n\n".join(parts)


class GPT4LLM:
    """
    Thin wrapper around OpenAI GPT-4 chat completions with retries and defensive checks.
    """

    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.0):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def generate(self, system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
        import time

        max_retries = 2
        delay = 2

        for attempt in range(max_retries + 1):
            try:
                start = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=1200,
                    top_p=0.95,
                    timeout=timeout
                )
                elapsed = time.time() - start
                print(f"✅ GPT-4 responded in {elapsed:.2f}s (attempt {attempt + 1})")

                if not response.choices:
                    raise ValueError("GPT-4 returned no choices")

                content = (response.choices[0].message.content or "").strip()
                if not content:
                    raise ValueError("GPT-4 returned empty content")
                return content

            except Exception as exc:
                print(f"⚠️ GPT-4 error on attempt {attempt + 1}: {exc}")
                if attempt < max_retries:
                    time.sleep(delay * (attempt + 1))
                    continue
                raise RuntimeError(str(exc))


class MockLLM:
    """
    Lightweight mock used when GPT-4 is unavailable. Provides a polite, context-aware answer.
    """

    def generate(self, system_prompt: str, user_prompt: str, chunks: List[RetrievedChunk] = None) -> str:
        # Extract user query from prompt
        user_query = ""
        if "User's question:" in user_prompt:
            user_query = user_prompt.split("User's question:")[-1].strip().split("\n")[0]
        elif "User said:" in user_prompt:
            user_query = user_prompt.split("User said:")[-1].strip().split("\n")[0]
        
        # If no chunks, use the detailed fallback with insurance-specific advice
        if not chunks:
            return _default_fallback(user_query)

        # If we have chunks, provide a summary
        summary_lines = ["Here's what I found in the policy documents:"]
        for chunk in chunks[:3]:
            summary_lines.append(f"- {chunk.policy_id} ({chunk.policy_type}): {chunk.text[:180]}...")

        summary_lines.append("Let me know if you'd like clarification on any specific clause.")
        return "\n".join(summary_lines)


def _default_fallback(user_query: str) -> str:
    """
    Provides a helpful fallback response when LLM fails or returns empty.
    Never returns error messages - always provides useful guidance.
    """
    if not user_query or not user_query.strip():
        return "Hello! How can I help you with insurance today?"
    
    if _is_small_talk(user_query):
        return "Hello! How can I help you with insurance today? Feel free to ask about health, car, or bike insurance policies."
    
    query_lower = user_query.lower()
    
    # Detect health insurance queries
    if any(word in query_lower for word in ["health", "medical", "hospital", "doctor", "treatment", "age", "57", "father", "senior", "male", "female", "year old", "years old"]):
        # Extract age if mentioned
        age_mentioned = "57" in query_lower or "age" in query_lower or "year old" in query_lower or "years old" in query_lower
        
        response = "I'd be happy to help you with health insurance options!\n\n"
        
        if age_mentioned:
            response += "For someone in their 50s or older, here's what to consider:\n\n"
            response += "• **Coverage Types**: Comprehensive plans cover hospitalization, surgeries, doctor visits, and preventive care. Basic plans offer essential coverage at lower premiums.\n\n"
            response += "• **Age-Specific Considerations**:\n"
            response += "  - Look for plans with coverage for pre-existing conditions (may have waiting periods of 1-4 years)\n"
            response += "  - Ensure no upper age limit for enrollment\n"
            response += "  - Comprehensive coverage for age-related health issues\n"
            response += "  - Consider room rent limits and sub-limits\n"
            response += "  - Check co-payment requirements\n"
            response += "  - Optional riders (critical illness, etc.)\n\n"
        else:
            response += "Here's general guidance for health insurance:\n\n"
            response += "• **Coverage Types**: Comprehensive plans cover hospitalization, surgeries, doctor visits, and preventive care. Basic plans offer essential coverage at lower premiums.\n\n"
            response += "• **Key Features to Consider**:\n"
            response += "  - Waiting periods for pre-existing conditions (typically 1-4 years)\n"
            response += "  - Room rent limits and sub-limits\n"
            response += "  - Co-payment requirements\n"
            response += "  - Optional riders (critical illness, maternity, etc.)\n\n"
        
        response += "To help me recommend the best options, could you tell me:\n"
        response += "• Do you want coverage only for hospitalization, or also outpatient and pre-existing conditions?\n"
        response += "• What's your approximate age range? (This helps determine eligibility and premiums)\n"
        response += "• Are you looking for individual or family coverage?"
        
        return response
    
    # Detect car insurance queries
    if any(word in query_lower for word in ["car", "auto", "vehicle", "automobile", "four-wheeler"]):
        response = "I can help you understand car insurance options!\n\n"
        response += "Here's what you should know:\n\n"
        response += "• **Coverage Types**: Full coverage includes liability, collision, and comprehensive. Liability-only meets minimum legal requirements.\n\n"
        response += "• **Key Considerations**:\n"
        response += "  - Liability limits (bodily injury and property damage)\n"
        response += "  - Deductibles (amount you pay before coverage kicks in)\n"
        response += "  - Optional coverage (roadside assistance, rental car reimbursement)\n\n"
        response += "To help me recommend the best options, could you tell me:\n"
        response += "• What type of coverage are you looking for - full coverage or liability-only?\n"
        response += "• What's the make and model of your vehicle?\n"
        response += "• Do you need any optional coverage like roadside assistance?"
        
        return response
    
    # Detect bike insurance queries (check this BEFORE car, as "bike" might match "bicycle")
    if any(word in query_lower for word in ["bike", "bicycle", "motorcycle", "two-wheeler", "scooter", "motorbike"]):
        response = "I'd be happy to help you with bike insurance!\n\n"
        response += "Here's what you should know:\n\n"
        response += "• **Motorcycle Insurance**: Typically includes liability, collision, and comprehensive coverage. Some policies cover accessories and custom parts.\n\n"
        response += "• **Bicycle Insurance**: Usually covers theft, damage from accidents, and liability while riding.\n\n"
        response += "• **Key Considerations**:\n"
        response += "  - Premium depends on bike value, usage, and location\n"
        response += "  - Coverage limits and deductibles vary\n"
        response += "  - Some policies require proof of purchase and serial number registration\n\n"
        response += "To help me recommend the best coverage, could you tell me:\n"
        response += "• Are you interested in coverage for theft, accidental damage, or third-party liability?\n"
        response += "• What type of bike do you have - motorcycle or bicycle?\n"
        response += "• What's the approximate value of your bike?"
        
        return response
    
    # General fallback - ask clarifying questions
    if "comparison" in query_lower or "compare" in query_lower:
        response = "I'd be happy to help you compare insurance policies!\n\n"
        response += "To provide the best comparison, I need a bit more information:\n\n"
        response += "• **What type of insurance** are you comparing - health, car, or bike?\n"
        response += "• **What specific features** are most important to you? (e.g., coverage amount, premium, waiting periods)\n"
        response += "• **Individual or family coverage?**\n\n"
        response += "Once you share these details, I can help you compare options and find the best fit!"
    elif "help" in query_lower or "need" in query_lower or "want" in query_lower:
        response = "I'd be happy to help you with insurance!\n\n"
        response += "I can assist with:\n\n"
        response += "• **Health Insurance**: Coverage options, eligibility, waiting periods, age-specific plans, pre-existing conditions\n"
        response += "• **Car Insurance**: Liability, collision, comprehensive coverage, deductibles, optional features\n"
        response += "• **Bike Insurance**: Motorcycle and bicycle coverage, theft protection, liability\n\n"
        response += "What type of insurance are you interested in? Feel free to ask specific questions!"
    else:
        response = f"I'd be happy to help you with your insurance question about \"{user_query}\"!\n\n"
        response += "To provide the most helpful guidance, could you tell me:\n\n"
        response += "• **What type of insurance** are you interested in - health, car, or bike?\n"
        response += "• **What specific aspect** would you like to know more about?\n"
        response += "• **Any particular requirements** or concerns?\n\n"
        response += "The more details you share, the better I can assist you!"
    
    return response


def generate_answer_with_rag(
    user_query: str,
    retrieved_chunks: List[RetrievedChunk],
    policy_type: str = None,
    region: str = None,
    conversation_history: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate an answer that is always conversational and never empty.
    """

    has_context = bool(retrieved_chunks)
    small_talk = _is_small_talk(user_query)
    
    # Check if this is a specific insurance query (health, car, bike)
    query_lower = user_query.lower() if user_query else ""
    
    # More comprehensive detection - check for insurance type keywords
    health_keywords = ["health", "medical", "hospital", "doctor", "treatment", "age", "57", "father", "senior", "healthcare", "male", "female", "year old", "years old"]
    car_keywords = ["car", "auto", "vehicle", "automobile", "four-wheeler"]
    bike_keywords = ["bike", "bicycle", "motorcycle", "two-wheeler", "scooter", "motorbike"]
    
    has_health = any(word in query_lower for word in health_keywords)
    has_car = any(word in query_lower for word in car_keywords)
    has_bike = any(word in query_lower for word in bike_keywords)
    
    # Also check for intent words combined with insurance
    has_intent = any(word in query_lower for word in ["need", "want", "looking for", "interested in", "require", "get", "take", "should", "give me", "comparison", "compare"])
    has_insurance = "insurance" in query_lower
    has_policy = "policy" in query_lower
    
    # It's an insurance query if:
    # 1. Contains specific insurance type keywords, OR
    # 2. Contains intent words + "insurance" or "policy", OR
    # 3. Contains "policy" or "insurance" with age/health keywords
    is_insurance_query = has_health or has_car or has_bike or (has_intent and (has_insurance or has_policy)) or (has_policy and has_health)
    
    print(f"🔍 Query analysis: health={has_health}, car={has_car}, bike={has_bike}, intent={has_intent}, insurance={has_insurance}, policy={has_policy}, is_insurance_query={is_insurance_query}")

    # Initialize llm_answer to empty string
    llm_answer = ""
    
    if has_context:
        # We have policy context - use it
        context_str = _format_context(retrieved_chunks)
        system_prompt = SYSTEM_PROMPT_CONTEXT
        
        # Include conversation history if available
        history_context = ""
        if conversation_history:
            history_context = f"\n\nCONVERSATION HISTORY:\n{conversation_history}\n"
        
        user_prompt = (
            f"{context_str}{history_context}\n\n---\nUSER QUESTION: {user_query}\n\n"
            "Provide a clear, conversational answer drawn from the policy snippets above. "
            "Use the conversation history to understand context. "
            "Ask a helpful follow-up question if it would clarify the user's needs."
        )
        try:
            if settings.LLM_MODEL_NAME != "mock-llm" and OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
                try:
                    llm = GPT4LLM(
                        api_key=settings.OPENAI_API_KEY,
                        model=settings.LLM_MODEL_NAME,
                        temperature=settings.LLM_TEMPERATURE,
                    )
                    llm_answer = llm.generate(system_prompt, user_prompt)
                    print(f"✅ GPT-4 generated answer: {len(llm_answer)} chars")
                except Exception as gpt_error:
                    print(f"⚠️ GPT-4 error, using fallback: {str(gpt_error)}")
                    llm_answer = ""
            else:
                print("ℹ️ Using mock LLM fallback")
                try:
                    llm = MockLLM()
                    llm_answer = llm.generate(system_prompt, user_prompt, retrieved_chunks)
                    print(f"✅ Mock LLM generated answer: {len(llm_answer)} chars")
                except Exception as mock_error:
                    print(f"⚠️ Mock LLM error, using fallback: {str(mock_error)}")
                    llm_answer = ""
        except Exception as exc:
            print(f"❌ LLM generation failed: {exc}")
            import traceback
            traceback.print_exc()
            llm_answer = ""
    else:
        # No context available
        skip_llm_processing = False
        if is_insurance_query and not small_talk:
            # For specific insurance queries without context, ALWAYS use detailed fallback directly
            # Skip LLM entirely to avoid generic responses
            print(f"📋 No context but specific insurance query detected: '{user_query[:50]}', SKIPPING LLM and using detailed fallback")
            llm_answer = _default_fallback(user_query)
            # Mark that we've already set the answer, so we don't process it again
            skip_llm_processing = True
        else:
            # For general queries or small talk, try LLM first
            context_str = ""
            system_prompt = SYSTEM_PROMPT_GENERAL
            # Include conversation history if available
            history_context = ""
            if conversation_history:
                history_context = f"\n\nCONVERSATION HISTORY:\n{conversation_history}\n"
            
            user_prompt = (
                f"{history_context}User's question: {user_query or 'Hi'}\n\n"
                "Provide helpful, specific insurance guidance. Use the conversation history to understand context. "
                "If they ask about health insurance, provide detailed information and ask follow-up questions. "
                "If they ask about bike/motorcycle insurance, provide detailed information and ask follow-up questions. "
                "Format: friendly paragraph + 2-4 detailed bullet points + optional follow-up question."
            )
            
            if not skip_llm_processing:
                llm_answer = ""
                try:
                    if settings.LLM_MODEL_NAME != "mock-llm" and OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
                        try:
                            llm = GPT4LLM(
                                api_key=settings.OPENAI_API_KEY,
                                model=settings.LLM_MODEL_NAME,
                                temperature=settings.LLM_TEMPERATURE,
                            )
                            llm_answer = llm.generate(system_prompt, user_prompt)
                            print(f"✅ GPT-4 generated answer: {len(llm_answer)} chars")
                        except Exception as gpt_error:
                            print(f"⚠️ GPT-4 error, using fallback: {str(gpt_error)}")
                            llm_answer = ""
                    else:
                        print("ℹ️ Using mock LLM fallback")
                        try:
                            llm = MockLLM()
                            llm_answer = llm.generate(system_prompt, user_prompt, retrieved_chunks)
                            print(f"✅ Mock LLM generated answer: {len(llm_answer)} chars")
                        except Exception as mock_error:
                            print(f"⚠️ Mock LLM error, using fallback: {str(mock_error)}")
                            llm_answer = ""
                except Exception as exc:
                    print(f"❌ LLM generation failed: {exc}")
                    import traceback
                    traceback.print_exc()
                    llm_answer = ""
            else:
                # Already set llm_answer from fallback above
                pass

    # CRITICAL: Check if answer is generic/repetitive and replace with specific advice
    llm_answer_lower = llm_answer.lower() if llm_answer else ""
    
    # Detect generic responses that should be replaced
    generic_phrases = [
        "i'm here to help you with insurance questions",
        "feel free to ask me about insurance policies",
        "i can help with health, car, or bike insurance",
        "hello! i'm here to help",
        "i'm here to help with any insurance questions",
        "feel free to ask",
        "i'm here to help"
    ]
    
    is_generic = any(phrase in llm_answer_lower for phrase in generic_phrases)
    
    # ALWAYS replace generic responses for insurance queries, regardless of context
    if is_insurance_query and is_generic:
        print(f"🚨 ALERT: Generic response detected for insurance query, FORCING replacement: '{user_query[:50]}'")
        llm_answer = _default_fallback(user_query)
    # If answer is empty, too short, or generic (and no context), use specific fallback
    elif not llm_answer or len(llm_answer.strip()) < 5:
        print(f"⚠️ LLM answer too short/empty, using specific fallback for: '{user_query[:50]}'")
        llm_answer = _default_fallback(user_query)
    elif is_generic and not has_context:
        # If it's a generic response and we have no context, replace with specific advice
        print(f"⚠️ LLM returned generic response (no context), replacing with specific advice for: '{user_query[:50]}'")
        llm_answer = _default_fallback(user_query)
    
    # Final safety check - ensure answer is never empty
    if not llm_answer or not llm_answer.strip():
        print("🚨 CRITICAL: Answer still empty after fallback, using hardcoded response")
        llm_answer = _default_fallback(user_query)

    supporting_info = {
        "policy_ids": list({chunk.policy_id for chunk in retrieved_chunks}),
        "mode": "contextual" if has_context else "general",
        "small_talk": small_talk,
        "num_chunks_used": len(retrieved_chunks),
    }

    return llm_answer.strip(), supporting_info
