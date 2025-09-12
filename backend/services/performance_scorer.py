"""
Enhanced Performance scoring service for dental call quality evaluation
Provides more differentiated and accurate scoring
"""
import logging
import re
import json
import asyncio
from typing import Dict, List

logger = logging.getLogger(__name__)

class PerformanceScorer:
    """Evaluate call performance using enhanced LLM analysis with better differentiation"""
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        
        # Enhanced call type definitions with more specific criteria
        self.call_types = {
            "appointment_booking": {
                "keywords": ["schedule", "appointment", "book", "reschedule", "available", "confirm"],
                "weights": {"greeting": 0.15, "patient_needs": 0.20, "scheduling_effectiveness": 0.50, "communication_clarity": 0.15},
                "success_criteria": "appointment scheduled successfully",
                "baseline_score": 70  # If basic requirements met
            },
            "emergency_call": {
                "keywords": ["pain", "emergency", "urgent", "hurt", "swelling", "broken", "bleeding"],
                "weights": {"urgency_recognition": 0.35, "empathy": 0.25, "immediate_scheduling": 0.30, "communication": 0.10},
                "success_criteria": "same-day appointment offered",
                "baseline_score": 65  # Emergency calls are more critical
            },
            "service_inquiry": {
                "keywords": ["cost", "price", "services", "treatment", "procedure", "whitening", "implant", "crown"],
                "weights": {"greeting": 0.15, "information_quality": 0.30, "consultation_booking": 0.40, "relationship_building": 0.15},
                "success_criteria": "information provided and consultation offered",
                "baseline_score": 75  # Sales opportunity baseline
            },
            "insurance_verification": {
                "keywords": ["insurance", "coverage", "benefits", "network", "accept", "medicaid", "ppo"],
                "weights": {"greeting": 0.20, "research_thoroughness": 0.35, "information_accuracy": 0.30, "helpfulness": 0.15},
                "success_criteria": "accurate insurance information provided",
                "baseline_score": 72  # Information accuracy critical
            },
            "general_inquiry": {
                "keywords": ["location", "hours", "contact", "directions", "address"],
                "weights": {"greeting": 0.25, "information_helpfulness": 0.50, "relationship_building": 0.25},
                "success_criteria": "information provided clearly",
                "baseline_score": 78  # Simple calls should score higher when done well
            }
        }
        
        # Enhanced scoring prompt with clearer differentiation
        self.performance_scoring_prompt = """
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

    async def score_call_performance(self, combined_transcript: Dict, patient_text: str, staff_text: str) -> Dict:
        """
        Enhanced call performance scoring with better differentiation
        """
        try:
            # Identify call type
            call_type = self._identify_call_type(patient_text, staff_text)
            
            # Get call type configuration
            call_config = self.call_types.get(call_type, self.call_types["general_inquiry"])
            
            # Pre-analyze call quality indicators
            quality_indicators = self._analyze_call_quality_indicators(patient_text, staff_text, call_type)
            
            # Generate enhanced performance scoring prompt
            evaluation_criteria = self._get_evaluation_criteria(call_type)
            scoring_components = self._get_scoring_components(call_type)
            component_structure = self._get_component_json_structure(call_type)
            
            prompt = self.performance_scoring_prompt.format(
                call_type=call_type.replace('_', ' ').title(),
                patient_text=patient_text[:2000],
                staff_text=staff_text[:2000],
                evaluation_criteria=evaluation_criteria,
                scoring_components=scoring_components,
                component_structure=component_structure
            )
            
            # Get LLM analysis
            logger.info(f"Scoring call performance for: {call_type}")
            llm_response = await self.llm_analyzer.generate_response(prompt, max_tokens=1000)
            
            if llm_response:
                # Parse enhanced LLM response
                parsed_scores = self._parse_enhanced_performance_response(llm_response, call_type, quality_indicators)
                
                # Calculate overall score with quality adjustments
                overall_score = self._calculate_enhanced_overall_score(parsed_scores, call_config, quality_indicators)
                
                return {
                    "overall_score": round(overall_score, 3),
                    "overall_grade": self._score_to_grade(overall_score),
                    "call_type": call_type,
                    "component_scores": parsed_scores.get("component_scores", {}),
                    "strengths": parsed_scores.get("strengths", []),
                    "weaknesses": parsed_scores.get("weaknesses", []),
                    "coaching_focus": parsed_scores.get("coaching_focus", []),
                    "overall_assessment": parsed_scores.get("overall_assessment", ""),
                    "meets_expectations": overall_score >= 70,
                    "performance_level": self._get_performance_level(overall_score),
                    "success_achieved": parsed_scores.get("success_achieved", False),
                    "customer_experience_rating": parsed_scores.get("customer_experience_rating", 5),
                    "performance_highlights": parsed_scores.get("performance_highlights", ""),
                    "quality_indicators": quality_indicators,
                    "raw_llm_response": llm_response
                }
            else:
                return self._create_enhanced_fallback_score(call_type, quality_indicators)
                
        except Exception as e:
            logger.error(f"Performance scoring failed: {str(e)}")
            return self._create_enhanced_fallback_score(call_type, {})
    
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
    
    def _get_evaluation_criteria(self, call_type: str) -> str:
        """Get enhanced evaluation criteria specific to call type"""
        
        criteria_map = {
            "appointment_booking": """
