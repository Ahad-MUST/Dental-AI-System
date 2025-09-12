"""
LLM Analysis Service - Fixed with Accurate Call Classification
"""
import logging
import aiohttp
from typing import Dict
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM-based call analysis using Ollama"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.session = None
        self.is_initialized = False
        
        # Updated prompts for accurate classification
        self.call_summary_prompt = """
Analyze this dental office call and provide a brief, professional summary.

TRANSCRIPT:
{transcript}

Provide a concise 2-3 sentence summary covering:
- What was the main purpose of the call
- What was discussed or accomplished
- The outcome

Summary:"""

        self.name_extraction_prompt = """
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

        # CRITICAL: Fixed opportunity assessment prompt
        self.opportunity_assessment_prompt = """
Analyze this dental call to determine if there was a HIGH-VALUE MISSED OPPORTUNITY.

PATIENT: {patient_text}
STAFF: {staff_text}

CALL TYPE CLASSIFICATION:

1. APPOINTMENT BOOKING CALLS (NOT missed opportunities):
- Patient calling to schedule, reschedule, or confirm existing appointments
- Example: "I want to confirm my appointment tomorrow"
- Example: "I need to reschedule my cleaning"
- If appointment successfully managed â†’ NO MISSED OPPORTUNITY

2. GENERAL INQUIRY CALLS (NOT missed opportunities):
- Patient asking for information: hours, location, insurance, pricing
- Patient asking "Do you take [insurance]?" and staff answers appropriately
- Simple questions that get answered professionally
- Example: "Do you take Blue Cross?" â†’ "We only take PPO" (appropriate response)
- Example: "How much to glue my crown?" (existing patient asking price)
- If question was answered â†’ NO MISSED OPPORTUNITY

3. MISSED OPPORTUNITY CALLS (These ARE missed opportunities):
- NEW patient inquiries about services where no appointment offered AND no follow-up promised
- Patient with pain/emergency but no urgent appointment offered AND no callback promised
- Patient interested in major treatment but no consultation scheduled AND no follow-up

CRITICAL RULES:
- If staff promised "I'll call you back" or "I'll check and get back to you" â†’ FALSE (follow-up promised)
- If patient just wanted information and got it â†’ FALSE (inquiry handled)
- If appointment was confirmed/scheduled â†’ FALSE (successful booking)
- If office doesn't accept insurance â†’ FALSE (no opportunity exists)

EXAMPLES OF FALSE (NOT missed opportunities):
- "Confirm appointment tomorrow" â†’ Staff confirms = SUCCESSFUL
- "Do you take Medicaid?" â†’ "No, PPO only" = APPROPRIATE RESPONSE  
- "How much for crown?" â†’ Staff quotes price = INFORMATION PROVIDED
- "I'll check your insurance and call back" = FOLLOW-UP PROMISED

EXAMPLES OF TRUE (Real missed opportunities):  
- Patient: "I need dental work" â†’ Staff: "OK" but no appointment offered, no callback promised
- Patient: "Tooth hurts" â†’ Staff gives advice but no urgent appointment AND no callback
- New patient ready to schedule â†’ Staff doesn't attempt booking AND no follow-up

