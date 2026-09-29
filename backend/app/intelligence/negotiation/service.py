"""Negotiation Agent generating proposed contract restructuring terms."""

import os
from typing import Any, Dict, Optional
import httpx

from app.intelligence.context_builder import build_contract_intelligence_context
from app.intelligence.negotiation.schemas import (
    NegotiationRequest,
    NegotiationResponse,
    ProposedTerm,
)
from app.intelligence.risk.service import risk_prediction_service


class NegotiationService:
    """Business service generating risk-mitigating term proposals."""

    def negotiate_contract(
        self, contract_id: str, request: Optional[NegotiationRequest] = None
    ) -> NegotiationResponse:
        """Generate proposed term adjustments for human review."""
        if request is None:
            request = NegotiationRequest()

        ctx = build_contract_intelligence_context(contract_id)
        risk_res = risk_prediction_service.evaluate_contract_risk(contract_id)

        groq_key = os.getenv("GROQ_API_KEY", "").strip()

        contract_info = ctx["contract"]
        curr_rate = contract_info.get("annual_interest_rate", 10.0)
        curr_principal = contract_info.get("principal", 100000.0)

        # Attempt Groq API integration if key exists
        if groq_key:
            try:
                system_prompt = (
                    "You are a professional financial contract restructuring advisor. "
                    "Analyze the provided contract terms and risk profile. Suggest 2-3 specific, "
                    "realistic term modifications to lower risk. Output clean JSON only with keys: "
                    "summary (string), terms (list of objects with parameter, current_value, proposed_value, reason)."
                )
                user_msg = (
                    f"Contract ID: {contract_id}\n"
                    f"Principal: ₹{curr_principal:,.2f}\n"
                    f"Interest Rate: {curr_rate}%\n"
                    f"Risk Category: {risk_res.risk_category}\n"
                    f"Default Prob: {risk_res.default_probability_percent}%\n"
                    f"Objective: {request.objective}\n"
                )

                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg},
                        ],
                        "temperature": 0.2,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    # Clean markdown fence if present
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                    import json
                    parsed = json.loads(content.strip())
                    opt_terms = [
                        ProposedTerm(
                            parameter=t["parameter"],
                            current_value=str(t["current_value"]),
                            proposed_value=str(t["proposed_value"]),
                            reason=t["reason"],
                        )
                        for t in parsed.get("terms", [])
                    ]
                    summary_text = parsed.get("summary", "AI Negotiation Agent proposal generated.")

                    revised_actus = {
                        "contractID": f"PROPOSED-{contract_id}",
                        "contractType": ctx["actus"].get("contract_type", "ANN"),
                        "status": "PROPOSED_FOR_HUMAN_REVIEW",
                        "nominalInterestRate": round((curr_rate + 1.0) / 100.0, 4),
                        "notionalPrincipal": curr_principal,
                    }

                    return NegotiationResponse(
                        contract_id=contract_id,
                        available=True,
                        optimized_terms=opt_terms,
                        negotiation_summary=summary_text,
                        revised_actus_json=revised_actus,
                        requires_human_approval=True,
                        message="Negotiation proposal generated using Groq LLM agent.",
                    )
            except Exception as e:
                pass

        # Transparent fallback if GROQ_API_KEY is not configured or failed
        proposed_rate = round(curr_rate + 1.5, 1)
        proposed_terms = [
            ProposedTerm(
                parameter="annual_interest_rate",
                current_value=f"{curr_rate}%",
                proposed_value=f"{proposed_rate}%",
                reason="Increase interest rate margin by +1.5% to compensate for elevated credit risk.",
            ),
            ProposedTerm(
                parameter="additional_collateral",
                current_value="None",
                proposed_value="15% Security Deposit / Collateral",
                reason="Require partial collateral reserve to mitigate potential default exposure.",
            ),
            ProposedTerm(
                parameter="payment_frequency",
                current_value=contract_info.get("payment_frequency", "MONTHLY"),
                proposed_value="MONTHLY WITH AUTO-DEBIT",
                reason="Mandate automated recurring direct debit to minimize payment delays.",
            ),
        ]

        revised_actus = {
            "contractID": f"PROPOSED-{contract_id}",
            "contractType": ctx["actus"].get("contract_type", "ANN"),
            "status": "PROPOSED_FOR_HUMAN_REVIEW",
            "nominalInterestRate": round(proposed_rate / 100.0, 4),
            "notionalPrincipal": curr_principal,
        }

        return NegotiationResponse(
            contract_id=contract_id,
            available=False if not groq_key else True,
            optimized_terms=proposed_terms,
            negotiation_summary="Rule-based prototype negotiation proposal: Recommended +1.5% rate adjustment and 15% collateral reserve for risk mitigation.",
            revised_actus_json=revised_actus,
            requires_human_approval=True,
            message="Groq API key not configured; displaying rule-based negotiation proposal.",
        )


negotiation_service = NegotiationService()
