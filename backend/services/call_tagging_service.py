"""
Call Tagging Service - WITH CHUNKING SUPPORT FOR LONG CALLS
"""
import logging
import re
import asyncio
import json
from typing import Dict, List
from prompts.call_tagging_prompts import CallTaggingPrompts

logger = logging.getLogger(__name__)

class CallTaggingService:
    """Service to automatically tag calls with chunking support for long calls"""
    
    def __init__(self, llm_analyzer=None):
        self.llm_analyzer = llm_analyzer
        
        # Initialize prompts from separate file
        self.prompts = CallTaggingPrompts()
        
        # Chunking configuration
        self.max_single_analysis_length = 3000  # Analyze without chunking
        self.chunk_size = 2500  # Chunk size for long calls
        
        # Use centralized predefined categories
        self.predefined_categories = {
            'new_patient': {
                'keywords': ['new patient', 'first time', 'never been', 'looking for dentist', 'need dentist', 'new to area'],
                'patterns': [r'first.{0,10}time', r'new.{0,10}patient', r'never.{0,10}been'],
                'priority': 100
            },
            'emergency': {
                'keywords': ['emergency', 'urgent', 'pain', 'hurt', 'swelling', 'bleeding', 'broken tooth', 'tooth fell out', 'severe pain', 'asap', 'right away', 'today'],
                'patterns': [r'tooth.{0,10}hurt', r'in.{0,10}pain', r'really.{0,10}hurt', r'severe.{0,10}pain', r'emergency', r'urgent', r'need.{0,10}see.{0,10}today'],
                'priority': 110
            },
            'insurance': {
                'keywords': ['insurance', 'coverage', 'benefits', 'network', 'accept', 'medicaid', 'ppo', 'delta dental', 'aetna', 'cigna', 'verification'],
                'patterns': [r'take.{0,10}insurance', r'accept.{0,10}medicaid', r'in.{0,10}network'],
                'priority': 70
            },
            'appointment_booking': {
                'keywords': ['schedule', 'appointment', 'book', 'reschedule', 'available', 'when can', 'time slot', 'open'],
                'patterns': [r'schedule.{0,10}appointment', r'book.{0,10}cleaning', r'available.{0,10}time'],
                'priority': 80
            },
            'appointment_confirm': {
                'keywords': ['confirm', 'confirmation', 'tomorrow', 'verify appointment', 'check appointment'],
                'patterns': [r'confirm.{0,10}appointment', r'appointment.{0,10}tomorrow', r'verify.{0,10}appointment'],
                'priority': 60
            },
            'appointment_cancel': {
                'keywords': ['cancel', 'reschedule', 'change appointment', 'move appointment', 'postpone'],
                'patterns': [r'cancel.{0,10}appointment', r'reschedule.{0,10}appointment', r'change.{0,10}time'],
                'priority': 65
            },
            'general_inquiry': {
                'keywords': ['hours', 'location', 'address', 'directions', 'contact', 'phone number', 'cost', 'price', 'how much'],
                'patterns': [r'how.{0,10}much', r'what.{0,10}cost', r'office.{0,10}hours'],
                'priority': 50
            },
            'cleaning': {
                'keywords': ['cleaning', 'checkup', 'exam', 'routine visit', 'six month', 'hygienist'],
                'patterns': [r'routine.{0,10}cleaning', r'six.{0,10}month', r'dental.{0,10}cleaning'],
                'priority': 75
            },
            'cosmetic': {
                'keywords': ['whitening', 'braces', 'invisalign', 'straighten', 'cosmetic', 'smile makeover', 'veneer'],
                'patterns': [r'whiten.{0,10}teeth', r'cosmetic.{0,10}dentistry', r'smile.{0,10}makeover'],
                'priority': 85
            },
            'major_treatment': {
                'keywords': ['implant', 'crown', 'bridge', 'root canal', 'oral surgery', 'extraction', 'wisdom teeth'],
                'patterns': [r'dental.{0,10}implant', r'root.{0,10}canal', r'wisdom.{0,10}teeth'],
                'priority': 95
            },
            'billing': {
                'keywords': ['billing', 'payment', 'balance', 'bill', 'charge', 'statement', 'account'],
                'patterns': [r'billing.{0,10}question', r'payment.{0,10}plan', r'account.{0,10}balance'],
                'priority': 55
            }
        }
        
    async def analyze_and_tag_call(self, patient_text: str, staff_text: str, call_summary: str = "") -> Dict:
        """
        Analyze call content and assign appropriate tag with chunking support for long calls
        
        Returns:
            Dict with primary_tag from predefined categories
        """
        try:
            # Combine all text for analysis
            combined_text = f"{patient_text} {staff_text} {call_summary}"
            
            # Check if chunking is needed for long calls
            if self._should_use_chunking(combined_text):
                logger.info(f"Long call detected ({len(combined_text)} chars), using chunking for call tagging")
                return await self._tag_with_chunking(patient_text, staff_text, call_summary)
            else:
                logger.info(f"Standard call length ({len(combined_text)} chars), using direct tagging")
                return await self._tag_directly(patient_text, staff_text, call_summary)
            
        except Exception as e:
            logger.error(f"Call tagging failed: {str(e)}")
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.5,
                'reasoning': 'Tagging analysis failed, defaulted to general inquiry'
            }
    
    def _should_use_chunking(self, combined_text: str) -> bool:
        """Determine if chunking is needed based on text length"""
        return len(combined_text) > self.max_single_analysis_length
    
    async def _tag_directly(self, patient_text: str, staff_text: str, call_summary: str) -> Dict:
        """Tag short calls directly without chunking"""
        try:
            combined_text = f"{patient_text} {staff_text} {call_summary}".lower()
            
            # First, try rule-based tagging with predefined categories
            rule_based_result = self._rule_based_tagging(combined_text)
            
            # If rule-based gives high confidence, use it
            if rule_based_result['confidence_score'] >= 0.7:
                logger.info(f"Rule-based tag: {rule_based_result['primary_tag']}")
                return rule_based_result
            
            # Otherwise, use LLM for better accuracy (still limited to predefined categories)
            if self.llm_analyzer and self.llm_analyzer.is_initialized:
                llm_result = await self._llm_based_tagging_direct(patient_text, staff_text)
                if llm_result['primary_tag'] in self.predefined_categories:
                    logger.info(f"LLM-based tag: {llm_result['primary_tag']}")
                    return llm_result
            
            # Fallback to rule-based result
            logger.info(f"Fallback to rule-based tag: {rule_based_result['primary_tag']}")
            return rule_based_result
            
        except Exception as e:
            logger.error(f"Direct tagging failed: {str(e)}")
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.5,
                'reasoning': 'Direct tagging failed'
            }
    
    async def _tag_with_chunking(self, patient_text: str, staff_text: str, call_summary: str) -> Dict:
        """Tag long calls using chunking approach"""
        try:
            # Split into chunks
            patient_chunks = self._split_text_into_chunks(patient_text)
            staff_chunks = self._split_text_into_chunks(staff_text)
            
            logger.info(f"Split into {len(patient_chunks)} patient chunks and {len(staff_chunks)} staff chunks")
            
            # Analyze each chunk pair for tagging indicators
            chunk_results = []
            max_chunks = max(len(patient_chunks), len(staff_chunks))
            
            for i in range(max_chunks):
                patient_chunk = patient_chunks[i] if i < len(patient_chunks) else ""
                staff_chunk = staff_chunks[i] if i < len(staff_chunks) else ""
                
                if patient_chunk or staff_chunk:  # Only process if at least one chunk has content
                    chunk_result = await self._analyze_chunk_for_tags(patient_chunk, staff_chunk, i + 1, max_chunks)
                    chunk_results.append(chunk_result)
                    
                    # Brief pause between chunks
                    await asyncio.sleep(0.2)
            
            # Aggregate chunk results to determine final tag
            final_result = self._aggregate_chunk_tags(chunk_results, call_summary)
            
            logger.info("Chunked call tagging completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Chunked tagging error: {str(e)}")
            # Fallback to rule-based on combined text
            combined_text = f"{patient_text} {staff_text} {call_summary}".lower()
            return self._rule_based_tagging(combined_text)
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks for processing"""
        if not text or len(text) <= self.chunk_size:
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
            if len(current_chunk) + len(sentence) + 2 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk += sentence + ". "
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _analyze_chunk_for_tags(self, patient_chunk: str, staff_chunk: str, chunk_num: int, total_chunks: int) -> Dict:
        """Analyze a single chunk for tagging indicators"""
        try:
            # Create a simplified tagging prompt for chunk
            chunk_prompt = f"""