Answer: TRUE or FALSE"""
        
    async def initialize(self) -> None:
        """Initialize LLM analyzer"""
        if self.is_initialized:
            return
            
        try:
            logger.info("Initializing LLM analyzer...")
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Check Ollama connection
            await self._check_ollama_connection()
            
            # Verify model availability
            await self._verify_model()
            
            self.is_initialized = True
            logger.info(f"LLM analyzer ready with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"LLM analyzer initialization failed: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
            raise
    
    async def _check_ollama_connection(self):
        """Check if Ollama server is running"""
        try:
            async with self.session.get(f"{self.ollama_url}/api/tags", timeout=5) as response:
                if response.status != 200:
                    raise Exception(f"Ollama server not responding (status: {response.status})")
        except Exception as e:
            raise Exception(f"Cannot connect to Ollama at {self.ollama_url}: {str(e)}")
    
    async def _verify_model(self):
        """Verify model is available"""
        try:
            async with self.session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model['name'] for model in data.get('models', [])]
                    
                    if self.model_name not in available_models:
                        logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                        raise Exception(f"Model {self.model_name} not available")
        except Exception as e:
            raise Exception(f"Error verifying model: {str(e)}")
    
    async def generate_response(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate LLM response"""
        try:
            if not self.is_initialized or not self.session:
                return ""
            
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for more consistent results
                    "top_p": 0.9,
                    "num_predict": max_tokens
                }
            }
            
            async with self.session.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "").strip()
                else:
                    logger.error(f"Ollama API error: {response.status}")
                    return ""
                    
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            return ""
    
    async def analyze_call_summary(self, full_transcript: str) -> Dict:
        """Generate clean call summary"""
        
        if not self.is_initialized:
            return {"call_summary": "LLM analysis unavailable"}
        
        try:
            prompt = self.call_summary_prompt.format(
                transcript=full_transcript[:3000]  # Limit context
            )
            
            response = await self.generate_response(prompt, max_tokens=200)
            
            if response:
                # Clean up the response
                summary = response.replace("Summary:", "").strip()
                if not summary:
                    summary = "Call processed successfully"
                    
                return {"call_summary": summary}
            else:
                return {"call_summary": "Summary generation failed"}
                
        except Exception as e:
            logger.error(f"Call summary generation failed: {str(e)}")
            return {"call_summary": "Summary generation failed"}
    
    async def extract_representative_name(self, full_transcript: str) -> str:
        """Extract the dental representative's name from transcript"""
        
        if not self.is_initialized:
            return "Unknown"
        
        try:
            prompt = self.name_extraction_prompt.format(
                transcript=full_transcript[:2000]  # Focus on beginning where introductions happen
            )
            
            response = await self.generate_response(prompt, max_tokens=50)
            
            if response:
                # Clean up the response
                name = response.replace("Representative name:", "").strip()
                
                # Basic validation
                if name and name.lower() not in ["unknown", "not mentioned", "none", "n/a"]:
                    # Extract just the first name if full name given
                    name_parts = name.split()
                    if name_parts:
                        return name_parts[0].title()  # Capitalize first letter
                
            # Fallback: Try simple pattern matching
            return self._extract_name_fallback(full_transcript)
                
        except Exception as e:
            logger.error(f"Name extraction failed: {str(e)}")
            return self._extract_name_fallback(full_transcript)
    
    def _extract_name_fallback(self, transcript: str) -> str:
        """Fallback name extraction using simple patterns"""
        
        import re
        
        # Common introduction patterns
        patterns = [
            r"This is (\w+)",
            r"My name is (\w+)", 
            r"I'm (\w+)",
            r"(\w+) calling from",
            r"Hi.*?I'm (\w+)",
            r"Hello.*?this is (\w+)"
        ]
        
        transcript_start = transcript[:500].lower()  # Focus on beginning
        
        for pattern in patterns:
            match = re.search(pattern, transcript_start, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if name.lower() not in ["this", "calling", "dental", "office", "hello", "hi"]:
                    return name.title()
        
        return "Unknown"
    
    async def assess_missed_opportunity(self, patient_text: str, staff_text: str) -> bool:
        """Assess if high-value opportunity was missed using accurate classification"""
        
        if not self.is_initialized:
            return False
        
        try:
            prompt = self.opportunity_assessment_prompt.format(
                patient_text=patient_text[:1500],
                staff_text=staff_text[:1500]
            )
            
            response = await self.generate_response(prompt, max_tokens=100)
            
            # Parse response - be precise
            is_missed = "TRUE" in response.upper() and "FALSE" not in response.upper()
            
            logger.info(f"Opportunity assessment result: {'TRUE (missed)' if is_missed else 'FALSE (no opportunity missed)'}")
            
            return is_missed
            
        except Exception as e:
            logger.error(f"Opportunity assessment failed: {str(e)}")
            return False  # Conservative default
    
    # Legacy methods for compatibility
    async def analyze_booking_outcome(self, patient_text: str, staff_text: str) -> Dict:
        """Legacy method - simplified"""
        return {"outcome": "unknown"}
    
    async def detect_missed_opportunities(self, patient_text: str, staff_text: str) -> Dict:
        """Legacy method - simplified"""
        high_value_missed = await self.assess_missed_opportunity(patient_text, staff_text)
        return {"high_value_missed": high_value_missed}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False