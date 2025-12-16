"""
Call Categorization Service - NEW
Categorizes calls based on client requirements:
- Patient type (new_patient vs existing_patient)
- Appointment booking status
- Script adherence (for new patients)
- Issue resolution (for existing patients)
- Call concern type (for existing patients)
"""
import logging
import json
from typing import Dict
from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class CallCategorizationService:
    """Categorizes calls for Google Ads conversion tracking and detailed analysis"""

    def __init__(self):
        self.openai_service = None
        self.is_initialized = False

    async def initialize(self) -> None:
        """Initialize categorization service"""
        if self.is_initialized:
            return

        try:
            logger.info("Initializing call categorization service...")
            self.openai_service = await get_openai_service()
            self.is_initialized = True
            logger.info("Call categorization service initialized")
        except Exception as e:
            logger.error(f"Call categorization service initialization failed: {str(e)}")
            raise

    async def categorize_call(self, patient_text: str, staff_text: str, call_summary: str) -> Dict:
        """
        Categorize call comprehensively for client requirements

        Returns:
            {
                "patient_type": "new_patient" | "existing_patient",
                "appointment_booked": true | false,
                "script_followed": true | false | null (null for existing patients),
                "call_concern_type": "issue" | "question" | "concern" | "query" | null (null for new patients),
                "issue_resolved": true | false | null (null for new patients),
                "detailed_analysis": "Brutally honest analysis for coaching",
                "conversion_status": "booked" | "not_booked" (for Google Ads),
                "categorization_confidence": 0.0-1.0
            }
        """
        if not self.is_initialized:
            logger.warning("Call categorization service not initialized")
            return self._get_default_categorization()

        try:
            # Combine all text for analysis
            full_context = f"""
CALL SUMMARY:
{call_summary}

PATIENT STATEMENTS:
{patient_text[:1500]}

STAFF STATEMENTS:
{staff_text[:1500]}
"""

            prompt = f"""Analyze this dental office call and provide a comprehensive categorization in JSON format.

{full_context}

Analyze the following:

1. **Patient Type**: Is this a NEW PATIENT (first-time caller, never visited before, new to the practice) or EXISTING PATIENT (returning patient, has been to the practice before)?

2. **Appointment Booking**: Was an appointment successfully BOOKED during this call? (true/false)

3. **For NEW PATIENTS ONLY** - Script Adherence: Did the front desk follow the proper greeting script and procedures for new patients? Consider:
   - Proper greeting with practice name
   - Asked how they heard about the practice
   - Collected necessary information
   - Explained what to expect
   - Provided clear next steps

4. **For EXISTING PATIENTS ONLY** - Call Concern Type: What was the nature of the call?
   - "issue": Problem, complaint, or something wrong
   - "question": Simple inquiry or clarification needed
   - "concern": Worry about treatment, billing, or appointment
   - "query": General information request

5. **For EXISTING PATIENTS ONLY** - Issue Resolution: If there was an issue/concern/question, was it completely resolved during the call? (true/false)

6. **Detailed Analysis**: Provide a brutally honest analysis:
   - What went well in this call
   - What went poorly or could be improved
   - How the staff should have handled it better
   - Specific coaching opportunities

Return ONLY valid JSON in this exact format:
{{
    "patient_type": "new_patient" or "existing_patient",
    "appointment_booked": true or false,
    "script_followed": true or false or null,
    "call_concern_type": "issue" or "question" or "concern" or "query" or null,
    "issue_resolved": true or false or null,
    "detailed_analysis": "Detailed brutally honest analysis here",
    "conversion_status": "booked" or "not_booked",
    "categorization_confidence": 0.85
}}

Important:
- If patient_type is "new_patient", set call_concern_type and issue_resolved to null
- If patient_type is "existing_patient", set script_followed to null
- Be BRUTALLY HONEST in the detailed_analysis - this is for coaching and improvement
"""

            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=800,
                temperature=0.2,
                system_message="You are an expert dental office call analyst. You provide brutally honest feedback for coaching purposes. Always return valid JSON."
            )

            # Parse the JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response)

                # Validate and normalize the result
                return self._validate_categorization(result)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse categorization JSON: {str(e)}")
                logger.error(f"Response was: {response}")
                return self._get_default_categorization()

        except Exception as e:
            logger.error(f"Call categorization failed: {str(e)}")
            return self._get_default_categorization()

    def _validate_categorization(self, result: Dict) -> Dict:
        """Validate and normalize categorization result"""
        # Ensure all required fields exist
        validated = {
            "patient_type": result.get("patient_type", "existing_patient"),
            "appointment_booked": bool(result.get("appointment_booked", False)),
            "script_followed": result.get("script_followed"),
            "call_concern_type": result.get("call_concern_type"),
            "issue_resolved": result.get("issue_resolved"),
            "detailed_analysis": result.get("detailed_analysis", "Analysis not available"),
            "conversion_status": "booked" if result.get("appointment_booked", False) else "not_booked",
            "categorization_confidence": float(result.get("categorization_confidence", 0.7))
        }

        # Apply business rules
        if validated["patient_type"] == "new_patient":
            validated["call_concern_type"] = None
            validated["issue_resolved"] = None
        elif validated["patient_type"] == "existing_patient":
            validated["script_followed"] = None

        return validated

    def _get_default_categorization(self) -> Dict:
        """Return default categorization when analysis fails"""
        return {
            "patient_type": "existing_patient",
            "appointment_booked": False,
            "script_followed": None,
            "call_concern_type": "question",
            "issue_resolved": False,
            "detailed_analysis": "Categorization unavailable - analysis service error",
            "conversion_status": "not_booked",
            "categorization_confidence": 0.0
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.is_initialized = False
        logger.info("Call categorization service cleanup completed")
