"""
Enhanced opportunity detection - Dental keyword-focused classification for high-value opportunities
Includes intelligent chunking to handle long transcripts without truncation
"""
import logging
import asyncio
import json
from typing import Dict, List
from prompts.opportunity_detector_prompts import OpportunityDetectorPrompts

logger = logging.getLogger(__name__)

class OpportunityDetector:
    """Detect missed business opportunities with enhanced dental keyword focus and intelligent chunking"""
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        
        # Initialize prompts from separate file
        self.prompts = OpportunityDetectorPrompts()
        
        # Chunking parameters for handling long transcripts
        self.max_single_analysis_length = 3000  # Characters - analyze without chunking
        self.max_chunk_length = 2500  # Characters per chunk for chunking
        
        # High-value dental treatment keywords that should trigger opportunity detection
        self.high_value_keywords = {
            'emergency': ['emergency', 'urgent', 'pain', 'toothache', 'tooth hurt', 'swelling', 'broken tooth', 'knocked out', 'bleeding'],
            'major_treatments': ['implant', 'crown', 'bridge', 'veneer', 'root canal', 'oral surgery', 'extraction', 'wisdom teeth'],
            'cosmetic': ['whitening', 'braces', 'invisalign', 'straighten', 'cosmetic', 'smile makeover'],
            'new_patient': ['new patient', 'first time', 'never been', 'looking for dentist', 'need dentist'],
            'preventive': ['cleaning', 'checkup', 'exam', 'x-ray', 'deep cleaning', 'periodontal']
        }
        
    async def detect_opportunities(self, patient_text: str, staff_text: str, 
                                 call_summary: Dict, booking_outcome: Dict) -> Dict:
        """
        Enhanced opportunity detection with intelligent chunking for long transcripts
        """
        try:
            logger.info("Analyzing missed opportunities with dental keyword focus and intelligent chunking...")
            
            # First check for high-value dental keywords
            has_dental_keywords = self._has_high_value_dental_keywords(patient_text)
            
            if not has_dental_keywords:
                logger.info("No high-value dental keywords found - not a missed opportunity")
                return {"high_value_missed": False}
            
            # Check for definitive exclusions
            if self._is_definitely_not_missed_opportunity(patient_text, staff_text, call_summary):
                logger.info("Pre-screening: Definitely not a missed opportunity despite keywords")
                return {"high_value_missed": False}
            
            if not self.llm_analyzer.is_initialized:
                # Enhanced rule-based detection for dental keywords
                high_value_missed = self._dental_keyword_opportunity_check(patient_text, staff_text)
                logger.info(f"Dental keyword-based assessment: {high_value_missed}")
                return {"high_value_missed": high_value_missed}
            
            # Combine texts to check if chunking is needed
            combined_text = f"PATIENT: {patient_text}\n\nSTAFF: {staff_text}"
            
            # Decision: Use chunking for long transcripts
            if self._should_use_chunking(combined_text):
                logger.info(f"Text is long ({len(combined_text)} chars), using chunking approach")
                return await self._analyze_with_chunking(patient_text, staff_text, combined_text)
            else:
                logger.info(f"Text is short ({len(combined_text)} chars), using direct analysis")
                return await self._analyze_directly(patient_text, staff_text)
            
        except Exception as e:
            logger.error(f"Opportunity detection failed: {str(e)}")
            # Conservative fallback
            return {"high_value_missed": False}
    
    def _should_use_chunking(self, combined_text: str) -> bool:
        """Determine if text needs chunking based on length"""
        return len(combined_text) > self.max_single_analysis_length
    
    async def _analyze_directly(self, patient_text: str, staff_text: str) -> Dict:
        """Analyze short texts directly without chunking"""
        try:
            prompt = self.prompts.SIMPLE_OPPORTUNITY_PROMPT.format(
                patient_text=patient_text,
                staff_text=staff_text
            )
            
            logger.debug("Sending prompt to LLM for direct opportunity analysis")
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=100)
            
            if response:
                logger.debug(f"Received LLM response: {response}")
                # Parse LLM response
                high_value_missed = "TRUE" in response.upper() and "FALSE" not in response.upper()
                logger.info(f"Direct LLM opportunity assessment: {'MISSED OPPORTUNITY' if high_value_missed else 'NO OPPORTUNITY MISSED'}")
                return {"high_value_missed": high_value_missed}
            else:
                logger.warning("Empty response from LLM")
            
            # If LLM failed, use enhanced rule-based
            logger.info("LLM failed, using enhanced rule-based analysis")
            high_value_missed = self._dental_keyword_opportunity_check(patient_text, staff_text)
            return {"high_value_missed": high_value_missed}
            
        except Exception as e:
            logger.error(f"Direct analysis error: {str(e)}")
            high_value_missed = self._dental_keyword_opportunity_check(patient_text, staff_text)
            return {"high_value_missed": high_value_missed}
    
    async def _analyze_with_chunking(self, patient_text: str, staff_text: str, combined_text: str) -> Dict:
        """Analyze long texts using chunking approach"""
        try:
            # Split into chunks
            chunks = self._split_text_into_chunks(combined_text)
            logger.info(f"Split text into {len(chunks)} chunks for opportunity analysis")
            
            # Analyze each chunk
            chunk_results = []
            for i, chunk in enumerate(chunks, 1):
                context_info = f"Previous {i-1} chunks analyzed" if i > 1 else "First chunk"
                chunk_result = await self._analyze_opportunity_chunk(chunk, i, len(chunks), context_info)
                chunk_results.append(chunk_result)
                
                # Brief pause between chunks
                await asyncio.sleep(0.2)
            
            # Generate final aggregated analysis
            final_result = await self._generate_final_opportunity_analysis(
                chunk_results, patient_text, staff_text
            )
            
            logger.info("LLM chunked opportunity analysis completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Chunked opportunity analysis error: {str(e)}")
            high_value_missed = self._dental_keyword_opportunity_check(patient_text, staff_text)
            return {"high_value_missed": high_value_missed}
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks for LLM processing"""
        if not text or len(text) <= self.max_chunk_length:
            return [text] if text else []
        
        # Split by sentences first to maintain context
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed chunk limit
            if len(current_chunk) + len(sentence) + 2 > self.max_chunk_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk += sentence + ". "
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _analyze_opportunity_chunk(self, chunk_text: str, chunk_num: int, total_chunks: int, context_info: str = "") -> Dict:
        """Analyze opportunity indicators for a single chunk"""
        try:
            prompt = self.prompts.OPPORTUNITY_CHUNK_PROMPT.format(
                text=chunk_text,
                chunk_num=chunk_num,
                total_chunks=total_chunks,
                context_info=context_info
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=400)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and isinstance(parsed_result, dict):
                    return parsed_result
            
            # Fallback chunk analysis
            return self._create_fallback_chunk_analysis(chunk_text)
            
        except Exception as e:
            logger.warning(f"Error analyzing opportunity chunk {chunk_num}: {str(e)}")
            return self._create_fallback_chunk_analysis(chunk_text)
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        if not response:
            return {}
        
        try:
            # Clean and parse directly
            cleaned = response.strip()
            
            # Remove common prefixes/suffixes
            for prefix in ['```json', '```', 'json', 'JSON']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            
            for suffix in ['```', '`']:
                if cleaned.endswith(suffix):
                    cleaned = cleaned[:-len(suffix)].strip()
            
            # Find JSON boundaries
            start_idx = cleaned.find('{')
            if start_idx == -1:
                return {}
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(cleaned)):
                if cleaned[i] == '{':
                    brace_count += 1
                elif cleaned[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count == 0:
                json_str = cleaned[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    logger.debug("Successfully extracted JSON from opportunity analysis response")
                    return parsed
        
        except Exception as e:
            logger.warning(f"JSON extraction error in opportunity analysis: {str(e)}")
        
        return {}
    
    def _create_fallback_chunk_analysis(self, text: str) -> Dict:
        """Create fallback analysis for chunk with dental keyword focus"""
        text_lower = text.lower()
        
        # Check for dental keywords
        dental_keywords_found = []
        for category, keywords in self.high_value_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    dental_keywords_found.append(keyword)
        
        # Check for scheduling indicators
        scheduling_phrases = ["schedule", "appointment", "book", "come in", "see you", "available", "when can"]
        scheduling_attempted = any(phrase in text_lower for phrase in scheduling_phrases)
        
        # Check for follow-up promises
        followup_phrases = ["call you back", "get back to you", "follow up", "check and call"]
        follow_up_promised = any(phrase in text_lower for phrase in followup_phrases)
        
        # Determine patient interest level
        if any(keyword in text_lower for keyword in self.high_value_keywords['emergency']):
            interest_level = "high"
        elif any(keyword in text_lower for keyword in self.high_value_keywords['major_treatments']):
            interest_level = "high"
        elif any(keyword in text_lower for keyword in self.high_value_keywords['new_patient']):
            interest_level = "medium"
        elif dental_keywords_found:
            interest_level = "medium"
        else:
            interest_level = "low"
        
        # Chunk assessment
        if dental_keywords_found and not scheduling_attempted and not follow_up_promised:
            chunk_assessment = "opportunity"
        elif dental_keywords_found and (scheduling_attempted or follow_up_promised):
            chunk_assessment = "no_opportunity"
        else:
            chunk_assessment = "unclear"
        
        return {
            "has_dental_keywords": len(dental_keywords_found) > 0,
            "dental_keywords_found": dental_keywords_found,
            "scheduling_attempted": scheduling_attempted,
            "follow_up_promised": follow_up_promised,
            "patient_interest_level": interest_level,
            "chunk_assessment": chunk_assessment,
            "key_indicators": dental_keywords_found[:3]  # Top 3 indicators
        }
    
    async def _generate_final_opportunity_analysis(self, chunk_results: List[Dict], patient_text: str, staff_text: str) -> Dict:
        """Generate final opportunity assessment from all chunks"""
        try:
            # Create simplified summary for LLM
            simplified_results = []
            for i, result in enumerate(chunk_results, 1):
                simplified = {
                    "chunk": i,
                    "has_keywords": result.get("has_dental_keywords", False),
                    "keywords": result.get("dental_keywords_found", []),
                    "scheduling": result.get("scheduling_attempted", False),
                    "followup": result.get("follow_up_promised", False),
                    "assessment": result.get("chunk_assessment", "unclear")
                }
                simplified_results.append(simplified)
            
            prompt = self.prompts.FINAL_OPPORTUNITY_PROMPT.format(
                chunk_count=len(chunk_results),
                chunk_results=json.dumps(simplified_results, indent=2),
                patient_length=len(patient_text),
                staff_length=len(staff_text)
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=300)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and "high_value_missed" in parsed_result:
                    high_value_missed = parsed_result["high_value_missed"]
                    logger.info(f"Final LLM opportunity assessment: {'MISSED OPPORTUNITY' if high_value_missed else 'NO OPPORTUNITY MISSED'}")
                    return {"high_value_missed": high_value_missed}
            
            # Fallback to manual aggregation
            return self._manual_opportunity_aggregation(chunk_results)
            
        except Exception as e:
            logger.warning(f"Error generating final opportunity analysis: {str(e)}")
            return self._manual_opportunity_aggregation(chunk_results)
    
    def _manual_opportunity_aggregation(self, chunk_results: List[Dict]) -> Dict:
        """Manually aggregate chunk results for opportunity detection"""
        if not chunk_results:
            return {"high_value_missed": False}
        
        # Check if any chunk indicates a clear opportunity
        has_opportunity = False
        has_dental_keywords = False
        has_scheduling_attempt = False
        has_followup_promise = False
        
        for chunk in chunk_results:
            if chunk.get("has_dental_keywords", False):
                has_dental_keywords = True
            
            if chunk.get("scheduling_attempted", False):
                has_scheduling_attempt = True
            
            if chunk.get("follow_up_promised", False):
                has_followup_promise = True
            
            if chunk.get("chunk_assessment") == "opportunity":
                has_opportunity = True
        
        # Final decision logic
        if has_dental_keywords and not has_scheduling_attempt and not has_followup_promise:
            final_decision = True
            logger.info("Manual aggregation: Dental keywords present, no scheduling/followup - MISSED OPPORTUNITY")
        elif has_opportunity and not (has_scheduling_attempt or has_followup_promise):
            final_decision = True
            logger.info("Manual aggregation: Opportunity detected in chunks, no resolution - MISSED OPPORTUNITY")
        else:
            final_decision = False
            logger.info("Manual aggregation: No clear missed opportunity detected")
        
        return {"high_value_missed": final_decision}
    
    def _has_high_value_dental_keywords(self, patient_text: str) -> bool:
        """Check if patient text contains high-value dental keywords"""
        
        patient_lower = patient_text.lower()
        
        # Check each category of high-value keywords
        for category, keywords in self.high_value_keywords.items():
            for keyword in keywords:
                if keyword in patient_lower:
                    logger.info(f"High-value dental keyword found: '{keyword}' in category '{category}'")
                    return True
        
        return False
    
    def _is_definitely_not_missed_opportunity(self, patient_text: str, staff_text: str, call_summary: Dict) -> bool:
        """Pre-screening to identify calls that are definitely not missed opportunities"""
        
        patient_lower = patient_text.lower()
        staff_lower = staff_text.lower()
        summary = call_summary.get("call_summary", "").lower()
        
        # Definitive indicators of non-missed opportunities
        definitive_non_opportunities = [
            # Successful appointment management
            ("confirm" in patient_lower and "appointment" in patient_lower),
            ("tomorrow" in patient_lower and ("appointment" in staff_lower or "see you" in staff_lower)),
            ("scheduled" in staff_lower or "booked" in staff_lower),
            ("appointment" in staff_lower and ("confirmed" in staff_lower or "set" in staff_lower)),
            
            # Staff committed to specific follow-up
            ("call you back" in staff_lower and ("today" in staff_lower or "tomorrow" in staff_lower)),
            ("check your insurance and call you" in staff_lower),
            ("get back to you" in staff_lower and ("today" in staff_lower or "shortly" in staff_lower)),
            ("follow up with you" in staff_lower),
            
            # Insurance/service limitations appropriately handled
            ("we don't accept" in staff_lower and "medicaid" in patient_lower),
            ("we only take ppo" in staff_lower and "medicaid" in patient_lower),
            ("not in network" in staff_lower),
            
            # Confirmation calls in summary
            ("confirm" in summary and "appointment" in summary),
            ("confirmation call" in summary)
        ]
        
        return any(definitive_non_opportunities)
    
    def _dental_keyword_opportunity_check(self, patient_text: str, staff_text: str) -> bool:
        """Enhanced rule-based opportunity detection focused on dental keywords"""
        
        patient_lower = patient_text.lower()
        staff_lower = staff_text.lower()
        
        # Step 1: Must have high-value dental keywords (already checked)
        
        # Step 2: Check for definitive exclusions
        exclusions = [
            # Successful appointment management
            ("appointment" in staff_lower and ("scheduled" in staff_lower or "booked" in staff_lower or "confirmed" in staff_lower)),
            ("see you" in staff_lower and ("tomorrow" in staff_lower or "today" in staff_lower)),
            
            # Specific follow-up promises
            ("call you back today" in staff_lower),
            ("call you back tomorrow" in staff_lower),
            ("check your insurance and call" in staff_lower),
            ("get back to you today" in staff_lower),
            ("follow up" in staff_lower and ("today" in staff_lower or "tomorrow" in staff_lower)),
            
            # Legitimate service limitations
            ("we don't accept" in staff_lower and "insurance" in patient_lower),
            ("we only take" in staff_lower and "ppo" in staff_lower),
            ("not covered" in staff_lower and "insurance" in patient_lower)
        ]
        
        if any(exclusions):
            return False
        
        # Step 3: Check for high-value dental treatment interest
        emergency_keywords = any(keyword in patient_lower for keyword in self.high_value_keywords['emergency'])
        major_treatment_keywords = any(keyword in patient_lower for keyword in self.high_value_keywords['major_treatments'])
        cosmetic_keywords = any(keyword in patient_lower for keyword in self.high_value_keywords['cosmetic'])
        new_patient_keywords = any(keyword in patient_lower for keyword in self.high_value_keywords['new_patient'])
        
        # Step 4: Check if staff made appropriate scheduling effort
        staff_scheduling_effort = any(phrase in staff_lower for phrase in [
            "schedule", "book", "appointment", "come in", "see you", "available",
            "when can", "what time", "today", "tomorrow", "this week"
        ])
        
        # Emergency calls should have urgent scheduling
        if emergency_keywords:
            urgent_response = any(phrase in staff_lower for phrase in [
                "today", "right away", "emergency", "urgent", "same day", "asap"
            ])
            if not urgent_response and not staff_scheduling_effort:
                logger.info("Emergency keywords found but no urgent scheduling offered")
                return True
        
        # Major treatments should have consultation offered
        if major_treatment_keywords or cosmetic_keywords:
            consultation_offered = any(phrase in staff_lower for phrase in [
                "consultation", "exam", "evaluation", "assessment", "come in", "schedule"
            ])
            if not consultation_offered and not staff_scheduling_effort:
                logger.info("Major treatment interest but no consultation offered")
                return True
        
        # New patients should be actively scheduled
        if new_patient_keywords:
            if not staff_scheduling_effort:
                logger.info("New patient inquiry but no appointment scheduling attempted")
                return True
        
        # Default: if high-value keywords present but no scheduling effort, it's a missed opportunity
        has_high_value_keywords = any([emergency_keywords, major_treatment_keywords, cosmetic_keywords, new_patient_keywords])
        
        if has_high_value_keywords and not staff_scheduling_effort:
            logger.info("High-value dental keywords present but no scheduling effort made")
            return True
        
        return False
    
    def _rule_based_opportunity_check(self, patient_text: str, staff_text: str) -> bool:
        """Legacy rule-based fallback - now uses dental keyword focus"""
        return self._dental_keyword_opportunity_check(patient_text, staff_text)