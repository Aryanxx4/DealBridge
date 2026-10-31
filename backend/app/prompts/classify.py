"""Product-chat question classification (fast model)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag

PROMPT_VERSION = "classify.v1"
TOOL = "classify_question"

Intent = Literal["PRODUCT_SPECIFIC", "GENERAL_EDUCATIONAL", "REQUIREMENT_STATEMENT", "OUT_OF_SCOPE", "SMALL_TALK"]


class Classification(BaseModel):
    intent: Intent
    standalone_question: str = Field(description="The question rewritten to stand alone")
    category: Literal["deployment", "architecture", "security", "platform", "integrations", "concepts", "OTHER"] = "OTHER"
    mentions_certification: bool = False
    certification_terms: list[str] = Field(default_factory=list)


SYSTEM = f"""You classify questions asked in DealBridge, a tool that helps buyers evaluate the IOMETE data lakehouse platform.

Return:
- intent:
  - PRODUCT_SPECIFIC: asks what IOMETE does, supports, integrates with, how it is deployed, secured or used. "Does IOMETE support X?" is PRODUCT_SPECIFIC.
  - GENERAL_EDUCATIONAL: asks about a general concept (for example "what is a lakehouse?") without asking about IOMETE specifically.
  - REQUIREMENT_STATEMENT: the user states their own need or constraint instead of asking ("We need X", "Our data must stay in our data center").
  - OUT_OF_SCOPE: unrelated to data platforms, IOMETE or evaluating it (for example weather, coding homework, other vendors' pricing).
  - SMALL_TALK: greetings, thanks, pleasantries.
- standalone_question: the latest question rewritten so it can be understood without the conversation. Resolve pronouns from earlier
  messages. Preserve every qualifier (product version, deployment environment, customer conditions, numbers). Remove personal names,
  company names and e-mail addresses. Do not add any fact that the user did not state.
- category: one of deployment, architecture, security, platform, integrations, concepts, OTHER.
- mentions_certification: true if the question asks about a certification, compliance status, regulation or standard
  (for example SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR, FedRAMP, or an internal standard).
- certification_terms: the certification or standard names copied exactly as written in the question.

{SHARED_RULES}"""


def build_messages(history: list[dict], question: str) -> list[dict]:
    convo = "\n".join(f"{m['role'].lower()}: {m['content'][:800]}" for m in history[-6:])
    return [
        {
            "role": "user",
            "content": (
                tag("conversation", convo or "(no earlier messages)") + "\n\n" + tag("question", question) + "\n\nClassify the question."
            ),
        }
    ]
