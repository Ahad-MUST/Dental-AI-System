"""
Enhanced Performance scoring service - NOW WITH CHUNKING SUPPORT FOR LONG CALLS
"""
import logging
import re
import json
import asyncio
from typing import Dict, List
from prompts.performance_scorer_prompts import PerformanceScorerPrompts

logger = logging.getLogger(__name__)

class PerformanceScorer:
    """Evaluate call performance with chunking support for long calls"""
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        self.prompts = PerformanceScorerPrompts()
        
        # Chunking configuration
        self.max_single_analysis_length = 4000  # Analyze without chunking
        self.chunk_size = 2500  # Chunk size for long calls
        
        # Call types configuration
        self.call_types = {
            "appointment_booking": {
                "keywords": ["schedule", "appointment", "book", "reschedule", "available", "confirm"],
                "weights": {"greeting": 0.15, "patient_needs": 0.20, "scheduling_effectiveness": 0.50, "communication_clarity": 0.15},
                "success_criteria": "appointment scheduled successfully",
                "baseline_score": 70
            },
            "emergency_call": {
                "keywords": ["pain", "emergency", "urgent", "hurt", "swelling", "broken", "bleeding"],
                "weights": {"urgency_recognition": 0.35, "empathy": 0.25, "immediate_scheduling": 0.30, "communication": 0.10},
                "success_criteria": "same-day appointment offered",
                "baseline_score": 65
            },
            "service_inquiry": {
                "keywords": ["cost", "price", "services", "treatment", "procedure", "whitening", "implant", "crown"],
                "weights": {"greeting": 0.15, "information_quality": 0.30, "consultation_booking": 0.40, "relationship_building": 0.15},
                "success_criteria": "information provided and consultation offered",
                "baseline_score": 75
            },
            "insurance_verification": {
                "keywords": ["insurance", "coverage", "benefits", "network", "accept", "medicaid", "ppo"],
                "weights": {"greeting": 0.20, "research_thoroughness": 0.35, "information_accuracy": 0.30, "helpfulness": 0.15},
                "success_criteria": "accurate insurance information provided",
                "baseline_score": 72
            },
            "general_inquiry": {
                "keywords": ["location", "hours", "contact", "directions", "address"],
                "weights": {"greeting": 0.25, "information_helpfulness": 0.50, "relationship_building": 0.25},
                "success_criteria": "information provided clearly",
                "baseline_score": 78
            }
        }

    async def score_call_performance(self, combined_transcript: Dict, patient_text: str, staff_text: str) -> Dict:
        """
        Score call performance with chunking support for long calls
        """
        try:
            # Identify call type
            call_type = self._identify_call_type(patient_text, staff_text)
            
            # Pre-analyze call quality indicators
            quality_indicators = self._analyze_call_quality_indicators(patient_text, staff_text, call_type)
            
            # Check if chunking is needed for long calls
            combined_text = f"PATIENT: {patient_text}\n\nSTAFF: {staff_text}"
            
            if self._should_use_chunking(combined_text):
                logger.info(f"Long call detected ({len(combined_text)} chars), using chunking for performance scoring")
                return await self._score_with_chunking(patient_text, staff_text, call_type, quality_indicators)
            else:
                logger.info(f"Standard call length ({len(combined_text)} chars), using direct scoring")
                return await self._score_directly(patient_text, staff_text, call_type, quality_indicators)
                
        except Exception as e:
            logger.error(f"Performance scoring failed: {str(e)}")
            return self._create_enhanced_fallback_score(call_type, {})
    
    def _should_use_chunking(self, combined_text: str) -> bool:
        """Determine if chunking is needed based on text length"""
        return len(combined_text) > self.max_single_analysis_length
    
    async def _score_directly(self, patient_text: str, staff_text: str, call_type: str, quality_indicators: Dict) -> Dict:
        """Score short calls directly without chunking"""
        try:
            call_config = self.call_types.get(call_type, self.call_types["general_inquiry"])
            
            # Generate scoring prompt
            evaluation_criteria = self.prompts.EVALUATION_CRITERIA.get(call_type, self.prompts.EVALUATION_CRITERIA["general_inquiry"])
            scoring_components = self.prompts.SCORING_COMPONENTS.get(call_type, self.prompts.SCORING_COMPONENTS["general_inquiry"])
            component_structure = self.prompts.COMPONENT_JSON_STRUCTURE.get(call_type, self.prompts.COMPONENT_JSON_STRUCTURE["general_inquiry"])
            
            prompt = self.prompts.PERFORMANCE_SCORING_PROMPT.format(
                call_type=call_type.replace('_', ' ').title(),
                patient_text=patient_text[:2000],
                staff_text=staff_text[:2000],
                evaluation_criteria=evaluation_criteria,
                scoring_components=scoring_components,
                component_structure=component_structure
            )
            
            llm_response = await self.llm_analyzer.generate_response(prompt, max_tokens=1000)
            
            if llm_response:
                parsed_scores = self._parse_enhanced_performance_response(llm_response, call_type, quality_indicators)
                overall_score = self._calculate_enhanced_overall_score(parsed_scores, call_config, quality_indicators)
                
                return self._build_final_result(overall_score, parsed_scores, call_type, quality_indicators, llm_response)
            else:
                return self._create_enhanced_fallback_score(call_type, quality_indicators)
                
        except Exception as e:
            logger.error(f"Direct scoring error: {str(e)}")
            return self._create_enhanced_fallback_score(call_type, quality_indicators)
    
    async def _score_with_chunking(self, patient_text: str, staff_text: str, call_type: str, quality_indicators: Dict) -> Dict:
        """Score long calls using chunking approach"""
        try:
            # Split into chunks
            patient_chunks = self._split_text_into_chunks(patient_text)
            staff_chunks = self._split_text_into_chunks(staff_text)
            
            logger.info(f"Split into {len(patient_chunks)} patient chunks and {len(staff_chunks)} staff chunks")
            
            # Score each chunk pair
            chunk_scores = []
            max_chunks = max(len(patient_chunks), len(staff_chunks))
            
            for i in range(max_chunks):
                patient_chunk = patient_chunks[i] if i < len(patient_chunks) else ""
                staff_chunk = staff_chunks[i] if i < len(staff_chunks) else ""
                
                if patient_chunk or staff_chunk:  # Only process if at least one chunk has content
                    chunk_result = await self._score_chunk(patient_chunk, staff_chunk, call_type, i + 1, max_chunks)
                    chunk_scores.append(chunk_result)
                    
                    # Brief pause between chunks
                    await asyncio.sleep(0.2)
            
            # Aggregate chunk scores
            final_result = self._aggregate_chunk_scores(chunk_scores, call_type, quality_indicators)
            
            logger.info("Chunked performance scoring completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Chunked scoring error: {str(e)}")
            return self._create_enhanced_fallback_score(call_type, quality_indicators)
    
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
    
    async def _score_chunk(self, patient_chunk: str, staff_chunk: str, call_type: str, chunk_num: int, total_chunks: int) -> Dict:
        """Score a single chunk of the conversation"""
        try:
            # Create a simplified scoring prompt for chunk
            chunk_prompt = f"""
Analyze this segment from a {call_type.replace('_', ' ')} call for performance indicators.

This is chunk {chunk_num} of {total_chunks}.

PATIENT SEGMENT: {patient_chunk}
STAFF SEGMENT: {staff_chunk}

Rate the staff performance in this segment on a scale of 1-10 for:
1. Professionalism
2. Helpfulness  
3. Communication Quality
4. Problem Solving

Respond with ONLY this JSON:
{{
    "professionalism": [1-10],
    "helpfulness": [1-10], 
    "communication": [1-10],
    "problem_solving": [1-10],
    "key_observations": ["observation1", "observation2"]
}}
"""
            
            response = await self.llm_analyzer.generate_response(chunk_prompt, max_tokens=300)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and isinstance(parsed_result, dict):
                    return parsed_result
            
            # Fallback scoring for chunk
            return self._create_fallback_chunk_score(patient_chunk, staff_chunk)
            
        except Exception as e:
            logger.warning(f"Error scoring chunk {chunk_num}: {str(e)}")
            return self._create_fallback_chunk_score(patient_chunk, staff_chunk)
    
    def _create_fallback_chunk_score(self, patient_chunk: str, staff_chunk: str) -> Dict:
        """Create fallback score for a chunk"""
        # Simple keyword-based scoring
        staff_lower = staff_chunk.lower()
        
        professionalism = 6  # Default
        if any(word in staff_lower for word in ["thank you", "please", "welcome"]):
            professionalism += 1
        if any(word in staff_lower for word in ["sorry", "apologize"]):
            professionalism += 1
            
        helpfulness = 6  # Default  
        if any(word in staff_lower for word in ["help", "assist", "can do"]):
            helpfulness += 1
        if any(word in staff_lower for word in ["let me", "I'll check"]):
            helpfulness += 1
            
        communication = 6  # Default
        if len(staff_chunk) > 50:  # Sufficient response length
            communication += 1
            
        problem_solving = 6  # Default
        if any(word in staff_lower for word in ["schedule", "appointment", "available"]):
            problem_solving += 1
        
        return {
            "professionalism": min(10, professionalism),
            "helpfulness": min(10, helpfulness),
            "communication": min(10, communication), 
            "problem_solving": min(10, problem_solving),
            "key_observations": ["Chunk analyzed with fallback method"]
        }
    
    def _aggregate_chunk_scores(self, chunk_scores: List[Dict], call_type: str, quality_indicators: Dict) -> Dict:
        """Aggregate scores from all chunks into final result"""
        if not chunk_scores:
            return self._create_enhanced_fallback_score(call_type, quality_indicators)
        
        # Calculate average scores
        total_scores = {
            "professionalism": 0,
            "helpfulness": 0,
            "communication": 0,
            "problem_solving": 0
        }
        
        valid_chunks = 0
        all_observations = []
        
        for chunk_score in chunk_scores:
            if isinstance(chunk_score, dict):
                for key in total_scores.keys():
                    if key in chunk_score and isinstance(chunk_score[key], (int, float)):
                        total_scores[key] += chunk_score[key]
                        
                if "key_observations" in chunk_score:
                    all_observations.extend(chunk_score["key_observations"])
                valid_chunks += 1
        
        if valid_chunks == 0:
            return self._create_enhanced_fallback_score(call_type, quality_indicators)
        
        # Calculate averages and convert to 0-1 scale
        avg_scores = {key: (total / valid_chunks) / 10 for key, total in total_scores.items()}
        
        # Map to call type specific components
        call_config = self.call_types.get(call_type, self.call_types["general_inquiry"])
        component_scores = {}
        
        for component in call_config["weights"].keys():
            # Map generic scores to specific components
            if "greeting" in component or "professionalism" in component:
                component_scores[component] = avg_scores["professionalism"]
            elif "helpfulness" in component or "assistance" in component:
                component_scores[component] = avg_scores["helpfulness"]
            elif "communication" in component or "clarity" in component:
                component_scores[component] = avg_scores["communication"]
            else:
                component_scores[component] = avg_scores["problem_solving"]
        
        # Calculate overall score
        overall_score = self._calculate_enhanced_overall_score(
            {"component_scores": component_scores}, call_config, quality_indicators
        )
        
        # Generate summary from observations
        unique_observations = list(set(all_observations))[:5]  # Top 5 unique observations
        
        return self._build_final_result(
            overall_score,
            {
                "component_scores": component_scores,
                "strengths": unique_observations[:3] if unique_observations else ["Professional interaction"],
                "weaknesses": [],
                "coaching_focus": [],
                "overall_assessment": f"Aggregated analysis from {valid_chunks} chunks",
                "success_achieved": overall_score >= 0.70,
                "customer_experience_rating": max(1, min(10, int(overall_score * 10))),
                "performance_highlights": f"Analysis based on {valid_chunks} conversation chunks"
            },
            call_type,
            quality_indicators,
            f"Chunked analysis of {valid_chunks} segments"
        )
    
    def _build_final_result(self, overall_score: float, parsed_scores: Dict, call_type: str, quality_indicators: Dict, raw_response: str) -> Dict:
        """Build final result dictionary"""
        return {
            "overall_score": round(overall_score, 3),
            "overall_grade": self._score_to_grade(overall_score),
            "call_type": call_type,
            "component_scores": parsed_scores.get("component_scores", {}),
            "strengths": parsed_scores.get("strengths", []),
            "weaknesses": parsed_scores.get("weaknesses", []),
            "coaching_focus": parsed_scores.get("coaching_focus", []),
            "overall_assessment": parsed_scores.get("overall_assessment", ""),
            "meets_expectations": overall_score >= 0.70,
            "performance_level": self._get_performance_level(overall_score),
            "success_achieved": parsed_scores.get("success_achieved", False),
            "customer_experience_rating": parsed_scores.get("customer_experience_rating", 5),
            "performance_highlights": parsed_scores.get("performance_highlights", ""),
            "quality_indicators": quality_indicators,
            "raw_llm_response": raw_response[:500] + "..." if len(raw_response) > 500 else raw_response
        }
    
    # Include all the existing helper methods from the original file
    def _analyze_call_quality_indicators(self, patient_text: str, staff_text: str, call_type: str) -> Dict:
        """Analyze specific quality indicators to guide scoring"""
        
        patient_lower = patient_text.lower()
        staff_lower = staff_text.lower()
        
        indicators = {
            "professional_greeting": False,
            "empathy_shown": False,
            "problem_solved": False,
            "rude_behavior": False,
            "confusion_detected": False,
            "above_beyond": False,
            "appointment_scheduled": False,
            "follow_up_promised": False,
            "patient_satisfied": False,
            "staff_knowledgeable": False
        }
        
        # Professional greeting indicators
        greeting_phrases = ["thank you for calling", "this is", "how can I help", "good morning", "good afternoon"]
        indicators["professional_greeting"] = any(phrase in staff_lower for phrase in greeting_phrases)
        
        # Empathy indicators
        empathy_phrases = ["understand", "sorry", "I can help", "let me help", "we'll take care", "I apologize"]
        indicators["empathy_shown"] = any(phrase in staff_lower for phrase in empathy_phrases)
        
        # Rude behavior indicators
        rude_phrases = ["can't help you", "you need to", "that's not my", "I don't know", "we don't do that"]
        indicators["rude_behavior"] = any(phrase in staff_lower for phrase in rude_phrases)
        
        # Confusion indicators
        confusion_phrases = ["um", "uh", "I'm not sure", "let me ask", "I don't think"]
        indicators["confusion_detected"] = any(phrase in staff_lower for phrase in confusion_phrases)
        
        # Problem solving
        solution_phrases = ["I can schedule", "let me check", "I'll help you", "we can do", "available"]
        indicators["problem_solved"] = any(phrase in staff_lower for phrase in solution_phrases)
        
        # Above and beyond
        extra_phrases = ["anything else", "questions", "happy to help", "pleasure", "welcome"]
        indicators["above_beyond"] = any(phrase in staff_lower for phrase in extra_phrases)
        
        # Appointment scheduled
        appointment_phrases = ["scheduled", "booked", "see you", "appointment set", "confirmed"]
        indicators["appointment_scheduled"] = any(phrase in staff_lower for phrase in appointment_phrases)
        
        # Follow-up promised
        followup_phrases = ["call you back", "get back to you", "follow up", "check and call"]
        indicators["follow_up_promised"] = any(phrase in staff_lower for phrase in followup_phrases)
        
        # Patient satisfaction (from patient responses)
        satisfaction_phrases = ["thank you", "great", "perfect", "sounds good", "appreciate"]
        indicators["patient_satisfied"] = any(phrase in patient_lower for phrase in satisfaction_phrases)
        
        # Staff knowledge
        knowledge_phrases = ["we accept", "we offer", "our hours", "cost is", "we provide"]
        indicators["staff_knowledgeable"] = any(phrase in staff_lower for phrase in knowledge_phrases)
        
        return indicators
    
    def _parse_enhanced_performance_response(self, response: str, call_type: str, quality_indicators: Dict) -> Dict:
        """Parse enhanced LLM performance response with JSON extraction"""
        
        parsed = {"component_scores": {}}
        
        # Try to extract JSON first
        json_result = self._extract_json_from_response(response)
        if json_result:
            parsed.update(json_result)
        
        # If JSON parsing failed, fall back to regex parsing
        if not parsed.get("component_scores"):
            call_config = self.call_types[call_type]
            
            # Extract component scores with enhanced patterns
            for component in call_config["weights"].keys():
                score = self._extract_component_score(response, component, quality_indicators)
                parsed["component_scores"][component] = score / 100.0  # Convert to 0-1 scale
        
        # Extract additional fields if not in JSON
        if "overall_assessment" not in parsed:
            parsed["overall_assessment"] = self._extract_text_field(response, "overall_assessment") or "Assessment completed"
        
        if "strengths" not in parsed:
            parsed["strengths"] = self._extract_list_field(response, "strengths") or ["Professional interaction"]
        
        if "weaknesses" not in parsed:
            parsed["weaknesses"] = self._extract_list_field(response, "weaknesses") or []
        
        if "coaching_focus" not in parsed:
            parsed["coaching_focus"] = self._extract_list_field(response, "coaching_focus") or []
        
        if "success_achieved" not in parsed:
            parsed["success_achieved"] = self._determine_success_achieved(call_type, quality_indicators)
        
        if "customer_experience_rating" not in parsed:
            parsed["customer_experience_rating"] = self._estimate_customer_rating(quality_indicators)
        
        return parsed
    
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
                
                # Convert component scores to 0-1 scale if they're 0-100
                if "component_scores" in parsed:
                    for key, value in parsed["component_scores"].items():
                        if isinstance(value, (int, float)) and value > 1:
                            parsed["component_scores"][key] = value / 100.0
                
                return parsed
        
        except Exception as e:
            logger.warning(f"JSON extraction failed: {str(e)}")
        
        return {}
    
    def _extract_component_score(self, response: str, component: str, quality_indicators: Dict) -> int:
        """Extract component score with quality-based adjustments"""
        
        component_patterns = [
            f'{component.upper()}_SCORE[:\s]*(\d+)',
            f'{component.upper()}[:\s]*(\d+)',
            f'{component.replace("_", " ").title()}[:\s]*(\d+)'
        ]
        
        base_score = 75  # Default middle score
        
        # Try to extract from LLM response
        for pattern in component_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                base_score = max(40, min(100, int(match.group(1))))
                break
        
        # Apply quality-based adjustments
        adjusted_score = self._apply_quality_adjustments(base_score, component, quality_indicators)
        
        return adjusted_score
    
    def _apply_quality_adjustments(self, base_score: int, component: str, quality_indicators: Dict) -> int:
        """Apply quality-based adjustments to component scores"""
        
        score = base_score
        
        # Positive adjustments
        if quality_indicators.get("professional_greeting") and component == "greeting":
            score += 10
        
        if quality_indicators.get("empathy_shown") and component in ["empathy", "patient_needs"]:
            score += 8
        
        if quality_indicators.get("problem_solved") and component in ["scheduling_effectiveness", "consultation_booking"]:
            score += 12
        
        if quality_indicators.get("above_beyond") and component == "relationship_building":
            score += 10
        
        if quality_indicators.get("appointment_scheduled") and component == "scheduling_effectiveness":
            score += 15
        
        if quality_indicators.get("patient_satisfied"):
            score += 5  # Small boost to all components
        
        # Negative adjustments
        if quality_indicators.get("rude_behavior"):
            score -= 20  # Significant penalty for rudeness
        
        if quality_indicators.get("confusion_detected") and component in ["communication_clarity", "information_quality"]:
            score -= 15
        
        if not quality_indicators.get("staff_knowledgeable") and component == "information_quality":
            score -= 10
        
        # Ensure score stays within bounds
        return max(45, min(100, score))
    
    def _extract_text_field(self, response: str, field_name: str) -> str:
        """Extract text field from response"""
        pattern = f'{field_name.replace("_", " ").title()}[:\s]*(.+?)(?=\\n[A-Z]|$)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _extract_list_field(self, response: str, field_name: str) -> List[str]:
        """Extract list field from response"""
        pattern = f'{field_name.replace("_", " ").title()}[:\s]*(.+?)(?=\\n[A-Z]|$)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            items_text = match.group(1).strip()
            items = []
            for line in items_text.split('\n'):
                line = line.strip()
                if line and not line.upper().startswith(('OVERALL', 'STRENGTHS', 'WEAKNESSES', 'COACHING')):
                    clean_line = re.sub(r'^[-*\d.\s\[\]"]+', '', line).strip().strip('"\'')
                    if len(clean_line) > 5:
                        items.append(clean_line)
            return items[:3]  # Limit to top 3
        return []
    
    def _determine_success_achieved(self, call_type: str, quality_indicators: Dict) -> bool:
        """Determine if call success criteria were met"""
        
        if call_type == "appointment_booking":
            return quality_indicators.get("appointment_scheduled", False)
        elif call_type == "emergency_call":
            return quality_indicators.get("appointment_scheduled", False) or quality_indicators.get("follow_up_promised", False)
        elif call_type == "service_inquiry":
            return quality_indicators.get("appointment_scheduled", False) or quality_indicators.get("staff_knowledgeable", False)
        elif call_type == "insurance_verification":
            return quality_indicators.get("staff_knowledgeable", False) or quality_indicators.get("follow_up_promised", False)
        else:
            return quality_indicators.get("staff_knowledgeable", False)
    
    def _estimate_customer_rating(self, quality_indicators: Dict) -> int:
        """Estimate customer experience rating 1-10"""
        
        rating = 5  # Base rating
        
        # Positive factors
        if quality_indicators.get("professional_greeting"):
            rating += 1
        if quality_indicators.get("empathy_shown"):
            rating += 1
        if quality_indicators.get("problem_solved"):
            rating += 2
        if quality_indicators.get("above_beyond"):
            rating += 1
        if quality_indicators.get("patient_satisfied"):
            rating += 1
        
        # Negative factors
        if quality_indicators.get("rude_behavior"):
            rating -= 3
        if quality_indicators.get("confusion_detected"):
            rating -= 1
        
        return max(1, min(10, rating))
    
    def _calculate_enhanced_overall_score(self, parsed_scores: Dict, call_config: Dict, quality_indicators: Dict) -> float:
        """Calculate enhanced overall score with quality adjustments"""
        
        component_scores = parsed_scores.get("component_scores", {})
        weights = call_config["weights"]
        
        # Calculate weighted score
        total_score = 0
        for component, weight in weights.items():
            score = component_scores.get(component, 0.75)
            total_score += score * weight
        
        # Apply overall quality adjustments
        if quality_indicators.get("rude_behavior"):
            total_score *= 0.8  # 20% penalty for rudeness
        
        if quality_indicators.get("above_beyond") and quality_indicators.get("patient_satisfied"):
            total_score *= 1.1  # 10% bonus for exceptional service
        
        if quality_indicators.get("confusion_detected") and not quality_indicators.get("problem_solved"):
            total_score *= 0.9  # 10% penalty for confusion without resolution
        
        # Ensure reasonable bounds
        return max(0.4, min(1.0, total_score))
    
    def _identify_call_type(self, patient_text: str, staff_text: str) -> str:
        """Enhanced call type identification"""
        
        combined_text = (patient_text + " " + staff_text).lower()
        
        # Score each call type with enhanced logic
        type_scores = {}
        for call_type, config in self.call_types.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in combined_text:
                    # Weight keywords differently
                    if call_type == "emergency_call" and keyword in ["pain", "emergency", "urgent", "hurt"]:
                        score += 3  # Higher weight for emergency indicators
                    elif call_type == "appointment_booking" and keyword in ["schedule", "appointment", "book"]:
                        score += 2  # High weight for booking keywords
                    else:
                        score += 1  # Standard weight for other keywords
            
            if score > 0:
                type_scores[call_type] = score
        
        # Return highest scoring type, with preference for emergency calls
        if type_scores:
            if "emergency_call" in type_scores and type_scores["emergency_call"] >= 2:
                return "emergency_call"  # Prioritize emergency calls
            return max(type_scores, key=type_scores.get)
        else:
            return "general_inquiry"
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade with realistic distribution"""
        if score >= 0.95: return "A+"
        elif score >= 0.90: return "A" 
        elif score >= 0.85: return "A-"
        elif score >= 0.80: return "B+"
        elif score >= 0.75: return "B"
        elif score >= 0.70: return "B-"
        elif score >= 0.65: return "C+"
        elif score >= 0.60: return "C"
        elif score >= 0.55: return "C-"
        elif score >= 0.50: return "D"
        else: return "F"
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level description with clear differentiation"""
        if score >= 0.90: return "Exceptional"
        elif score >= 0.80: return "Above Average"
        elif score >= 0.70: return "Satisfactory"
        elif score >= 0.60: return "Below Average"
        elif score >= 0.50: return "Needs Improvement"
        else: return "Unsatisfactory"
    
    def _create_enhanced_fallback_score(self, call_type: str, quality_indicators: Dict) -> Dict:
        """Create enhanced fallback performance score based on quality indicators"""
        
        # Base score depends on quality indicators
        if quality_indicators.get("rude_behavior"):
            base_score = 0.55
            grade = "C-"
            level = "Needs Improvement"
        elif quality_indicators.get("confusion_detected"):
            base_score = 0.65
            grade = "C+"
            level = "Below Average"
        elif quality_indicators.get("problem_solved") and quality_indicators.get("professional_greeting"):
            base_score = 0.85
            grade = "A-"
            level = "Above Average"
        elif quality_indicators.get("professional_greeting"):
            base_score = 0.75
            grade = "B"
            level = "Satisfactory"
        else:
            base_score = 0.70
            grade = "B-"
            level = "Satisfactory"
        
        # Generate component scores based on quality indicators
        call_config = self.call_types.get(call_type, self.call_types["general_inquiry"])
        component_scores = {}
        
        for component in call_config["weights"].keys():
            score = base_score
            
            # Adjust based on quality indicators
            if quality_indicators.get("professional_greeting") and component == "greeting":
                score += 0.10
            elif quality_indicators.get("rude_behavior"):
                score -= 0.15
            
            component_scores[component] = max(0.45, min(1.0, score))
        
        # Generate appropriate feedback
        strengths = []
        weaknesses = []
        
        if quality_indicators.get("professional_greeting"):
            strengths.append("Professional greeting and introduction")
        if quality_indicators.get("problem_solved"):
            strengths.append("Successfully addressed patient's needs")
        if quality_indicators.get("empathy_shown"):
            strengths.append("Showed empathy and understanding")
        
        if quality_indicators.get("rude_behavior"):
            weaknesses.append("Unprofessional or rude behavior detected")
        if quality_indicators.get("confusion_detected"):
            weaknesses.append("Showed confusion or uncertainty")
        if not quality_indicators.get("staff_knowledgeable"):
            weaknesses.append("Limited knowledge of services or policies")
        
        # Default feedback if no indicators
        if not strengths:
            strengths = ["Call was completed professionally"]
        if not weaknesses and base_score < 0.80:
            weaknesses = ["Opportunity for improvement in customer service"]
        
        return {
            "overall_score": round(base_score, 3),
            "overall_grade": grade,
            "call_type": call_type,
            "component_scores": component_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "coaching_focus": weaknesses[:2] if weaknesses else ["Continue current approach"],
            "overall_assessment": f"Fallback analysis based on quality indicators - {level} performance level",
            "meets_expectations": base_score >= 0.70,
            "performance_level": level,
            "success_achieved": quality_indicators.get("problem_solved", False),
            "customer_experience_rating": self._estimate_customer_rating(quality_indicators),
            "performance_highlights": "Analysis completed using quality indicator fallback",
            "quality_indicators": quality_indicators,
            "source": "enhanced_fallback"
        }