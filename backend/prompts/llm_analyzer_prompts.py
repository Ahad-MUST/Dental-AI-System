"""
LLM Analyzer Prompts - Centralized prompt management for LLM-based analysis
Updated to include employee list for better representative name extraction
"""

class LLMAnalyzerPrompts:
    """Collection of prompts for LLM analyzer service"""
    
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

KNOWN DENTAL OFFICE EMPLOYEES:
{employee_list}

TRANSCRIPT:
{transcript}

Look for phrases like:
- "This is [Name]"
- "My name is [Name]"
- "[Name] calling from"
- "I'm [Name]"

INSTRUCTIONS:
1. First, try to identify which of the known employees is speaking in this call
2. If you find a match with the known employees list, respond with that employee's FIRST NAME only
3. If no known employee is identified but another name is mentioned, respond with that name (first name only)
4. If no name is mentioned at all, respond with "Unknown"

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
- "How much for crown?" → Staff provides price = INFORMATION PROVIDED

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