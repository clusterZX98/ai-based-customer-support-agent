import os
import re
import json
import uuid
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI

from agent.prompts import SYSTEM_PROMPT
from tools.knowledge_search import search_knowledge_base
from tools.customer_lookup import get_customer
from tools.order_lookup import get_order
from tools.escalation import escalate_to_human

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0.2,
    thinking_level="minimal",
)

def _extract_text(content) -> str:
    """
    Gemini 3.x can return content as a plain string OR as a list of
    content blocks, e.g. [{'type': 'text', 'text': '...', 'extras': {...}}].
    Pull only the actual text out, ignore signatures/extras/thinking blocks.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)

    return str(content)

# ---------------------------------------------------------------------------
# PART 16 -- Intent schema
# ---------------------------------------------------------------------------
class IntentResult(BaseModel):
    intent: Literal[
        "FAQ",
        "ORDER",
        "PAYMENT",
        "REFUND",
        "CANCELLATION",
        "COMPLAINT",
        "OTHER",
    ]
    confidence: float = Field(ge=0, le=1)
    reason: str


# ---------------------------------------------------------------------------
# PART 17 -- Intent classifier
# ---------------------------------------------------------------------------
def classify_intent(state):
    user_message = state.get("user_message", "")

    classifier = llm.with_structured_output(IntentResult)

    prompt = f"""
Classify the customer's request.

Customer message:
{user_message}

Choose exactly one intent:
FAQ
ORDER
PAYMENT
REFUND
CANCELLATION
COMPLAINT
OTHER

Return the intent, confidence and a short reason.
"""

    result = classifier.invoke(prompt)

    return {
        "intent": result.intent,
        "confidence": result.confidence,
        "agent_steps": ["Intent classified"],
    }


# ---------------------------------------------------------------------------
# PART 18 -- Load long-term memory
# ---------------------------------------------------------------------------
def load_memory(state, config, *, store):
    user_id = state.get("user_id", "anonymous")
    user_message = state.get("user_message", "")

    namespace = ("users", user_id, "memories")

    results = store.search(namespace, query=user_message, limit=5)

    memory_text = []
    for item in results:
        value = item.value
        if isinstance(value, dict):
            text = value.get("text", str(value))
        else:
            text = str(value)
        memory_text.append(text)

    return {
        "memories": memory_text,
        "agent_steps": ["Long-term memory retrieved"],
    }


# ---------------------------------------------------------------------------
# PART 19 -- Knowledge retrieval
# ---------------------------------------------------------------------------
def retrieve_knowledge(state):
    intent = state.get("intent", "OTHER")
    user_message = state.get("user_message", "")

    if intent in {"FAQ", "REFUND", "PAYMENT", "CANCELLATION", "COMPLAINT"}:
        context = search_knowledge_base(user_message)
    else:
        context = ""

    return {
        "knowledge_context": context,
        "agent_steps": ["Knowledge base searched"],
    }


# ---------------------------------------------------------------------------
# PART 20 -- Customer lookup
# ---------------------------------------------------------------------------
def lookup_customer(state):
    user_id = state.get("user_id")

    if not user_id:
        return {
            "customer_data": {},
            "agent_steps": ["Customer ID unavailable"],
        }

    customer = get_customer(user_id)

    return {
        "customer_data": customer,
        "agent_steps": ["Customer information retrieved"],
    }


# ---------------------------------------------------------------------------
# PART 21 -- Order lookup
# ---------------------------------------------------------------------------
def lookup_order(state):
    user_message = state.get("user_message", "")

    match = re.search(r"ORD\d+", user_message.upper())

    if not match:
        return {
            "order_data": {},
            "agent_steps": ["No order ID found"],
        }

    order_id = match.group()
    order = get_order(order_id)

    return {
        "order_data": order,
        "agent_steps": [f"Order {order_id} retrieved"],
    }


# ---------------------------------------------------------------------------
# PART 22 -- Human escalation check
# ---------------------------------------------------------------------------
HIGH_RISK_WORDS = [
    "fraud",
    "scam",
    "double charged",
    "charged twice",
    "duplicate payment",
    "lawsuit",
    "legal",
    "angry",
    "complaint",
    "terrible",
]

LOW_CONFIDENCE_THRESHOLD = 0.55


def check_escalation(state):
    intent = state.get("intent", "OTHER")
    user_message = state.get("user_message", "").lower()
    confidence = state.get("confidence", 0)
    customer_data = state.get("customer_data", {}) or {}

    risky = any(word in user_message for word in HIGH_RISK_WORDS)
    low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD

    requires_human = bool(
        risky or intent == "COMPLAINT" or low_confidence
    )

    steps = ["Escalation checked"]
    ticket_data = {}

    if requires_human:
        customer_id = customer_data.get("customer_id", state.get("user_id", "unknown"))
        reason = f"Intent={intent}, confidence={confidence:.2f}. Message: {state.get('user_message', '')}"

        result = escalate_to_human(
            customer_id=customer_id,
            reason=reason,
            priority="High" if risky else "Medium",
        )
        ticket_data = result.get("ticket", {})
        steps.append(f"Escalated to human ({ticket_data.get('ticket_id', 'unknown')})")

    return {
        "requires_human": requires_human,
        "ticket_data": ticket_data,
        "agent_steps": steps,
    }


# ---------------------------------------------------------------------------
# PART 23 -- Response generator
# ---------------------------------------------------------------------------
def generate_response(state):
    intent = state.get("intent", "OTHER")
    user_message = state.get("user_message", "")
    human_required = state.get("requires_human", False)
    memory_text = state.get("memories", [])
    knowledge = state.get("knowledge_context", "")
    customer = state.get("customer_data", {})
    order = state.get("order_data", {})

    prompt = f"""
{SYSTEM_PROMPT}

