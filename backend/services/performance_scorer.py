"""
Performance scoring service for dental call quality evaluation
"""
import logging
import re
from typing import Dict, List
from prompts.analysis_prompts import AnalysisPrompts

logger = logging.getLogger(__name__)

class PerformanceScorer:
    """Evaluate call performance using LLM analysis"""
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        
        # Call type definitions
        self.call_types = {
            "appointment_booking": {
                "keywords": ["schedule", "appointment", "book", "reschedule", "available"],
                "weights": {"greeting": 0.20, "patient_needs": 0.20, "scheduling_effectiveness": 0.45, "communication_clarity": 0.15},
                "success_criteria": "appointment scheduled successfully"
            },
            "emergency_call": {
                "keywords": ["pain", "emergency", "urgent", "hurt", "swelling"],
                "weights": {"urgency_recognition": 0.40, "empathy": 0.20, "immediate_scheduling": 0.30, "communication": 0.10},
                "success_criteria": "same-day appointment offered"
            },
            "service_inquiry": {
                "keywords": ["cost", "price", "services", "treatment", "procedure"],
                "weights": {"greeting": 0.20, "information_quality": 0.30, "consultation_booking": 0.35, "relationship_building": 0.15},
                "success_criteria": "information provided and consultation offered"
            },
            "insurance_verification": {
                "keywords": ["insurance", "coverage", "benefits", "network", "accept"],
                "weights": {"greeting": 0.25, "research_thoroughness": 0.40, "information_accuracy": 0.25, "helpfulness": 0.10},
                "success_criteria": "accurate insurance information provided"
            },
            "general_inquiry": {
                "keywords": ["location", "hours", "contact", "directions"],
                "weights": {"greeting": 0.30, "information_helpfulness": 0.50, "relationship_building": 0.20},
                "success_criteria": "information provided clearly"
            }
        }
    
    async def score_call_performance(self, combined_transcript: Dict, patient_text: str, staff_text: str) -> Dict:
        """
        Score call performance using LLM analysis
        
        Args:
            combined_transcript: Full transcript with speaker segments
            patient_text: Patient's part of conversation
            staff_text: Staff's part of conversation
            
        Returns:
            Dict with performance scores and analysis
        """
        try:
            # Identify call type
            call_type = self._identify_call_type(patient_text, staff_text)
            
            # Get call type configuration
            call_config = self.call_types.get(call_type, self.call_types["general_inquiry"])
            
            # Generate performance scoring prompt
            evaluation_criteria = AnalysisPrompts.get_evaluation_criteria(call_type)
            scoring_components = AnalysisPrompts.get_scoring_components(call_type)
            
            prompt = AnalysisPrompts.PERFORMANCE_SCORING_PROMPT.format(
                call_type=call_type.replace('_', ' ').title(),
                patient_text=patient_text[:2000],
                staff_text=staff_text[:2000],
                evaluation_criteria=evaluation_criteria,
                scoring_components=scoring_components
            )
            
            # Get LLM analysis
            logger.info(f"Scoring call performance for: {call_type}")
            llm_response = await self.llm_analyzer.generate_response(prompt, max_tokens=700)
            
            if llm_response:
                # Parse LLM response
                parsed_scores = self._parse_performance_response(llm_response, call_type)
                
                # Calculate overall score
                overall_score = self._calculate_overall_score(parsed_scores, call_config["weights"])
                
                return {
                    "overall_score": round(overall_score, 3),
                    "overall_grade": self._score_to_grade(overall_score),
                    "call_type": call_type,
                    "component_scores": parsed_scores["component_scores"],
                    "strengths": parsed_scores.get("strengths", []),
                    "weaknesses": parsed_scores.get("weaknesses", []),
                    "coaching_focus": parsed_scores.get("coaching_focus", []),
                    "overall_assessment": parsed_scores.get("overall_assessment", ""),
                    "meets_expectations": overall_score >= 0.70,
                    "performance_level": self._get_performance_level(overall_score),
                    "success_achieved": self._check_success_achieved(call_type, patient_text, staff_text),
                    "raw_llm_response": llm_response
                }
            else:
                return self._create_fallback_performance_score(call_type)
                
        except Exception as e:
            logger.error(f"Performance scoring failed: {str(e)}")
            return self._create_fallback_performance_score(call_type)
    
    def _identify_call_type(self, patient_text: str, staff_text: str) -> str:
        """Identify the type of call based on content"""
        
        combined_text = (patient_text + " " + staff_text).lower()
        
        # Score each call type
        type_scores = {}
        for call_type, config in self.call_types.items():
            score = sum(1 for keyword in config["keywords"] if keyword in combined_text)
            if score > 0:
                type_scores[call_type] = score
        
        # Return highest scoring type
        if type_scores:
            return max(type_scores, key=type_scores.get)
        else:
            return "general_inquiry"
    
    def _parse_performance_response(self, response: str, call_type: str) -> Dict:
        """Parse LLM performance response"""
        
        parsed = {"component_scores": {}}
        
        # Get expected components for this call type
        call_config = self.call_types[call_type]
        
        # Extract component scores
        for component in call_config["weights"].keys():
            component_upper = component.replace("_", " ").upper()
            
            # Look for score patterns
            score_patterns = [
                f'{component_upper}_SCORE:\\s*(\\d+)',
                f'{component_upper}[:\-]\\s*(\\d+)'
            ]
            
            score = 75  # Default score
            for pattern in score_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    score = max(50, min(100, int(match.group(1))))
                    break
            
            parsed["component_scores"][component] = score / 100.0  # Convert to 0-1 scale
        
        # Extract text sections
        self._extract_text_section(response, parsed, "OVERALL_ASSESSMENT", "overall_assessment")
        self._extract_list_section(response, parsed, "STRENGTHS", "strengths")
        self._extract_list_section(response, parsed, "WEAKNESSES", "weaknesses")
        self._extract_list_section(response, parsed, "COACHING_FOCUS", "coaching_focus")
        
        return parsed
    
    def _extract_text_section(self, response: str, parsed: Dict, section_name: str, key: str):
        """Extract text section from LLM response"""
        pattern = f'{section_name}:\\s*(.+?)(?=\\n\\w+:|$)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            parsed[key] = match.group(1).strip()
        else:
            parsed[key] = f"Assessment not available for {section_name.lower()}"
    
    def _extract_list_section(self, response: str, parsed: Dict, section_name: str, key: str):
        """Extract list section from LLM response"""
        pattern = f'{section_name}:\\s*(.+?)(?=\\n\\w+:|$)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            items_text = match.group(1).strip()
            items = []
            for line in items_text.split('\n'):
                line = line.strip()
                if line and not line.startswith(('OVERALL', 'STRENGTHS', 'WEAKNESSES', 'COACHING')):
                    clean_line = re.sub(r'^[-*\d.\s]+', '', line).strip()
                    if len(clean_line) > 5:
                        items.append(clean_line)
            parsed[key] = items[:3]  # Limit to top 3
        else:
            parsed[key] = []
    
    def _calculate_overall_score(self, parsed_scores: Dict, weights: Dict) -> float:
        """Calculate weighted overall score"""
        
        component_scores = parsed_scores["component_scores"]
        total_score = 0
        
        for component, weight in weights.items():
            score = component_scores.get(component, 0.75)
            total_score += score * weight
        
        return total_score
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.97: return "A+"
        elif score >= 0.93: return "A"
        elif score >= 0.90: return "A-"
        elif score >= 0.87: return "B+"
        elif score >= 0.83: return "B"
        elif score >= 0.80: return "B-"
        elif score >= 0.77: return "C+"
        elif score >= 0.73: return "C"
        elif score >= 0.70: return "C-"
        elif score >= 0.67: return "D+"
        elif score >= 0.63: return "D"
        elif score >= 0.60: return "D-"
        else: return "F"
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level description"""
        if score >= 0.90: return "Exceptional"
        elif score >= 0.80: return "Proficient"
        elif score >= 0.70: return "Satisfactory"
        elif score >= 0.60: return "Needs Improvement"
        else: return "Unsatisfactory"
    
    def _check_success_achieved(self, call_type: str, patient_text: str, staff_text: str) -> bool:
        """Check if primary objective was achieved"""
        
        combined_text = (patient_text + " " + staff_text).lower()
        
        if call_type == "appointment_booking":
            return any(word in combined_text for word in ["scheduled", "booked", "see you"])
        elif call_type == "emergency_call":
            return any(word in combined_text for word in ["today", "right away", "immediately"])
        elif call_type == "service_inquiry":
            return any(word in combined_text for word in ["consultation", "appointment", "schedule"])
        
        return True  # Assume success for other types
    
    def _create_fallback_performance_score(self, call_type: str) -> Dict:
        """Create fallback performance score"""
        return {
            "overall_score": 0.75,
            "overall_grade": "C+",
            "call_type": call_type,
            "component_scores": {"general_performance": 0.75},
            "strengths": ["Call was completed"],
            "weaknesses": ["Detailed analysis unavailable"],
            "coaching_focus": ["Review call recording"],
            "overall_assessment": "LLM analysis unavailable - default score assigned",
            "meets_expectations": True,
            "performance_level": "Satisfactory",
            "success_achieved": True,
            "source": "fallback"
        }
    



    