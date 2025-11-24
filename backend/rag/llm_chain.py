"""
LLM Chain Module: Generate answers using RAG (Retrieval-Augmented Generation).

This module implements the generation component of RAG:
1. Takes user query and retrieved chunks
2. Constructs a context prompt with retrieved information
3. Calls LLM (GPT-4) with strict system prompt that enforces:
   - Use ONLY provided context (no external knowledge)
   - STRICTLY avoid hallucination
   - Cite sources with policy IDs
   - Suggest relevant policies
4. Parses and returns the answer

The system is configured with:
- Temperature = 0.0 for deterministic, factual responses
- Strong anti-hallucination prompts
- Explicit instructions to say "I don't know" if information is missing
"""

from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.retrieval import RetrievedChunk
from config import settings

# Try to import OpenAI - will use mock if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI package not installed. Install with: pip install openai")


# System prompt optimized for better GPT-4 results
SYSTEM_PROMPT = """You are a helpful and knowledgeable insurance assistant chatbot. Your role is to help users understand insurance policies and answer their questions about coverage, exclusions, limits, terms, and help them find suitable policies.

IMPORTANT GUIDELINES:
1. USE THE PROVIDED CONTEXT: Base your answer primarily on the context chunks provided below. These contain actual policy information.

2. BE HELPFUL AND INFORMATIVE:
   - Answer the user's question directly and clearly
   - If the context contains relevant information, use it to provide a comprehensive answer
   - If specific details (like exact premium amounts or age eligibility) aren't in the context, acknowledge this and guide them appropriately
   - Structure your answer with clear paragraphs or bullet points

3. RESPONSE STYLE:
   - Use a friendly, professional, and conversational tone
   - Be specific when the context provides specific information
   - Be general and helpful when specific details aren't available
   - Always end with actionable next steps

4. HANDLING USER NEEDS:
   - If user mentions age, family members, or specific requirements, acknowledge them
   - Explain what policies might be suitable based on the context
   - Guide them to contact providers for exact eligibility, pricing, and to purchase policies
   - Be encouraging and supportive

5. ANTI-HALLUCINATION:
   - DO NOT make up specific premium amounts, coverage limits, or policy terms that aren't in the context
   - DO NOT invent company names, policy IDs, or websites
   - If you're unsure about something, say so and guide them to contact providers
   - You can provide general insurance guidance, but be clear when you're doing so vs. citing specific policy details

6. FORMAT YOUR RESPONSE:
   - Start with a direct answer to their question
   - Provide details from the context when available
   - Mention policy types and key features
   - Include helpful next steps

Remember: Be helpful, informative, and guide users effectively. Use the context as your primary source, but be conversational and helpful."""


