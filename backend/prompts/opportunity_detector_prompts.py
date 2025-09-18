"""
Opportunity Detector Prompts - Centralized prompt management for missed opportunity detection
"""

class OpportunityDetectorPrompts:
    """Collection of prompts for opportunity detection service"""
    
    SIMPLE_OPPORTUNITY_PROMPT = """
Analyze this dental office call to determine if there was a HIGH-VALUE MISSED OPPORTUNITY based on DENTAL KEYWORDS.

PATIENT SAID: {patient_text}
STAFF RESPONSE: {staff_text}

DENTAL KEYWORD ANALYSIS:

HIGH-VALUE DENTAL KEYWORDS that indicate opportunity:
- EMERGENCY: pain, toothache, urgent, emergency, swelling, broken tooth
- MAJOR TREATMENTS: implant, crown, bridge, root canal, oral surgery, extraction
- COSMETIC: whitening, braces, invisalign, cosmetic dentistry, smile makeover  
- NEW PATIENT: new patient, looking for dentist, need dentist, first time
- PREVENTIVE: cleaning, checkup, exam, deep cleaning

OPPORTUNITY DETECTION RULES:

TRUE (MISSED opportunity) if:
- Patient mentions HIGH-VALUE dental keywords (emergency, implant, crown, etc.)
- AND no appointment was scheduled
- AND no specific follow-up was arranged

FALSE (NO missed opportunity) if:
- Appointment was successfully scheduled/confirmed
- Staff promised specific follow-up ("I'll call you back", "check insurance and call you")
- Patient only asked for basic information that was provided (hours, location)
- Office legitimately cannot serve patient (insurance not accepted)

FOCUS ON DENTAL TREATMENT OPPORTUNITIES:
- Emergency calls without same-day scheduling = TRUE
- Crown/implant inquiries without consultation booking = TRUE  
- New patient calls without appointment offered = TRUE
- Cosmetic treatment interest without consultation = TRUE
- Pain/toothache calls without urgent appointment = TRUE

EXAMPLES:
- "My tooth hurts" + no urgent appointment offered = TRUE
- "Need a crown" + no consultation scheduled = TRUE  
- "New patient, need cleaning" + no appointment booked = TRUE
- "Confirm my appointment tomorrow" + confirmed = FALSE
- "Do you take Medicaid?" + "No, PPO only" = FALSE

Answer with ONLY: TRUE or FALSE

Assessment:"""

    OPPORTUNITY_CHUNK_PROMPT = """
Analyze this segment from a dental office call for missed opportunities:

TEXT: "{text}"

This is chunk {chunk_num} of {total_chunks}. {context_info}

Look for:
- HIGH-VALUE DENTAL KEYWORDS: pain, emergency, implant, crown, bridge, root canal, new patient, cleaning
- SCHEDULING ATTEMPTS: appointment offered, booking attempted, follow-up promised
- PATIENT INTEREST: treatment requests, service inquiries, pain mentions

Respond with ONLY this JSON:
{{
    "has_dental_keywords": true/false,
    "dental_keywords_found": ["keyword1", "keyword2"],
    "scheduling_attempted": true/false,
    "follow_up_promised": true/false,
    "patient_interest_level": "high/medium/low/none",
    "chunk_assessment": "opportunity/no_opportunity/unclear",
    "key_indicators": ["specific", "phrases", "found"]
}}
"""

    FINAL_OPPORTUNITY_PROMPT = """
You analyzed {chunk_count} chunks from a dental call. Determine final missed opportunity assessment.

CHUNK SUMMARIES: {chunk_results}

PATIENT SPEECH: {patient_length} characters
STAFF SPEECH: {staff_length} characters

Based on all chunks, determine if there was a HIGH-VALUE MISSED OPPORTUNITY:

RULES:
- If ANY chunk shows high patient interest in dental treatment AND no scheduling/follow-up = TRUE
- If appointment was scheduled or specific follow-up promised = FALSE
- Emergency/pain mentions without urgent care = TRUE
- Major treatment interest without consultation = TRUE

Provide final analysis as ONLY this JSON:
{{
    "high_value_missed": true/false,
    "reasoning": "Clear explanation of decision",
    "dental_keywords_detected": ["keyword1", "keyword2"],
    "opportunity_type": "emergency/major_treatment/new_patient/cosmetic/none",
    "confidence": [0.1-1.0 based on clarity of indicators]
}}
"""