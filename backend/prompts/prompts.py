"""
Centralized Prompts Configuration for Dental Call Analysis System
All LLM prompts are stored here for easy editing and management
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

class LLMAnalyzerPrompts:
    """Prompts for LLM Analyzer service"""
    
    CALL_SUMMARY_PROMPT = """
Analyze this dental office call and provide a brief, professional summary.

TRANSCRIPT:
{transcript}

Provide a concise 2-3 sentence summary covering:
- What was the main purpose of the call
- What was discussed or accomplished
- The outcome

Summary:"""

    NAME_EXTRACTION_PROMPT = """
Extract the dental office representative's name from this call transcript.

TRANSCRIPT:
{transcript}

Look for phrases like:
- "This is [Name]"
- "My name is [Name]"
- "[Name] calling from"
- "I'm [Name]"

If you find the representative's name, respond with just the name (first name only).
If no name is mentioned, respond with "Unknown".

Representative name:"""

    OPPORTUNITY_ASSESSMENT_PROMPT = """
Analyze this dental call to determine if there was a HIGH-VALUE MISSED OPPORTUNITY.

PATIENT: {patient_text}
STAFF: {staff_text}

CALL TYPE CLASSIFICATION:

1. APPOINTMENT BOOKING CALLS (NOT missed opportunities):
- Patient calling to schedule, reschedule, or confirm existing appointments
- Example: "I want to confirm my appointment tomorrow"
- Example: "I need to reschedule my cleaning"
- If appointment successfully managed → NO MISSED OPPORTUNITY

2. GENERAL INQUIRY CALLS (NOT missed opportunities):
- Patient asking for information: hours, location, insurance, pricing
- Patient asking "Do you take [insurance]?" and staff answers appropriately
- Simple questions that get answered professionally
- Example: "Do you take Blue Cross?" → "We only take PPO" (appropriate response)
- Example: "How much to glue my crown?" (existing patient asking price)
- If question was answered → NO MISSED OPPORTUNITY

3. MISSED OPPORTUNITY CALLS (These ARE missed opportunities):
- NEW patient inquiries about services where no appointment offered AND no follow-up promised
- Patient with pain/emergency but no urgent appointment offered AND no callback promised
- Patient interested in major treatment but no consultation scheduled AND no follow-up

CRITICAL RULES:
- If staff promised "I'll call you back" or "I'll check and get back to you" → FALSE (follow-up promised)
- If patient just wanted information and got it → FALSE (inquiry handled)
- If appointment was confirmed/scheduled → FALSE (successful booking)
- If office doesn't accept insurance → FALSE (no opportunity exists)

EXAMPLES OF FALSE (NOT missed opportunities):
- "Confirm appointment tomorrow" → Staff confirms = SUCCESSFUL
- "Do you take Medicaid?" → "No, PPO only" = APPROPRIATE RESPONSE  
- "How much for crown?" → Staff quotes price = INFORMATION PROVIDED
- "I'll check your insurance and call back" = FOLLOW-UP PROMISED

EXAMPLES OF TRUE (Real missed opportunities):  
- Patient: "I need dental work" → Staff: "OK" but no appointment offered, no callback promised
- Patient: "Tooth hurts" → Staff gives advice but no urgent appointment AND no callback
- New patient ready to schedule → Staff doesn't attempt booking AND no follow-up

Answer: TRUE or FALSE"""

class SentimentAnalysisPrompts:
    """Prompts for LLM Sentiment Analysis service"""
    
    SIMPLE_SENTIMENT_PROMPT = """
You are analyzing a dental office phone call for sentiment and emotions. Pay attention to dental-specific contexts like insurance issues, pain, anxiety, and service satisfaction.

PATIENT SAID: "{patient_text}"

STAFF SAID: "{staff_text}"

CALL CONTEXT CLUES:
- Insurance inquiries (coverage questions, denials)
- Pain/discomfort mentions
- Appointment scheduling
- Service satisfaction
- Anxiety about dental procedures

Analyze this dental call and respond with ONLY this JSON (no other text):
{{
    "patient_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on how clear the sentiment indicators are]
    }},
    "staff_sentiment": {{
        "sentiment_label": "positive/negative/neutral", 
        "confidence": [calculate 0.1-1.0 based on professional tone clarity]
    }},
    "overall_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on overall conversation clarity]
    }},
    "emotion_analysis": {{
        "patient_emotions": {{
            "primary_emotion": {{"emotion": "joy/sadness/anger/fear/neutral/disappointment", "confidence": [0.1-1.0 based on emotion clarity]}},
            "intensity": "low/medium/high",
            "dental_specific": {{
                "pain_detected": true/false,
                "anxiety_detected": true/false,
                "satisfaction_detected": true/false,
                "insurance_concern": true/false,
                "disappointment_detected": true/false
            }}
        }},
        "staff_emotions": {{
            "primary_emotion": {{"emotion": "professional/helpful/neutral", "confidence": [0.1-1.0 based on professional tone clarity]}},
            "intensity": "low/medium/high"
        }},
        "emotion_flags": ["PAIN", "ANXIETY", "SATISFACTION", "INSURANCE_ISSUE", "DISAPPOINTMENT"],
        "call_dynamics": {{
            "call_emotional_health": {{"health_level": "good/fair/poor"}},
            "emotional_alignment": {{"is_aligned": true/false}},
            "escalation_pattern": {{"pattern": "none/escalating/de-escalating"}}
        }}
    }},
    "sentiment_summary": "Detailed summary describing the call sentiment, patient emotions, and staff response"
}}