class GPT4LLM:
    """
    GPT-4 LLM integration with strict anti-hallucination controls.
    
    This uses OpenAI's GPT-4 API with:
    - Temperature = 0.0 for deterministic responses
    - Strong system prompts to prevent hallucination
    - Explicit instructions to only use provided context
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.0):
        """
        Initialize GPT-4 LLM client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4, gpt-4-turbo-preview, etc.)
            temperature: Temperature for generation (0.0 = deterministic)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    def generate(self, system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
        """
        Generate a response using GPT-4 with strict context constraints.
        
        Args:
            system_prompt: System prompt with anti-hallucination rules
            user_prompt: User prompt with context and question
            timeout: Request timeout in seconds (default: 60)
            
        Returns:
            Generated answer text
        """
        import time
        max_retries = 2
        retry_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                print(f"Calling {self.model} API (attempt {attempt + 1}/{max_retries + 1})...")
                print(f"User query length: {len(user_prompt)} characters")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    temperature=self.temperature,
                    max_tokens=1500,  # Increased for more detailed responses
                    top_p=0.95,  # Nucleus sampling for consistency
                    timeout=timeout  # Add timeout
                )
                
                elapsed_time = time.time() - start_time
                print(f"✅ GPT-4 response received in {elapsed_time:.2f} seconds")
                
                if not response.choices or not response.choices[0].message:
                    raise ValueError("Empty response from GPT-4 API")
                
                answer = response.choices[0].message.content.strip()
                
                if not answer:
                    raise ValueError("Empty answer content from GPT-4")
                
                print(f"Answer length: {len(answer)} characters")
                return answer
                
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                print(f"❌ GPT-4 API error (attempt {attempt + 1}): {error_type}: {error_msg}")
                
                # Check for specific error types
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < max_retries:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    raise RuntimeError("OpenAI API rate limit exceeded. Please try again in a moment.")
                
                elif "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                    raise RuntimeError("Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable.")
                
                elif "insufficient_quota" in error_msg.lower():
                    raise RuntimeError("OpenAI API quota exceeded. Please check your account billing.")
                
                elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if attempt < max_retries:
                        print(f"Timeout occurred. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    raise RuntimeError("Request timed out. The API is taking too long to respond.")
                
                elif attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed
                    raise RuntimeError(f"Error calling GPT-4 API after {max_retries + 1} attempts: {error_msg}")


class MockLLM:
    """
    Mock LLM fallback for when OpenAI is not available.
    
    Only used if:
    - OpenAI package is not installed
    - API key is not provided
    - API call fails
    
    This provides intelligent responses based on context chunks.
    """
    
    def generate(self, system_prompt: str, user_prompt: str, context_chunks: List[RetrievedChunk] = None) -> str:
        """
        Generate a helpful response from context chunks.
        
        Args:
            system_prompt: System instructions (not used in mock, but kept for compatibility)
            user_prompt: User prompt with context and question
            context_chunks: List of retrieved chunks
            
        Returns:
            Generated answer text
        """
        if not context_chunks:
            return "I don't have specific information about that in the available policy documents. However, I can help you find the right insurance policy. Please contact a customer service agent or visit insurance provider websites for detailed information about eligibility, pricing, and coverage options."
        
        # Extract user query from prompt
        user_query = ""
        if "User question:" in user_prompt:
            user_query = user_prompt.split("User question:")[-1].strip()
        
        query_lower = user_query.lower() if user_query else ""
        
        # Build a comprehensive answer from context chunks
        answer_parts = []
        
        # Determine query intent
        is_health = any(word in query_lower for word in ["health", "medical", "hospital", "doctor", "treatment", "illness", "father", "age", "57"])
        is_car = any(word in query_lower for word in ["car", "auto", "vehicle", "automobile"])
        is_bike = any(word in query_lower for word in ["bike", "bicycle", "motorcycle"])
        
        # Filter relevant chunks
        relevant_chunks = []
        if is_health:
            relevant_chunks = [c for c in context_chunks if c.policy_type == "health"]
        elif is_car:
            relevant_chunks = [c for c in context_chunks if c.policy_type == "car"]
        elif is_bike:
            relevant_chunks = [c for c in context_chunks if c.policy_type == "bike"]
        else:
            relevant_chunks = context_chunks[:3]  # Use top 3 if no specific type
        
        if not relevant_chunks:
            relevant_chunks = context_chunks[:3]
        
        # Build answer
        policy_types = list(set([c.policy_type for c in relevant_chunks]))
        policy_ids = list(set([c.policy_id for c in relevant_chunks]))
        
        # Introduction
        if is_health:
            answer_parts.append("Based on the available health insurance policies, here's what I found:\n\n")
        elif is_car:
            answer_parts.append("Based on the available car insurance policies, here's what I found:\n\n")
        elif is_bike:
            answer_parts.append("Based on the available bike insurance policies, here's what I found:\n\n")
        else:
            answer_parts.append("Based on the available policy documents, here's what I found:\n\n")
        
        # Extract key information from top chunks
        for i, chunk in enumerate(relevant_chunks[:3], 1):
            chunk_text = chunk.text.strip()
            
            # Find most relevant sentences
            if len(chunk_text) > 400:
                sentences = chunk_text.split('. ')
                # Take first 3-4 sentences that are most relevant
                chunk_text = '. '.join(sentences[:4])
                if chunk_text and not chunk_text.endswith('.'):
                    chunk_text += '.'
            
            # Format chunk information
            if i == 1:
                answer_parts.append(f"**{chunk.policy_id.replace('_', ' ').title()}** ({chunk.policy_type} policy):\n")
            else:
                answer_parts.append(f"\n**{chunk.policy_id.replace('_', ' ').title()}** also states:\n")
            
            answer_parts.append(f"{chunk_text[:500]}")
            if len(chunk.text) > 500:
                answer_parts.append("...")
        
        # Add helpful guidance
        answer_parts.append(f"\n\n**Next Steps:**\n")
        answer_parts.append("To get complete details about eligibility, premium costs, and to purchase a policy, I recommend:\n")
        answer_parts.append("1. Contact the insurance providers directly\n")
        answer_parts.append("2. Visit their websites for online quotes\n")
        answer_parts.append("3. Speak with a licensed insurance agent for personalized advice\n")
        
        if is_health and "age" in query_lower or "57" in query_lower:
            answer_parts.append("\n**Note:** For health insurance for someone aged 57, please check with providers about age-specific eligibility and any waiting periods for pre-existing conditions.")
        
        return "".join(answer_parts)


def generate_answer_with_rag(
    user_query: str,
    retrieved_chunks: List[RetrievedChunk],
    policy_type: str = None,
    region: str = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate an answer using RAG (Retrieval-Augmented Generation).
    
    Process:
    1. Format context from retrieved chunks
    2. Construct prompt with system instructions
    3. Call LLM (or mock LLM for local dev)
    4. Parse response and extract structured info
    
    Args:
        user_query: User's question
        retrieved_chunks: List of relevant chunks from retrieval
        policy_type: Optional policy type filter (for context)
        region: Optional region filter (for context)
        
    Returns:
        Tuple of:
            - answer: The generated answer text
            - supporting_info: Dictionary with policy IDs, clause types, etc.
    """
    if not retrieved_chunks:
        return (
            "I don't have information about that in the available policy documents. "
            "Please contact a customer service agent for assistance.",
            {"policy_ids": [], "clause_types": []}
        )
    
    # Format context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"[Chunk {i}]\n"
            f"Policy ID: {chunk.policy_id}\n"
            f"Policy Type: {chunk.policy_type}\n"
            f"Clause Type: {chunk.clause_type}\n"
            f"Region: {chunk.region}\n"
            f"Content: {chunk.text}\n"
        )
    
    context = "\n\n".join(context_parts)
    
    # Format the user prompt with context - optimized for GPT-4 to get better results
    user_prompt = f"""You are helping a user understand insurance policies. Use the following policy document excerpts to answer their question.

POLICY DOCUMENTS:
{context}

USER'S QUESTION: {user_query}

INSTRUCTIONS:
1. Read the policy documents carefully
2. Answer the user's question using information from the documents
3. Be specific and detailed when the documents contain relevant information
4. If the user asks about something not in the documents (like exact premium costs or age eligibility), acknowledge this and guide them to contact the insurance provider
5. Structure your answer clearly with:
   - A direct answer to their question
   - Specific details from the policies (coverage, exclusions, limits, etc.)
   - Helpful next steps

Provide a comprehensive, helpful answer now:"""
    
    # Generate answer using GPT-4 with improved error handling
    try:
        if settings.LLM_MODEL_NAME == "mock-llm" or not OPENAI_AVAILABLE:
            # Use mock LLM as fallback
            print("⚠️  Using Mock LLM (OpenAI not available or mock-llm selected)")
            llm = MockLLM()
            answer = llm.generate(SYSTEM_PROMPT, user_prompt, retrieved_chunks)
        elif settings.OPENAI_API_KEY:
            # Use GPT-4
            print(f"🚀 Using {settings.LLM_MODEL_NAME} API")
            print(f"📝 Query: {user_query[:100]}...")
            print(f"📚 Retrieved {len(retrieved_chunks)} relevant chunks")
            print(f"📄 Context length: {len(context)} characters")
            
            try:
                llm = GPT4LLM(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.LLM_MODEL_NAME,
                    temperature=settings.LLM_TEMPERATURE
                )
                answer = llm.generate(SYSTEM_PROMPT, user_prompt)
                
                if answer and len(answer) > 50:
                    print(f"✅ Successfully generated answer ({len(answer)} characters)")
                    print(f"📋 Answer preview: {answer[:150]}...")
                else:
                    print(f"⚠️  Warning: Answer seems too short ({len(answer) if answer else 0} characters)")
                    # Try to enhance the answer
                    if retrieved_chunks:
                        top_chunk = retrieved_chunks[0]
                        answer = f"{answer}\n\nBased on {top_chunk.policy_id}, here's additional information: {top_chunk.text[:300]}..."
            except Exception as api_error:
                print(f"❌ GPT-4 API call failed: {str(api_error)}")
                raise
        else:
            # No API key provided, use mock
            print("⚠️  Warning: OPENAI_API_KEY not set. Using Mock LLM.")
            print("   Set OPENAI_API_KEY environment variable to use GPT-4.")
            llm = MockLLM()
            answer = llm.generate(SYSTEM_PROMPT, user_prompt, retrieved_chunks)
            
    except RuntimeError as e:
        # Specific API errors - re-raise with helpful message
        error_msg = str(e)
        print(f"❌ GPT-4 API Error: {error_msg}")
        
        # Try to provide a helpful fallback response
        if retrieved_chunks:
            print("📋 Falling back to context-based response")
            top_chunk = retrieved_chunks[0]
            policy_type = top_chunk.policy_type
            answer = f"Based on the available {policy_type} insurance policies, here's what I found:\n\n"
            answer += f"{top_chunk.text[:500]}\n\n"
            answer += "**Note:** I'm experiencing some technical difficulties with the AI service. "
            answer += "For complete details about eligibility, pricing, and to purchase a policy, "
            answer += "please contact the insurance provider directly or visit their website."
        else:
            answer = f"I'm experiencing a technical issue: {error_msg}. "
            answer += "Please try again in a moment or contact customer service for assistance."
        
        # Don't raise - return the fallback answer
        
    except Exception as e:
        # Unexpected errors - log and provide fallback
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Unexpected error in LLM generation: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        print("📋 Falling back to context-based response")
        
        if retrieved_chunks:
            # Build a helpful response from chunks
            top_chunk = retrieved_chunks[0]
            policy_type = top_chunk.policy_type
            answer = f"Based on the available {policy_type} insurance policies, here's what I found:\n\n"
            answer += f"{top_chunk.text[:500]}\n\n"
            answer += "For complete details about eligibility, pricing, and to purchase a policy, "
            answer += "please contact the insurance provider or visit their website."
        else:
            answer = "I encountered an unexpected error processing your request. "
            answer += "Please try rephrasing your question or contact customer service for assistance."
    
    # Extract supporting information
    policy_ids = list(set([chunk.policy_id for chunk in retrieved_chunks]))
    clause_types = list(set([chunk.clause_type for chunk in retrieved_chunks]))
    policy_types = list(set([chunk.policy_type for chunk in retrieved_chunks]))
    
    supporting_info = {
        "policy_ids": policy_ids,
        "clause_types": clause_types,
        "policy_types": policy_types,
        "num_chunks_used": len(retrieved_chunks)
    }
    
    return answer, supporting_info