APPOINTMENT BOOKING EXPECTATIONS:
- EXCELLENT: Warm greeting, understands needs quickly, offers multiple options, confirms details clearly, professional close
- GOOD: Professional greeting, books appointment efficiently, confirms basic details  
- POOR: Confused about availability, doesn't confirm details, unprofessional tone
KEY SUCCESS METRIC: Appointment successfully scheduled with clear confirmation
""",
            
            "emergency_call": """
EMERGENCY CALL EXPECTATIONS:
- EXCELLENT: Immediate urgency recognition, empathetic response, same-day appointment offered, clear instructions
- GOOD: Recognizes urgency, shows concern, offers prompt appointment
- POOR: Doesn't recognize urgency, no empathy for pain, delays scheduling
KEY SUCCESS METRIC: Same-day or urgent appointment offered for patient in pain
""",
            
            "service_inquiry": """
SERVICE INQUIRY EXPECTATIONS:
- EXCELLENT: Thorough information provided, consultation offered, builds relationship, captures interest
- GOOD: Answers questions clearly, mentions consultation option
- POOR: Vague information, no attempt to schedule consultation, missed sales opportunity
KEY SUCCESS METRIC: Clear information + consultation appointment offered
""",
            
            "insurance_verification": """
INSURANCE VERIFICATION EXPECTATIONS:
- EXCELLENT: Thorough verification process, accurate information, helpful alternatives if not covered
- GOOD: Checks insurance properly, provides clear answer, professional throughout
- POOR: Quick dismissal, inaccurate information, unhelpful attitude
KEY SUCCESS METRIC: Accurate insurance information + helpful guidance
""",
            
            "general_inquiry": """
GENERAL INQUIRY EXPECTATIONS:
- EXCELLENT: Friendly greeting, comprehensive information, offers additional help, professional close
- GOOD: Answers questions clearly, professional manner
- POOR: Rushed responses, incomplete information, unfriendly tone
KEY SUCCESS METRIC: Patient's questions answered clearly and completely
"""
        }
        
        return criteria_map.get(call_type, criteria_map["general_inquiry"])
    
    def _get_scoring_components(self, call_type: str) -> str:
        """Get detailed scoring components for specific call type"""
        
        components_map = {
            "appointment_booking": """
GREETING (15%): Professional introduction and tone
- 90-100: Warm, professional greeting with name and offer to help
- 70-89: Basic professional greeting
- 50-69: Minimal or rushed greeting
- Below 50: No proper greeting or rude

PATIENT_NEEDS (20%): Understanding and addressing scheduling needs  
- 90-100: Asks clarifying questions, shows flexibility, understands urgency
- 70-89: Understands basic needs, some flexibility shown
- 50-69: Basic understanding, limited flexibility
- Below 50: Doesn't understand or address needs

SCHEDULING_EFFECTIVENESS (50%): Success in booking appointment
- 90-100: Multiple options offered, confirms all details, handles obstacles well
- 70-89: Successfully schedules with basic confirmation
- 50-69: Schedules but misses details or shows confusion
- Below 50: Fails to schedule or very unprofessional process

COMMUNICATION_CLARITY (15%): Clear communication throughout
- 90-100: Crystal clear instructions, professional language, good pace
- 70-89: Generally clear communication
- 50-69: Some unclear moments but adequate
- Below 50: Confusing or unprofessional communication
""",
            
            "emergency_call": """
URGENCY_RECOGNITION (35%): Immediately recognizing this is urgent
- 90-100: Immediate recognition, prioritizes urgency, expedites process
- 70-89: Recognizes urgency, responds appropriately
- 50-69: Eventually recognizes urgency but delayed response
- Below 50: Fails to recognize urgency or treats as routine

EMPATHY (25%): Showing concern and understanding for patient's pain
- 90-100: Genuine empathy, comforting words, acknowledges pain
- 70-89: Shows appropriate concern and understanding
- 50-69: Minimal empathy but professional
- Below 50: No empathy or dismissive of patient's pain

