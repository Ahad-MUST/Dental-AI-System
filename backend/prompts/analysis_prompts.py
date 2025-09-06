"""
LLM Analysis Prompts for Dental Call Evaluation - Fixed for Accurate Classification
"""

class AnalysisPrompts:
    """Collection of prompts for different analysis tasks"""
    
    CALL_SUMMARY_PROMPT = """
Analyze this dental office phone call and provide a comprehensive summary.

CALL TRANSCRIPT:
{transcript}

Provide a detailed analysis covering:
1. What was the main purpose of this call?
2. What dental services or treatments were discussed?
3. What concerns, problems, or pain did the patient express?
4. How well did the staff handle the patient's needs?
5. Was an appointment successfully scheduled?
6. Rate the overall call quality (1-10 scale)

ANALYSIS:
"""

    PERFORMANCE_SCORING_PROMPT = """
You are evaluating a dental office staff member's call performance. Be FAIR and REALISTIC in your scoring.

CALL TYPE: {call_type}
PATIENT SAID: {patient_text}
STAFF RESPONSE: {staff_text}

EVALUATION CRITERIA:
{evaluation_criteria}

SCORING SCALE (be realistic):
- 90-100: Exceptional performance (rare, everything perfect)
- 80-89: Good performance (above average, meets expectations well)  
- 70-79: Satisfactory performance (meets basic expectations)
- 60-69: Below expectations (some issues but not terrible)
- 50-59: Poor performance (significant issues)
- Below 50: Unacceptable (major problems)

IMPORTANT: 
- If staff accomplished the main goal for this call type, score should be 70+ minimum
- Routine calls handled appropriately should score 75-80
- Don't penalize staff for situations outside their control (like insurance not accepted)

Rate the following components:
{scoring_components}

OVERALL_ASSESSMENT: [Your fair assessment considering real-world context]
STRENGTHS: [What the staff did well - be specific]
WEAKNESSES: [Areas for improvement - be constructive]
COACHING_FOCUS: [Top 2-3 specific areas for coaching]
"""

    # FIXED: More accurate opportunity detection prompt
    OPPORTUNITY_DETECTION_PROMPT = """
Analyze this dental office call for missed business opportunities.

PATIENT SAID: {patient_text}
STAFF RESPONSE: {staff_text}

CALL TYPE ANALYSIS:

1. APPOINTMENT BOOKING CALLS:
- Patient scheduling, confirming, or rescheduling appointments
- If appointment was managed successfully → NO MISSED OPPORTUNITY

2. GENERAL INQUIRY CALLS:
- Patient asking about hours, location, insurance, services, pricing  
- If staff provided appropriate information → NO MISSED OPPORTUNITY
- Even if services aren't available (e.g., no Medicaid) → NO MISSED OPPORTUNITY

3. MISSED OPPORTUNITY CALLS:
Look for these specific missed opportunities:
- Patient expressed treatment need but no appointment offered AND no follow-up promised
- Patient had dental pain/emergency but no urgent care offered AND no callback promised  
- Patient showed interest in services but staff didn't attempt scheduling AND no follow-up
- New patient ready to book but staff didn't facilitate AND no follow-up

CRITICAL EXCLUSIONS (NOT missed opportunities):
- Staff promised "I'll call back", "check insurance and get back to you"
- Office legitimately doesn't accept patient's insurance  
- Routine confirmation calls handled appropriately
- Simple pricing questions answered appropriately
- Existing patient maintenance calls

For each potential missed opportunity, determine:
- What specific opportunity was missed?
- How urgent is this opportunity? (critical/high/medium/low)
- What should the staff have done differently?
- What's the potential revenue impact?

MISSED OPPORTUNITIES ANALYSIS:
"""

    BOOKING_OUTCOME_PROMPT = """
Determine the booking outcome for this dental office call.

PATIENT: {patient_text}
STAFF: {staff_text}

Answer these questions:
1. Did the patient want to schedule an appointment? (Yes/No/Unclear)
2. Did the staff attempt to book an appointment? (Yes/No)
3. Was an appointment successfully scheduled? (Yes/No/Unclear)
4. If no appointment was made, what prevented it? (price, timing, fear, insurance, etc.)
5. What was the final outcome?

BOOKING ANALYSIS:
"""

    @classmethod
    def get_evaluation_criteria(cls, call_type: str) -> str:
        """Get evaluation criteria specific to call type"""
        
        criteria_map = {
            "appointment_booking": """
APPOINTMENT BOOKING CALL:
- Greeting & Professionalism (20%): Professional introduction, friendly tone
- Patient Needs Understanding (20%): Listening to scheduling needs, showing flexibility
- Scheduling Effectiveness (45%): Successfully booking/rescheduling, offering alternatives
- Communication Clarity (15%): Clear confirmation of details, professional closure

SUCCESS DEFINITION: Appointment successfully scheduled or rescheduled
""",
            
            "emergency_call": """
EMERGENCY/PAIN CALL:
- Urgency Recognition (40%): Immediately understanding this is urgent
- Empathy & Comfort (20%): Showing concern for patient's pain
- Immediate Scheduling (30%): Offering same-day or urgent appointment
- Clear Communication (10%): Brief but clear instructions

SUCCESS DEFINITION: Same-day or urgent appointment offered for patient in pain
""",
            
            "service_inquiry": """
SERVICE INQUIRY CALL:
- Greeting & Professionalism (20%): Professional introduction
- Information Quality (30%): Clear, accurate service information
- Consultation Booking (35%): Attempting to schedule consultation
- Relationship Building (15%): Building rapport with potential patient

SUCCESS DEFINITION: Clear information provided + consultation appointment offered
""",
            
            "insurance_verification": """
INSURANCE VERIFICATION CALL:
- Greeting & Professionalism (25%): Professional introduction
- Research Thoroughness (40%): Taking time to verify insurance properly
- Information Accuracy (25%): Providing correct coverage information  
- Helpfulness (10%): Patient and helpful throughout process

SUCCESS DEFINITION: Accurate insurance information provided + follow-up committed if needed
""",
            
            "general_inquiry": """
GENERAL INQUIRY CALL:
- Greeting & Professionalism (30%): Professional, friendly introduction
- Information Helpfulness (50%): Providing requested information clearly
- Relationship Building (20%): Building rapport, professional closure

SUCCESS DEFINITION: Patient's questions answered clearly and professionally
"""
        }
        
        return criteria_map.get(call_type, criteria_map["general_inquiry"])
    
    @classmethod
    def get_scoring_components(cls, call_type: str) -> str:
        """Get scoring components for specific call type"""
        
        components_map = {
            "appointment_booking": """
GREETING_SCORE: [50-100]
GREETING_EXPLANATION: [Specific explanation]

PATIENT_NEEDS_SCORE: [50-100]  
PATIENT_NEEDS_EXPLANATION: [Specific explanation]

SCHEDULING_EFFECTIVENESS_SCORE: [50-100]
SCHEDULING_EFFECTIVENESS_EXPLANATION: [Specific explanation]

COMMUNICATION_CLARITY_SCORE: [50-100]
COMMUNICATION_CLARITY_EXPLANATION: [Specific explanation]
""",
            
            "emergency_call": """
URGENCY_RECOGNITION_SCORE: [50-100]
URGENCY_RECOGNITION_EXPLANATION: [Specific explanation]

EMPATHY_SCORE: [50-100]
EMPATHY_EXPLANATION: [Specific explanation]

IMMEDIATE_SCHEDULING_SCORE: [50-100]
IMMEDIATE_SCHEDULING_EXPLANATION: [Specific explanation]

COMMUNICATION_SCORE: [50-100]
COMMUNICATION_EXPLANATION: [Specific explanation]
""",
            
            "service_inquiry": """
GREETING_SCORE: [50-100]
GREETING_EXPLANATION: [Specific explanation]

INFORMATION_QUALITY_SCORE: [50-100]
INFORMATION_QUALITY_EXPLANATION: [Specific explanation]

CONSULTATION_BOOKING_SCORE: [50-100]
CONSULTATION_BOOKING_EXPLANATION: [Specific explanation]

RELATIONSHIP_BUILDING_SCORE: [50-100]
RELATIONSHIP_BUILDING_EXPLANATION: [Specific explanation]
""",
            
            "insurance_verification": """
GREETING_SCORE: [50-100]
GREETING_EXPLANATION: [Specific explanation]

RESEARCH_THOROUGHNESS_SCORE: [50-100]
RESEARCH_THOROUGHNESS_EXPLANATION: [Specific explanation]

INFORMATION_ACCURACY_SCORE: [50-100]
INFORMATION_ACCURACY_EXPLANATION: [Specific explanation]

HELPFULNESS_SCORE: [50-100]
HELPFULNESS_EXPLANATION: [Specific explanation]
""",
            
            "general_inquiry": """
GREETING_SCORE: [50-100]
GREETING_EXPLANATION: [Specific explanation]

INFORMATION_HELPFULNESS_SCORE: [50-100]
INFORMATION_HELPFULNESS_EXPLANATION: [Specific explanation]

RELATIONSHIP_BUILDING_SCORE: [50-100]
RELATIONSHIP_BUILDING_EXPLANATION: [Specific explanation]
"""
        }
        
        return components_map.get(call_type, components_map["general_inquiry"])