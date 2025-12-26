"""
Speaker Role Assignment Prompts - Centralized prompt management for LLM-based speaker role detection
"""

class SpeakerRolePrompts:
    """Collection of prompts for speaker role assignment service"""
    
    SPEAKER_ROLE_ANALYSIS_PROMPT = """
Analyze this dental office call transcript and identify which speakers are DENTAL OFFICE STAFF and which are PATIENTS.

TRANSCRIPT WITH SPEAKERS:
{transcript_with_speakers}

IMPORTANT CONTEXT:
- This is a dental office phone call
- There may be multiple speakers due to diarization splitting one person's speech
- One or more speakers represent dental office staff (receptionist, assistant, dentist)
- One or more speakers represent patients (calling for appointments, inquiries, etc.)
- There may be automated voice saying "This call may be recorded" - identify separately
- The speaker labels (SPEAKER_00, etc.) may be wrong - analyze CONTENT only

ANALYSIS STRATEGY:
1. First identify any AUTOMATED voice segments
2. Then look for clear STAFF indicators: professional greetings, office knowledge, scheduling
3. Finally identify PATIENT indicators: personal needs, questions, providing personal info

STAFF INDICATORS:
- "Thank you for calling [Office Name]"
- "This is [Name]" (professional introduction)
- "How can I help you?"
- Knowledge of schedules, appointments, procedures
- "Let me check", "I can schedule", "We have available"
- Professional closing: "Have a good day"

PATIENT INDICATORS:
- Giving personal name when asked
- "I have an appointment", "I need to change"
- Asking about availability, costs, insurance
- Personal requests or problems
- Responding to staff questions about preferences

AUTOMATED INDICATORS:
- "This call may be recorded"
- "For quality and training purposes"

CRITICAL REQUIREMENTS:
1. You MUST include at least ONE speaker in staff_speakers
2. You MUST include at least ONE speaker in patient_speakers
3. Staff and patient speakers MUST be different
4. ALL speakers mentioned must exist in the transcript above (use exact speaker IDs like SPEAKER_00, SPEAKER_01, etc.)
5. Multiple speakers might be the SAME person (diarization errors) - group by ROLE not just speaker ID

Respond with ONLY valid JSON, no other text:
{{
    "staff_speakers": ["SPEAKER_00"],
    "patient_speakers": ["SPEAKER_01"],
    "automated_speakers": [],
    "confidence": 0.8,
    "reasoning": "SPEAKER_00 uses professional greetings and scheduling language (staff). SPEAKER_01 asks questions about appointment availability (patient)."
}}

Example format - your response must be parseable JSON with these exact fields.
"""

    CHUNKED_ROLE_ANALYSIS_PROMPT = """
Analyze this segment from a dental office call to identify speaker roles.

This is chunk {chunk_num} of {total_chunks}.

TRANSCRIPT SEGMENT:
{transcript_chunk}

CONTEXT FROM PREVIOUS CHUNKS: {context_info}

Look for these indicators in this chunk:

STAFF INDICATORS:
- Professional greetings ("Thank you for calling", "How can I help")
- Knowledge of office policies/procedures
- Scheduling language ("available", "book you")  
- Medical/dental terminology used professionally
- Asking for patient information

PATIENT INDICATORS:
- Stating personal needs/problems
- Asking about costs, insurance, availability
- Providing personal information when asked
- Expressing pain, concerns, preferences
- Responding to staff questions

AUTOMATED VOICE INDICATORS:
- "This call may be recorded"
- Legal disclaimers or hold music announcements

Respond with ONLY this JSON:
{{
    "chunk_analysis": {{
        "dominant_staff_speaker": "SPEAKER_XX or null",
        "dominant_patient_speaker": "SPEAKER_XX or null", 
        "automated_speaker": "SPEAKER_XX or null",
        "confidence_level": "high/medium/low",
        "key_indicators": ["specific phrases or behaviors that indicate roles"]
    }},
    "speaker_behaviors": {{
        "SPEAKER_00": {{"likely_role": "staff/patient/automated/unknown", "evidence": ["evidence1", "evidence2"]}},
        "SPEAKER_01": {{"likely_role": "staff/patient/automated/unknown", "evidence": ["evidence1", "evidence2"]}},
        "SPEAKER_02": {{"likely_role": "staff/patient/automated/unknown", "evidence": ["evidence1", "evidence2"]}}
    }}
}}
"""

    FINAL_ROLE_ASSIGNMENT_PROMPT = """
Based on analysis of {chunk_count} chunks from a dental office call, determine the final speaker role assignments.

CHUNK ANALYSIS RESULTS:
{chunk_results}

ORIGINAL SPEAKER SEGMENTS:
- Total speakers detected: {speaker_count}
- Speakers found: {speakers_list}

CONSOLIDATION RULES:
1. Look for consistent patterns across chunks
2. Staff speaker should have professional language throughout
3. Patient speaker should have personal needs/questions
4. Automated speaker only appears briefly at start
5. If 3+ speakers, one might be automated voice or multiple staff

Provide final role assignments as ONLY this JSON:
{{
    "final_assignments": {{
        "staff_speaker": "SPEAKER_XX",
        "patient_speaker": "SPEAKER_XX",
        "automated_speaker": "SPEAKER_XX or null"
    }},
    "confidence_scores": {{
        "staff_assignment": [0.1-1.0],
        "patient_assignment": [0.1-1.0],
        "overall_confidence": [0.1-1.0]
    }},
    "assignment_reasoning": "Clear explanation of final role assignments",
    "speaker_analysis": {{
        "SPEAKER_00": {{"assigned_role": "staff/patient/automated", "evidence_strength": "strong/moderate/weak"}},
        "SPEAKER_01": {{"assigned_role": "staff/patient/automated", "evidence_strength": "strong/moderate/weak"}},
        "SPEAKER_02": {{"assigned_role": "staff/patient/automated", "evidence_strength": "strong/moderate/weak"}}
    }},
    "warnings": ["any concerns about assignment accuracy"]
}}

Calculate confidence based on:
- Consistency of role indicators across chunks
- Strength of evidence for each assignment
- Clarity of professional vs personal language patterns
- Logical consistency of conversation flow
"""