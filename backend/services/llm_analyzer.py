"""
LLM Analysis Service - OpenAI GPT-4 Integration
WITH CHUNKING SUPPORT FOR LONG CALLS AND EMPLOYEE LIST INTEGRATION
"""
import logging
import asyncio
import json
from typing import Dict, List
from config.settings import settings
from prompts.llm_analyzer_prompts import LLMAnalyzerPrompts
from services.employee_list_service import EmployeeListService
from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """OpenAI GPT-4 based call analysis with chunking support for long calls and employee list integration"""

    def __init__(self):
        self.openai_service = None
        self.is_initialized = False

        # Initialize prompts from separate file
        self.prompts = LLMAnalyzerPrompts()

        # Initialize employee list service
        self.employee_service = EmployeeListService()
        
    async def initialize(self) -> None:
        """Initialize OpenAI LLM analyzer using shared service"""
        if self.is_initialized:
            return

        try:
            logger.info("Initializing LLM analyzer with shared OpenAI service...")

            # Get shared OpenAI service
            self.openai_service = await get_openai_service()

            self.is_initialized = True
            logger.info("LLM analyzer ready using OpenAI")

        except Exception as e:
            logger.error(f"LLM analyzer initialization failed: {str(e)}")
            self.openai_service = None
            raise
    
    async def generate_response(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate LLM response using shared OpenAI service"""
        try:
            if not self.is_initialized or not self.openai_service:
                return ""

            return await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=max_tokens,
                system_message="You are a professional dental office call analyst. Provide accurate, concise analysis."
            )

        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            return ""
    
    async def analyze_call_summary(self, full_transcript: str) -> Dict:
        """Generate clean call summary with chunking support for long transcripts"""
        
        if not self.is_initialized:
            return {"call_summary": "LLM analysis unavailable"}
        
        try:
            # Check if we need chunking
            if self._should_chunk_for_analysis(full_transcript):
                return await self._analyze_summary_with_chunking(full_transcript)
            else:
                return await self._analyze_summary_directly(full_transcript)
                
        except Exception as e:
            logger.error(f"Call summary analysis failed: {str(e)}")
            return {"call_summary": "Summary generation failed"}
    
    def _should_chunk_for_analysis(self, text: str) -> bool:
        """Determine if chunking is needed for summary analysis"""
        return len(text) > 4000  # Characters
    
    async def _analyze_summary_directly(self, transcript: str) -> Dict:
        """Analyze short transcripts directly"""
        prompt = self.prompts.CALL_SUMMARY_PROMPT.format(
            transcript=transcript[:4000]  # Limit to prevent token overflow
        )
        
        response = await self.generate_response(prompt, max_tokens=200)
        
        if response:
            summary = response.replace("Summary:", "").strip()
            return {"call_summary": summary if summary else "Call summary generated"}
        else:
            return {"call_summary": "Summary generation failed"}
    
    async def _analyze_summary_with_chunking(self, full_transcript: str) -> str:
        """Analyze long transcripts with chunking"""
        try:
            # Split into chunks
            chunk_size = 3000
            chunks = [full_transcript[i:i+chunk_size] for i in range(0, len(full_transcript), chunk_size)]
            
            # Generate summary for each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks, 1):
                logger.debug(f"Processing summary chunk {i}/{len(chunks)}")
                
                prompt = self.prompts.CALL_SUMMARY_PROMPT.format(transcript=chunk)
                response = await self.generate_response(prompt, max_tokens=150)
                
                if response:
                    summary = response.replace("Summary:", "").strip()
                    chunk_summaries.append(f"Segment {i}: {summary}")
            
            # Combine chunk summaries into final summary
            if chunk_summaries:
                combined_summaries = "\n".join(chunk_summaries)
                
                final_prompt = f"""
SEGMENT SUMMARIES:
{combined_summaries}

Create a cohesive summary that covers:
- The main purpose of the call
- Key topics discussed throughout
- The overall outcome

Final Call Summary:"""
                
                response = await self.generate_response(final_prompt, max_tokens=200)
                
                if response:
                    final_summary = response.replace("Final Call Summary:", "").strip()
                    return final_summary if final_summary else "Call summary generated from multiple segments"
                else:
                    # Fallback: combine chunk summaries directly
                    return "Call covered multiple topics: " + "; ".join([s.split(": ", 1)[1] if ": " in s else s for s in chunk_summaries])
            else:
                return "Summary generation failed"
                
        except Exception as e:
            logger.error(f"Chunked summary generation failed: {str(e)}")
            return "Summary generated from multiple conversation segments"
    
    async def extract_representative_name(self, full_transcript: str) -> str:
        """Extract the dental representative's name from transcript using employee list"""
        
        if not self.is_initialized:
            return "Unknown"
        
        try:
            # Get the current employee list formatted for the prompt
            employee_list = self.employee_service.get_employees_formatted_for_prompt()
            
            # For name extraction, we only need the beginning of the transcript
            # Names are typically mentioned in the first few exchanges
            prompt = self.prompts.NAME_EXTRACTION_PROMPT.format(
                employee_list=employee_list,
                transcript=full_transcript[:2000]
            )
            
            response = await self.generate_response(prompt, max_tokens=50)
            
            if response:
                # Clean up the response
                name = response.replace("Representative name:", "").strip()
                
                # Basic validation
                if name and name.lower() not in ["unknown", "not mentioned", "none", "n/a"]:
                    # Try to match against employee list first
                    visible_employees = self.employee_service.get_visible_employees()
                    name_lower = name.lower().strip()
                    
                    # Try exact match first
                    for employee in visible_employees:
                        if employee.lower() == name_lower:
                            return employee
                    
                    # Try first name match
                    for employee in visible_employees:
                        if employee.split()[0].lower() == name_lower:
                            return employee
                    
                    # Extract just the first name if no match and full name given
                    name_parts = name.split()
                    if name_parts:
                        first_name = name_parts[0].title()
                        # Try matching first name again
                        for employee in visible_employees:
                            if employee.split()[0].lower() == first_name.lower():
                                return employee
                        return first_name
                
            # Fallback: Try simple pattern matching
            return self._extract_name_fallback(full_transcript)
                
        except Exception as e:
            logger.error(f"Name extraction failed: {str(e)}")
            return self._extract_name_fallback(full_transcript)
    
    def _extract_name_fallback(self, transcript: str) -> str:
        """Fallback name extraction using simple patterns and employee list"""
        
        import re
        
        # Get employee list for matching
        visible_employees = self.employee_service.get_visible_employees()
        
        # First, try to match against known visible employees (case-insensitive)
        transcript_lower = transcript.lower()
        for employee in visible_employees:
            first_name = employee.split()[0].lower()
            # Look for the first name in common introduction patterns
            patterns = [
                f"this is {first_name}",
                f"my name is {first_name}",
                f"i'm {first_name}",
                f"{first_name} calling",
                f"hi.*?{first_name}",
                f"hello.*?{first_name}"
            ]
            
            for pattern in patterns:
                if re.search(pattern, transcript_lower):
                    return employee  # Return full name instead of first name
        
        # If no employee match, try general patterns
        patterns = [
            r"This is (\w+)",
            r"My name is (\w+)", 
            r"I'm (\w+)",
            r"(\w+) calling from",
            r"Hi.*?I'm (\w+)",
            r"Hello.*?(\w+) here"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                extracted_name = match.group(1)
                # Basic validation - avoid common words
                if extracted_name.lower() not in ['this', 'the', 'and', 'for', 'with', 'from', 'calling']:
                    # Try to match against employee list
                    for employee in visible_employees:
                        if employee.split()[0].lower() == extracted_name.lower():
                            return employee
                    return extracted_name.title()
        
        return "Unknown"
    
    async def cleanup(self):
        """Cleanup resources"""
        # OpenAI service is shared, no need to close it here
        self.openai_service = None
        self.is_initialized = False
        logger.info("LLM analyzer cleanup completed")