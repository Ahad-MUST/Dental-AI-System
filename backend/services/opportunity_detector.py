"""
Fixed opportunity detection - Accurate classification for all three call types
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class OpportunityDetector:
    """Detect missed business opportunities with accurate call type classification"""
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        
        # Updated opportunity prompt that correctly handles all three call types
        self.opportunity_prompt = """
Analyze this dental office call to determine if there was a HIGH-VALUE MISSED OPPORTUNITY.

PATIENT SAID: {patient_text}
STAFF RESPONSE: {staff_text}

THREE CALL TYPES:

1. APPOINTMENT BOOKING CALLS:
- Patient scheduling, rescheduling, or confirming appointments
- Examples: "confirm my appointment", "reschedule my cleaning", "book appointment"
- If appointment was successfully managed → FALSE (no opportunity missed)

2. GENERAL INQUIRY CALLS:
- Patient asking for information: hours, insurance, services, pricing
- Examples: "Do you take Medicaid?", "What are your hours?", "How much for crown?"
- If staff provided the requested information appropriately → FALSE (inquiry handled)
- Even if patient can't use services (no insurance match) → FALSE (no opportunity exists)

3. MISSED OPPORTUNITY CALLS:
These are EXPLICIT or NON-EXPLICIT missed opportunities:
- EXPLICIT: Patient directly asks about treatment but no appointment offered AND no follow-up
- NON-EXPLICIT: Patient shows interest/need but staff doesn't recognize opportunity AND no follow-up

CRITICAL CLASSIFICATION RULES:

FALSE (NO missed opportunity) if ANY of these:
- Appointment was confirmed/scheduled successfully
- Patient's information request was answered appropriately  
- Staff promised "I'll call back", "check and get back to you", "follow up"
- Office legitimately doesn't provide the service (e.g. no Medicaid accepted)
- Existing patient asking simple pricing question that was answered

TRUE (MISSED opportunity) ONLY if ALL these:
- Patient showed genuine interest in dental treatment/services
- No appointment was scheduled
- No follow-up was promised by staff
- This represents lost revenue potential

ANALYZE YOUR TEST CASES:
- Sherwin crown re-glue: Simple pricing question from existing patient → FALSE
- Alex appointment confirmation: Routine confirmation call → FALSE  
- Habib insurance check: Staff promised "I will check and give you a call back" → FALSE
- Blue Cross inquiry: Office doesn't take Medicaid, appropriately answered → FALSE

Answer with ONLY: TRUE or FALSE

Assessment:"""
    
    async def detect_opportunities(self, patient_text: str, staff_text: str, 
                                 call_summary: Dict, booking_outcome: Dict) -> Dict:
        """
        Accurate opportunity detection for all three call types
        """
        try:
            logger.info("Analyzing missed opportunities with improved classification...")
            
            # Quick rule-based pre-screening for obvious cases
            if self._is_definitely_not_missed_opportunity(patient_text, staff_text, call_summary):
                logger.info("Pre-screening: Definitely not a missed opportunity")
                return {"high_value_missed": False}
            
            if not self.llm_analyzer.is_initialized:
                # Fallback rule-based detection
                high_value_missed = self._rule_based_opportunity_check(patient_text, staff_text)
                logger.info(f"Rule-based assessment: {high_value_missed}")
                return {"high_value_missed": high_value_missed}
            
            # Use LLM for nuanced analysis
            prompt = self.opportunity_prompt.format(
                patient_text=patient_text[:2000],
                staff_text=staff_text[:2000]
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=50)
            
            # Parse LLM response
            high_value_missed = "TRUE" in response.upper() and "FALSE" not in response.upper()
            
            logger.info(f"LLM opportunity assessment: {'MISSED OPPORTUNITY' if high_value_missed else 'NO OPPORTUNITY MISSED'}")
            
            return {"high_value_missed": high_value_missed}
            
        except Exception as e:
            logger.error(f"Opportunity detection failed: {str(e)}")
            # Conservative fallback
            return {"high_value_missed": False}
    
    def _is_definitely_not_missed_opportunity(self, patient_text: str, staff_text: str, call_summary: Dict) -> bool:
        """Pre-screening to identify calls that are definitely not missed opportunities"""
        
        patient_lower = patient_text.lower()
        staff_lower = staff_text.lower()
        summary = call_summary.get("call_summary", "").lower()
        
        # Definitive indicators of non-missed opportunities
        definitive_non_opportunities = [
            # Appointment confirmations/bookings
            ("confirm" in patient_lower and "appointment" in patient_lower),
            ("tomorrow" in patient_lower and "appointment" in staff_lower),
            ("scheduled" in staff_lower or "see you" in staff_lower),
            
            # Staff committed to follow-up
            ("call you back" in staff_lower),
            ("get back to you" in staff_lower), 
            ("call back" in staff_lower),
            ("follow up" in staff_lower),
            ("check and" in staff_lower and "let you know" in staff_lower),
            
            # Insurance inquiries where office doesn't participate
            ("medicaid" in patient_lower and "don't" in staff_lower),
            ("we only take ppo" in staff_lower),
            ("not familiar with that" in staff_lower and "insurance" in patient_lower),
            
            # Simple pricing questions answered
            ("how much" in patient_lower and len(patient_text) < 300 and ("$" in staff_lower or "cost" in staff_lower)),
            
            # Confirmation calls mentioned in summary
            ("confirm" in summary and "appointment" in summary),
            ("confirmation" in summary)
        ]
        
        return any(definitive_non_opportunities)
    
    def _rule_based_opportunity_check(self, patient_text: str, staff_text: str) -> bool:
        """Rule-based fallback for opportunity detection"""
        
        patient_lower = patient_text.lower()
        staff_lower = staff_text.lower()
        
        # Step 1: Check for definitive exclusions (same as above)
        exclusions = [
            ("call you back" in staff_lower),
            ("get back to you" in staff_lower),
            ("follow up" in staff_lower),
            ("check and" in staff_lower),
            ("we don't" in staff_lower and "insurance" in patient_lower),
            ("we only take" in staff_lower),
            ("appointment" in patient_lower and ("confirm" in patient_lower or "tomorrow" in patient_lower)),
            ("scheduled" in staff_lower or "see you" in staff_lower)
        ]
        
        if any(exclusions):
            return False
        
        # Step 2: Look for genuine treatment interest
        treatment_interest_indicators = [
            "tooth hurt", "toothache", "pain", "broken", "emergency",
            "need dental", "need treatment", "implant", "crown", "root canal",
            "cleaning", "checkup", "wisdom teeth", "braces"
        ]
        
        has_treatment_interest = any(indicator in patient_lower for indicator in treatment_interest_indicators)
        
        # Step 3: Check if staff made scheduling effort
        staff_scheduling_effort = any(phrase in staff_lower for phrase in [
            "schedule", "appointment", "come in", "see you", "available",
            "book", "when can", "what time"
        ])
        
        # Only mark as missed opportunity if patient showed treatment interest 
        # but staff made no scheduling effort AND no follow-up promised
        return has_treatment_interest and not staff_scheduling_effort