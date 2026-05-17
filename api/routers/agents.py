"""
Smart Doctor Connect AI — Agentic Routing
"""

from __future__ import annotations
import json

from fastapi import APIRouter, HTTPException
from api.database import get_db
from api.models import AgentMatchRequest, AgentMatchResponse
from api.routers.chat import _score_doctor, _doc_to_response
from api.services.recommender import SymptomRecommender

router = APIRouter(prefix="/agents", tags=["agents"])
recommender = SymptomRecommender()

@router.post(
    "/match-doctor",
    response_model=AgentMatchResponse,
    summary="Agentic Doctor Matching",
)
async def match_doctor_agent(payload: AgentMatchRequest):
    """
    Takes a finalized triage summary, extracts specialties via LLM, 
    and queries MongoDB to find the top 2 best matches.
    """
    db = await get_db()
    llm = recommender._get_llm()
    
    specializations = []
    reasoning = "Based on standard routing."
    
    if llm:
        prompt = f"""You are a Smart Doctor-Matching Specialist Agent.
Analyze this triage summary:
"{payload.triage_summary}"

What 1-2 medical specializations (e.g., Cardiologist, Neurologist, General Physician) are best suited for this?
Also provide a 1-sentence reasoning for the patient.

Respond ONLY in valid JSON format:
{{
  "specializations": ["Spec1", "Spec2"],
  "reasoning": "1 sentence explanation"
}}"""
        try:
            from langchain_core.messages import HumanMessage
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            text = response.content.strip()
            # Strip markdown blocks if present
            if text.startswith("```json"):
                text = text.replace("```json", "", 1)
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text.strip())
            specializations = data.get("specializations", [])
            reasoning = data.get("reasoning", "Routing based on AI analysis.")
        except Exception as e:
            print(f"Match Agent error: {e}")
            specializations = ["General Physician"]
    else:
        specializations = ["General Physician"]
        
    # Query MongoDB for these doctors
    import re
    spec_filters = [
        {"specialization": {"$regex": re.escape(s), "$options": "i"}}
        for s in specializations
    ]
    mongo_query = {"$or": spec_filters} if spec_filters else {}
    
    cursor = db.doctors.find(mongo_query).limit(10)
    raw_docs = await cursor.to_list(length=10)
    
    if not raw_docs:
        cursor = db.doctors.find({"is_available": True}).limit(5)
        raw_docs = await cursor.to_list(length=5)
        
    scored = sorted(
        [(_score_doctor(d, specializations, payload.patient_location), d) for d in raw_docs],
        key=lambda x: x[0],
        reverse=True,
    )
    
    top_doctors = [_doc_to_response(doc, score) for score, doc in scored[:2]]
    
    return AgentMatchResponse(
        doctors=top_doctors,
        reasoning=reasoning
    )
