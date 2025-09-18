"""
Performance Scorer Prompts - Centralized prompt management for performance scoring
"""

class PerformanceScorerPrompts:
    """Collection of prompts for performance scoring service"""
    
    PERFORMANCE_SCORING_PROMPT = """
You are evaluating a dental office staff member's call performance. Provide REALISTIC and DIFFERENTIATED scores based on actual performance quality.

CALL TYPE: {call_type}
PATIENT: {patient_text}
STAFF: {staff_text}

SCORING PHILOSOPHY:
- Be HONEST and DIFFERENTIATE between good and poor performance
- REWARD excellent customer service with high scores (85-95)
- PENALIZE poor service appropriately (50-70)
- Use the FULL scoring range, not just 70-80

PERFORMANCE EXPECTATIONS BY CALL TYPE:
{evaluation_criteria}

DETAILED SCORING CRITERIA:
{scoring_components}

CRITICAL PERFORMANCE INDICATORS:
✅ EXCELLENT (85-95): Professional, empathetic, solves patient's problem, exceeds expectations
✅ GOOD (75-84): Professional, addresses needs well, meets expectations  
✅ SATISFACTORY (65-74): Basic professionalism, gets job done with minor issues
⚠️ NEEDS IMPROVEMENT (55-64): Unprofessional tone, doesn't fully address needs, confused responses
❌ POOR (45-54): Rude, unhelpful, fails to address patient needs, unprofessional

RESPOND WITH THIS EXACT JSON FORMAT:
{{
    "component_scores": {{
        {component_structure}
    }},
    "overall_assessment": "Your detailed assessment of the call quality and staff performance",
    "strengths": ["Specific strength 1", "Specific strength 2", "Specific strength 3"],
    "weaknesses": ["Specific weakness 1", "Specific weakness 2"],
    "coaching_focus": ["Specific coaching point 1", "Specific coaching point 2"],
    "success_achieved": true/false,
    "performance_highlights": "What made this call stand out (positive or negative)",
    "customer_experience_rating": [1-10 from patient's perspective]
}}

IMPORTANT GUIDELINES:
- If staff was rude or unprofessional → Score components 50-65
- If staff was professional but basic → Score components 70-80  
- If staff was exceptional and went above/beyond → Score components 85-95
- Consider the patient's likely satisfaction with the interaction
- Reward genuine empathy, problem-solving, and professionalism
- Penalize confusion, rudeness, or failure to help
"""

    # Evaluation criteria templates
    EVALUATION_CRITERIA = {
        "appointment_booking": """
APPOINTMENT BOOKING EXPECTATIONS:
- EXCELLENT: Warm greeting, understands needs quickly, offers multiple options, confirms details clearly, professional close
- GOOD: Professional greeting, books appointment efficiently, confirms basic details  
- POOR: Confused about availability, doesn't confirm details, unprofessional tone
KEY SUCCESS METRIC: Appointment successfully scheduled with clear confirmation
""",
        
        "emergency_call": """
EMERGENCY CALL EXPECTATIONS:
- EXCELLENT: Immediate urgency recognition, empathetic response, same-day appointment offered, clear instructions
- GOOD: Recognizes urgency, shows concern, offers prompt appointment
- POOR: Doesn't recognize urgency, no empathy for pain, delays scheduling
KEY SUCCESS METRIC: Same-day or urgent appointment offered for patient in pain
""",
        
        "service_inquiry": """
SERVICE INQUIRY EXPECTATIONS:
- EXCELLENT: Thorough information provided, consultation offered, builds relationship, captures interest
- GOOD: Answers questions clearly, mentions consultation option
- POOR: Vague information, no attempt to schedule consultation, missed sales opportunity
KEY SUCCESS METRIC: Clear information + consultation appointment offered
""",
        
        "insurance_verification": """
INSURANCE VERIFICATION EXPECTATIONS:
- EXCELLENT: Thorough verification process, accurate information, helpful alternatives if not covered
- GOOD: Checks insurance properly, provides clear answer, professional throughout
- POOR: Quick dismissal, inaccurate information, unhelpful attitude
KEY SUCCESS METRIC: Accurate insurance information + helpful guidance
""",
        
        "general_inquiry": """
GENERAL INQUIRY EXPECTATIONS:
- EXCELLENT: Friendly greeting, comprehensive information, offers additional help, professional close
- GOOD: Answers questions clearly, professional manner
- POOR: Rushed responses, incomplete information, unfriendly tone
KEY SUCCESS METRIC: Patient's questions answered clearly and completely
"""
    }

    # Scoring components templates
    SCORING_COMPONENTS = {
        "appointment_booking": """
GREETING (15%): Professional introduction and tone
- 90-100: Warm, professional greeting with name and offer to help
- 70-89: Basic professional greeting
- 50-69: Minimal or rushed greeting
- Below 50: No proper greeting or rude

PATIENT_NEEDS (20%): Understanding and addressing scheduling needs  
- 90-100: Asks clarifying questions, shows flexibility, understands urgency
- 70-89: Understands basic needs, some flexibility shown
- 50-69: Basic understanding, limited flexibility
- Below 50: Doesn't understand or address needs

SCHEDULING_EFFECTIVENESS (50%): Success in booking appointment
- 90-100: Multiple options offered, confirms all details, handles obstacles well
- 70-89: Successfully schedules with basic confirmation
- 50-69: Schedules but misses details or shows confusion
- Below 50: Fails to schedule or very unprofessional process

COMMUNICATION_CLARITY (15%): Clear communication throughout
- 90-100: Crystal clear instructions, professional language, good pace
- 70-89: Generally clear communication
- 50-69: Some unclear moments but adequate
- Below 50: Confusing or unprofessional communication
""",
        
        "emergency_call": """
URGENCY_RECOGNITION (35%): Immediately recognizing this is urgent
- 90-100: Immediate recognition, prioritizes urgency, expedites process
- 70-89: Recognizes urgency, responds appropriately
- 50-69: Eventually recognizes urgency but delayed response
- Below 50: Fails to recognize urgency or treats as routine

EMPATHY (25%): Showing concern and understanding for patient's pain
- 90-100: Genuine empathy, comforting words, acknowledges pain
- 70-89: Shows appropriate concern and understanding
- 50-69: Minimal empathy but professional
- Below 50: No empathy or dismissive of patient's pain

IMMEDIATE_SCHEDULING (30%): Offering urgent/same-day appointment
- 90-100: Same-day appointment offered, works around schedule
- 70-89: Urgent appointment within 24 hours offered
- 50-69: Next available appointment (not urgent) offered
- Below 50: No urgent scheduling attempt made

COMMUNICATION (10%): Clear, calming communication
- 90-100: Calm, clear, reassuring communication style
- 70-89: Professional and clear communication
- 50-69: Adequate communication with some issues
- Below 50: Poor or confusing communication
""",
        
        "service_inquiry": """
GREETING (15%): Professional introduction
- 90-100: Warm, welcoming greeting that builds rapport
- 70-89: Professional standard greeting
- 50-69: Basic greeting with minimal warmth
- Below 50: Poor or no proper greeting

INFORMATION_QUALITY (30%): Providing accurate, helpful service information
- 90-100: Comprehensive, accurate information with details and benefits
- 70-89: Good information covering main questions
- 50-69: Basic information but lacking detail
- Below 50: Vague, inaccurate, or unhelpful information

CONSULTATION_BOOKING (40%): Attempting to schedule consultation
- 90-100: Actively promotes consultation, makes it easy to book, shows value
- 70-89: Offers consultation and provides booking option
- 50-69: Mentions consultation but doesn't actively pursue
- Below 50: No consultation offered or discourages booking

RELATIONSHIP_BUILDING (15%): Building rapport with potential patient
- 90-100: Friendly, engaging, makes patient feel valued and comfortable
- 70-89: Professional and friendly interaction
- 50-69: Professional but minimal relationship building
- Below 50: Cold, transactional, or unfriendly
""",
        
        "insurance_verification": """
GREETING (20%): Professional introduction
- 90-100: Warm, professional greeting with clear identification
- 70-89: Standard professional greeting
- 50-69: Basic greeting, adequate professionalism
- Below 50: Poor greeting or unprofessional start

RESEARCH_THOROUGHNESS (35%): Taking time to properly verify insurance
- 90-100: Thorough verification process, asks for details, double-checks
- 70-89: Proper verification with standard questions
- 50-69: Basic verification but may miss details
- Below 50: Rushed or inadequate verification process

INFORMATION_ACCURACY (30%): Providing correct coverage information
- 90-100: Completely accurate information with clear explanations
- 70-89: Accurate information with good explanation
- 50-69: Generally accurate but may lack clarity
- Below 50: Inaccurate or confusing information provided

HELPFULNESS (15%): Being patient and helpful throughout
- 90-100: Extremely helpful, offers alternatives if not covered, patient with questions
- 70-89: Helpful and patient during the process
- 50-69: Adequately helpful but minimal extra effort
- Below 50: Unhelpful attitude or impatient
""",
        
        "general_inquiry": """
GREETING (25%): Professional, friendly introduction
- 90-100: Warm, welcoming greeting that sets positive tone
- 70-89: Professional and friendly greeting
- 50-69: Adequate greeting but lacks warmth
- Below 50: Poor or unfriendly greeting

INFORMATION_HELPFULNESS (50%): Providing clear, complete information
- 90-100: Comprehensive answers, anticipates additional questions, very helpful
- 70-89: Clear answers to all questions asked
- 50-69: Basic answers but may lack completeness
- Below 50: Incomplete, unclear, or unhelpful information

RELATIONSHIP_BUILDING (25%): Professional interaction and rapport
- 90-100: Engaging, builds rapport, makes positive impression, offers additional help
- 70-89: Professional and pleasant interaction
- 50-69: Professional but minimal rapport building
- Below 50: Cold, rushed, or unfriendly interaction
"""
    }

    # Component JSON structure templates
    COMPONENT_JSON_STRUCTURE = {
        "appointment_booking": '"greeting": [score 0-100], "patient_needs": [score 0-100], "scheduling_effectiveness": [score 0-100], "communication_clarity": [score 0-100]',
        "emergency_call": '"urgency_recognition": [score 0-100], "empathy": [score 0-100], "immediate_scheduling": [score 0-100], "communication": [score 0-100]',
        "service_inquiry": '"greeting": [score 0-100], "information_quality": [score 0-100], "consultation_booking": [score 0-100], "relationship_building": [score 0-100]',
        "insurance_verification": '"greeting": [score 0-100], "research_thoroughness": [score 0-100], "information_accuracy": [score 0-100], "helpfulness": [score 0-100]',
        "general_inquiry": '"greeting": [score 0-100], "information_helpfulness": [score 0-100], "relationship_building": [score 0-100]'
    }