CONFIDENCE SCORING GUIDELINES:
- 0.9-1.0: Very clear indicators (multiple strong keywords, obvious tone)
- 0.7-0.8: Clear indicators (some keywords, clear context)
- 0.5-0.6: Mixed signals (unclear tone, conflicting indicators)
- 0.3-0.4: Weak indicators (minimal context, ambiguous)
- 0.1-0.2: Very unclear (contradictory or no clear indicators)

Guidelines:
- Insurance denials often cause disappointment (not anger)
- Professional staff responses should be "positive" sentiment
- Pain mentions = fear/anxiety emotions
- Successful information exchange = positive overall
- Be specific in sentiment_summary about what happened
- Calculate confidence based on actual clarity of indicators
"""

    SENTIMENT_CHUNK_PROMPT = """
Analyze this segment from a dental office call:

TEXT: "{text}"

This is chunk {chunk_num} of {total_chunks}. {context_info}

Respond with ONLY this JSON:
{{
    "sentiment": {{
        "label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on how clear sentiment indicators are in this chunk],
        "reasoning": "why this sentiment and confidence level"
    }},
    "emotions": {{
        "primary_emotion": "joy/sadness/anger/fear/neutral/disappointment",
        "intensity": "low/medium/high",
        "dental_specific": {{
            "pain_detected": true/false,
            "anxiety_detected": true/false,
            "satisfaction_detected": true/false,
            "insurance_concern": true/false
        }}
    }},
    "key_indicators": ["specific", "words", "or", "phrases"]
}}

Calculate confidence based on:
- Clarity of emotional/sentiment keywords
- Context consistency
- Ambiguity level (lower confidence for unclear text)
"""

    FINAL_ANALYSIS_PROMPT = """
You analyzed {chunk_count} chunks from a dental call. Create the final analysis.

CHUNK SUMMARIES: {chunk_results}

PATIENT SPEECH: {patient_length} characters
STAFF SPEECH: {staff_length} characters

Provide final analysis as ONLY this JSON:
{{
    "patient_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on consistency across chunks]
    }},
    "staff_sentiment": {{
        "sentiment_label": "positive/negative/neutral", 
        "confidence": [calculate 0.1-1.0 based on staff tone consistency]
    }},
    "overall_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on overall call clarity]
    }},
    "emotion_analysis": {{
        "patient_emotions": {{
            "primary_emotion": {{"emotion": "emotion_name", "confidence": [0.1-1.0 based on emotion consistency]}},
            "intensity": "low/medium/high",
            "dental_specific": {{
                "pain_detected": true/false,
                "anxiety_detected": true/false,
                "satisfaction_detected": true/false,
                "insurance_concern": true/false,
                "disappointment_detected": true/false
            }}
        }},
        "staff_emotions": {{
            "primary_emotion": {{"emotion": "emotion_name", "confidence": [0.1-1.0 based on staff behavior consistency]}},
            "intensity": "low/medium/high"
        }},
        "emotion_flags": [],
        "call_dynamics": {{
            "call_emotional_health": {{"health_level": "good/fair/poor"}},
            "emotional_alignment": {{"is_aligned": true/false}},
            "escalation_pattern": {{"pattern": "none/escalating/de-escalating"}}
        }}
    }},
    "sentiment_summary": "Complete summary of the call sentiment and emotions"
}}

Calculate confidence scores based on:
- Consistency across all chunks
- Strength of indicators found
- Conflicting signals (lower confidence)
- Clear patterns (higher confidence)
"""

class CallTaggingPrompts:
    """Prompts for Call Tagging service"""
    
    TAGGING_PROMPT = """
Analyze this dental office call and choose ONE category from the predefined list.

PATIENT: {patient_text}
STAFF: {staff_text}

PREDEFINED CATEGORIES (choose ONLY from these):
1. new_patient - First-time patients or people looking for a new dentist
2. emergency - Urgent dental issues, pain, broken teeth, swelling
3. insurance - Insurance verification, coverage questions, benefit inquiries
4. appointment_booking - Scheduling new appointments
5. appointment_confirm - Confirming existing appointments
6. appointment_cancel - Canceling or rescheduling appointments
7. general_inquiry - General questions about hours, location, services, pricing
8. cleaning - Routine cleanings, checkups, preventive care
9. cosmetic - Whitening, braces, veneers, smile makeovers
10. major_treatment - Implants, crowns, root canals, oral surgery
11. billing - Payment questions, billing issues, account inquiries

Choose the BEST MATCH from these 11 categories. If none fit perfectly, choose "general_inquiry".

Respond with ONLY the category name (e.g., "emergency" or "billing").

Category:"""

class OpportunityDetectorPrompts:
    """Prompts for Opportunity Detector service"""
    
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

class PerformanceScorerPrompts:
    """Prompts for Performance Scorer service"""
    
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