Analyze this segment from a dental office call to identify call type indicators.

This is segment {chunk_num} of {total_chunks}.

PATIENT SEGMENT: {patient_chunk}
STAFF SEGMENT: {staff_chunk}

Look for keywords that indicate the call type:
- NEW PATIENT: "new patient", "first time", "looking for dentist"
- EMERGENCY: "pain", "urgent", "emergency", "tooth hurt", "swelling"
- INSURANCE: "insurance", "coverage", "medicaid", "ppo", "benefits"
- APPOINTMENT: "schedule", "appointment", "book", "reschedule", "confirm"
- SERVICES: "cost", "price", "whitening", "implant", "crown", "cleaning"
- BILLING: "payment", "bill", "balance", "charge"

Respond with ONLY this JSON:
{{
    "detected_categories": ["category1", "category2"],
    "confidence_level": "high/medium/low",
    "key_keywords": ["keyword1", "keyword2"],
    "segment_focus": "primary topic discussed in this segment"
}}
"""
            
            if self.llm_analyzer and self.llm_analyzer.is_initialized:
                response = await self.llm_analyzer.generate_response(chunk_prompt, max_tokens=200)
                
                if response:
                    parsed_result = self._extract_json_from_response(response)
                    if parsed_result and isinstance(parsed_result, dict):
                        return parsed_result
            
            # Fallback: rule-based analysis for chunk
            return self._analyze_chunk_with_rules(patient_chunk, staff_chunk)
            
        except Exception as e:
            logger.warning(f"Error analyzing chunk {chunk_num} for tags: {str(e)}")
            return self._analyze_chunk_with_rules(patient_chunk, staff_chunk)
    
    def _analyze_chunk_with_rules(self, patient_chunk: str, staff_chunk: str) -> Dict:
        """Analyze chunk using rule-based approach"""
        combined_chunk = f"{patient_chunk} {staff_chunk}".lower()
        
        detected_categories = []
        key_keywords = []
        confidence_level = "low"
        
        # Check each category
        for category, config in self.predefined_categories.items():
            category_score = 0
            matched_keywords = []
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword in combined_chunk:
                    category_score += 1
                    matched_keywords.append(keyword)
                    key_keywords.append(keyword)
            
            # Check regex patterns
            for pattern in config.get('patterns', []):
                if re.search(pattern, combined_chunk, re.IGNORECASE):
                    category_score += 2
            
            # If category has indicators, add it
            if category_score > 0:
                detected_categories.append(category)
                if category_score >= 2:
                    confidence_level = "high"
                elif category_score >= 1 and confidence_level == "low":
                    confidence_level = "medium"
        
        # Determine primary focus
        if "pain" in combined_chunk or "emergency" in combined_chunk:
            segment_focus = "emergency care"
        elif "insurance" in combined_chunk or "coverage" in combined_chunk:
            segment_focus = "insurance verification"
        elif "appointment" in combined_chunk or "schedule" in combined_chunk:
            segment_focus = "appointment management"
        elif "cost" in combined_chunk or "price" in combined_chunk:
            segment_focus = "service inquiry"
        else:
            segment_focus = "general discussion"
        
        return {
            "detected_categories": detected_categories,
            "confidence_level": confidence_level,
            "key_keywords": list(set(key_keywords)),  # Remove duplicates
            "segment_focus": segment_focus
        }
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            # Find JSON boundaries
            start_idx = response.find('{')
            if start_idx == -1:
                return {}
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count == 0:
                json_str = response[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    return parsed
        
        except Exception as e:
            logger.warning(f"JSON extraction failed in tagging: {str(e)}")
        
        return {}
    
    def _aggregate_chunk_tags(self, chunk_results: List[Dict], call_summary: str) -> Dict:
        """Aggregate tagging results from all chunks"""
        if not chunk_results:
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.5,
                'reasoning': 'No chunk results available'
            }
        
        # Count category occurrences across all chunks
        category_counts = {}
        all_keywords = []
        high_confidence_chunks = 0
        
        for chunk_result in chunk_results:
            detected_categories = chunk_result.get("detected_categories", [])
            confidence_level = chunk_result.get("confidence_level", "low")
            keywords = chunk_result.get("key_keywords", [])
            
            # Count categories
            for category in detected_categories:
                if category in self.predefined_categories:
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            # Collect keywords
            all_keywords.extend(keywords)
            
            # Count high confidence chunks
            if confidence_level == "high":
                high_confidence_chunks += 1
        
        # Determine primary tag based on frequency and priority
        if not category_counts:
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.5,
                'reasoning': 'No specific categories detected across chunks'
            }
        
        # Weight by priority and frequency
        weighted_scores = {}
        for category, count in category_counts.items():
            priority = self.predefined_categories[category]['priority']
            weighted_scores[category] = count * (priority / 100)
        
        # Get highest weighted category
        primary_category = max(weighted_scores, key=weighted_scores.get)
        
        # Calculate confidence based on consistency and chunk confidence
        max_count = category_counts[primary_category]
        total_chunks = len(chunk_results)
        frequency_confidence = max_count / total_chunks
        
        # Boost confidence if multiple high-confidence chunks detected this category
        if high_confidence_chunks > 0:
            frequency_confidence *= 1.2
        
        final_confidence = min(0.95, max(0.4, frequency_confidence))
        
        # Generate reasoning
        unique_keywords = list(set(all_keywords))
        reasoning = f"Detected across {max_count}/{total_chunks} chunks"
        if unique_keywords:
            reasoning += f", keywords: {', '.join(unique_keywords[:5])}"
        
        return {
            'primary_tag': primary_category,
            'confidence_score': round(final_confidence, 3),
            'reasoning': reasoning,
            'keyword_matches': unique_keywords[:10],  # Top 10 keywords
            'chunk_distribution': category_counts
        }
    
    def _rule_based_tagging(self, combined_text: str) -> Dict:
        """Rule-based tagging using predefined categories only"""
        
        category_scores = {}
        
        # Score each predefined category
        for category, config in self.predefined_categories.items():
            score = 0
            matched_keywords = []
            matched_patterns = []
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword in combined_text:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Check regex patterns
            for pattern in config.get('patterns', []):
                if re.search(pattern, combined_text, re.IGNORECASE):
                    score += 2  # Patterns are more specific
                    matched_patterns.append(pattern)
            
            # Apply category priority weighting
            if score > 0:
                weighted_score = score * (config['priority'] / 100)
                category_scores[category] = {
                    'score': weighted_score,
                    'raw_score': score,
                    'keywords': matched_keywords,
                    'patterns': matched_patterns
                }
        
        # Determine primary category from predefined list
        if not category_scores:
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.5,
                'reasoning': 'No specific keywords found, defaulted to general inquiry'
            }
        
        # Get highest scoring predefined category
        primary_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
        primary_score = category_scores[primary_category]
        
        # Calculate confidence based on score strength
        confidence = min(0.95, max(0.4, primary_score['score'] / 5))  # Normalize to 0.4-0.95
        
        reasoning = f"Matched {len(primary_score['keywords'])} keywords"
        if primary_score['patterns']:
            reasoning += f" and {len(primary_score['patterns'])} patterns"
        reasoning += f" for {primary_category}"
        
        return {
            'primary_tag': primary_category,
            'confidence_score': confidence,
            'reasoning': reasoning,
            'keyword_matches': primary_score['keywords']
        }
    
    async def _llm_based_tagging_direct(self, patient_text: str, staff_text: str) -> Dict:
        """LLM-based tagging for direct analysis (non-chunked)"""
        
        try:
            prompt = self.prompts.TAGGING_PROMPT.format(
                patient_text=patient_text[:1500],
                staff_text=staff_text[:1500]
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=50)
            
            if response:
                # Clean and validate response
                tag = response.strip().lower()
                tag = re.sub(r'[^a-z_]', '', tag)  # Remove any non-letter characters except underscore
                
                # ENSURE tag is from predefined categories only
                if tag in self.predefined_categories:
                    return {
                        'primary_tag': tag,
                        'confidence_score': 0.85,
                        'reasoning': f'LLM-based classification as {tag}'
                    }
                else:
                    logger.warning(f"LLM returned tag '{response}' not in predefined categories, defaulting to general_inquiry")
                    return {
                        'primary_tag': 'general_inquiry',
                        'confidence_score': 0.6,
                        'reasoning': f'LLM returned non-predefined category, defaulted to general inquiry'
                    }
            else:
                return {
                    'primary_tag': 'general_inquiry',
                    'confidence_score': 0.5,
                    'reasoning': 'LLM analysis failed, defaulted to general inquiry'
                }
                
        except Exception as e:
            logger.error(f"LLM tagging failed: {str(e)}")
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.4,
                'reasoning': 'LLM tagging error, defaulted to general inquiry'
            }
    
    def get_tag_display_name(self, tag: str) -> str:
        """Convert tag to user-friendly display name"""
        display_names = {
            'new_patient': 'New Patient',
            'emergency': 'Emergency Call',
            'insurance': 'Insurance Inquiry',
            'appointment_booking': 'Appointment Booking',
            'appointment_confirm': 'Appointment Confirmation',
            'appointment_cancel': 'Cancel/Reschedule',
            'general_inquiry': 'General Inquiry',
            'cleaning': 'Cleaning/Checkup',
            'cosmetic': 'Cosmetic Treatment',
            'major_treatment': 'Major Treatment',
            'billing': 'Billing Question'
        }

        return display_names.get(tag, tag.replace('_', ' ').title())
    
    def get_available_tags(self) -> List[str]:
        """Get list of predefined tag categories"""
        return list(self.predefined_categories.keys())
    
    def get_tag_statistics(self, calls_data: List[Dict]) -> Dict:
        """Generate statistics about tag distribution from predefined categories"""
        
        tag_counts = {}
        total_calls = len(calls_data)
        
        for call in calls_data:
            tag = call.get('Call_Tag', 'general_inquiry')
            # Ensure tag is from predefined categories
            if tag not in self.predefined_categories:
                tag = 'general_inquiry'
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Convert to percentages and add display names
        tag_stats = {}
        for tag, count in tag_counts.items():
            tag_stats[tag] = {
                'count': count,
                'percentage': (count / total_calls * 100) if total_calls > 0 else 0,
                'display_name': self.get_tag_display_name(tag)
            }
        
        return {
            'total_calls': total_calls,
            'tag_distribution': tag_stats,
            'most_common_tag': max(tag_counts.keys(), key=lambda k: tag_counts[k]) if tag_counts else 'general_inquiry'
        }