CURRENT CUSTOMER REQUEST:
{user_message}

INTENT:
{intent}

LONG-TERM MEMORY:
{memory_text if memory_text else "No relevant memories found."}

KNOWLEDGE BASE:
{knowledge if knowledge else "No relevant knowledge-base information found."}

CUSTOMER DATA:
{json.dumps(customer, indent=2)}

ORDER DATA:
{json.dumps(order, indent=2)}

HUMAN ESCALATION REQUIRED:
{human_required}

Generate the best customer-facing response.
If human escalation is required:
- Clearly explain that the issue needs human review.
- Do not pretend that a human has already reviewed it.
- Do not claim a refund or payment reversal has occurred.
Keep the answer professional and reasonably concise.
"""

    response = llm.invoke(prompt)
    text = _extract_text(response.content)

    return {
        "response": text.strip(),
        "agent_steps": ["Response generated"],
    }


# ---------------------------------------------------------------------------
# PART 24 -- Memory extraction
# ---------------------------------------------------------------------------
class MemoryExtraction(BaseModel):
    should_save: bool
    memories: list[str]


def extract_memory(state):
    user_message = state.get("user_message", "")
    response = state.get("response", "")

    extractor = llm.with_structured_output(MemoryExtraction)

    prompt = f"""
You are a long-term memory extraction system.

Analyze this customer interaction.

USER:
{user_message}

ASSISTANT:
{response}

Extract only information that is useful in future conversations.
Good memories include:
- Customer name
- Language preference
- Communication preference
- Relevant product preferences
- Important recurring issues
- Important customer context

Do NOT save:
- Greetings
- Temporary details
- One-time conversational filler
- The assistant's generic statements
- Sensitive information that is unnecessary

Return should_save=true only if useful durable information exists.
"""

    result = extractor.invoke(prompt)

    return {
        "memory_candidates": result.memories if result.should_save else [],
        "agent_steps": ["Memory extraction analyzed"],
    }


# ---------------------------------------------------------------------------
# PART 25 -- Save long-term memory
# ---------------------------------------------------------------------------
def save_memory(state, config, *, store):
    user_id = state.get("user_id", "anonymous")
    candidates = state.get("memory_candidates", [])

    namespace = ("users", user_id, "memories")

    for memory in candidates:
        memory_id = str(uuid.uuid4())
        store.put(namespace, memory_id, {"text": memory})

    return {
        "agent_steps": ["Long-term memory updated"],
    }