IMMEDIATE_SCHEDULING (30%): Offering urgent/same-day appointment
- 90-100: Same-day appointment offered, works around schedule
- 70-89: Urgent appointment within 24 hours offered
- 50-69: Next available appointment (not urgent) offered
- Below 50: No urgent scheduling attempt made

COMMUNICATION (10%): Clear, calming communication
- 90-100: Calm, clear, reassuring communication style
- 70-89: Professional and clear communication
- 50-69: Adequate communication with some issues
- Below 50: Poor or confusing communication
""",
            
            "service_inquiry": """
GREETING (15%): Professional introduction
- 90-100: Warm, welcoming greeting that builds rapport
- 70-89: Professional standard greeting
- 50-69: Basic greeting with minimal warmth
- Below 50: Poor or no proper greeting

INFORMATION_QUALITY (30%): Providing accurate, helpful service information
- 90-100: Comprehensive, accurate information with details and benefits
- 70-89: Good information covering main questions
- 50-69: Basic information but lacking detail
- Below 50: Vague, inaccurate, or unhelpful information

CONSULTATION_BOOKING (40%): Attempting to schedule consultation
- 90-100: Actively promotes consultation, makes it easy to book, shows value
- 70-89: Offers consultation and provides booking option
- 50-69: Mentions consultation but doesn't actively pursue
- Below 50: No consultation offered or discourages booking

RELATIONSHIP_BUILDING (15%): Building rapport with potential patient
- 90-100: Friendly, engaging, makes patient feel valued and comfortable
- 70-89: Professional and friendly interaction
- 50-69: Professional but minimal relationship building
- Below 50: Cold, transactional, or unfriendly
""",
            
            "insurance_verification": """
GREETING (20%): Professional introduction
- 90-100: Warm, professional greeting with clear identification
- 70-89: Standard professional greeting
- 50-69: Basic greeting, adequate professionalism
- Below 50: Poor greeting or unprofessional start

RESEARCH_THOROUGHNESS (35%): Taking time to properly verify insurance
- 90-100: Thorough verification process, asks for details, double-checks
- 70-89: Proper verification with standard questions
- 50-69: Basic verification but may miss details
- Below 50: Rushed or inadequate verification process

INFORMATION_ACCURACY (30%): Providing correct coverage information
- 90-100: Completely accurate information with clear explanations
- 70-89: Accurate information with good explanation
- 50-69: Generally accurate but may lack clarity
- Below 50: Inaccurate or confusing information provided

HELPFULNESS (15%): Being patient and helpful throughout
- 90-100: Extremely helpful, offers alternatives if not covered, patient with questions
- 70-89: Helpful and patient during the process
- 50-69: Adequately helpful but minimal extra effort
- Below 50: Unhelpful attitude or impatient
""",
            
            "general_inquiry": """
GREETING (25%): Professional, friendly introduction
- 90-100: Warm, welcoming greeting that sets positive tone
- 70-89: Professional and friendly greeting
- 50-69: Adequate greeting but lacks warmth
- Below 50: Poor or unfriendly greeting

INFORMATION_HELPFULNESS (50%): Providing clear, complete information
- 90-100: Comprehensive answers, anticipates additional questions, very helpful
- 70-89: Clear answers to all questions asked
- 50-69: Basic answers but may lack completeness
- Below 50: Incomplete, unclear, or unhelpful information

RELATIONSHIP_BUILDING (25%): Professional interaction and rapport
- 90-100: Engaging, builds rapport, makes positive impression, offers additional help
- 70-89: Professional and pleasant interaction
- 50-69: Professional but minimal rapport building
- Below 50: Cold, rushed, or unfriendly interaction
"""
        }
        
        return components_map.get(call_type, components_map["general_inquiry"])
    
    def _get_component_json_structure(self, call_type: str) -> str:
        """Get JSON structure for component scores"""
        
        structure_map = {
            "appointment_booking": '"greeting": [score 0-100], "patient_needs": [score 0-100], "scheduling_effectiveness": [score 0-100], "communication_clarity": [score 0-100]',
            "emergency_call": '"urgency_recognition": [score 0-100], "empathy": [score 0-100], "immediate_scheduling": [score 0-100], "communication": [score 0-100]',
            "service_inquiry": '"greeting": [score 0-100], "information_quality": [score 0-100], "consultation_booking": [score 0-100], "relationship_building": [score 0-100]',
            "insurance_verification": '"greeting": [score 0-100], "research_thoroughness": [score 0-100], "information_accuracy": [score 0-100], "helpfulness": [score 0-100]',
            "general_inquiry": '"greeting": [score 0-100], "information_helpfulness": [score 0-100], "relationship_building": [score 0-100]'
        }
        
        return structure_map.get(call_type, structure_map["general_inquiry"])
    
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