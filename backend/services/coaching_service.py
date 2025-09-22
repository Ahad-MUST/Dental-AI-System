"""
Coaching Service - Backend service for generating coaching materials and case studies
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from services.llm_analyzer import LLMAnalyzer
from services.pdf_generator import CoachingPDFGenerator

logger = logging.getLogger(__name__)

class CoachingService:
    """
    Service for generating coaching case studies and training materials
    """
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm_analyzer = llm_analyzer
        self.pdf_generator = CoachingPDFGenerator()
        
    async def generate_case_study(self, calls_data: List[Dict], analysis_type: str, 
                                target_employee: str, title: str) -> Dict[str, Any]:
        """
        Generate a comprehensive case study from selected calls
        
        Args:
            calls_data: List of call dictionaries with transcripts and analysis
            analysis_type: 'individual' or 'comparative'
            target_employee: Name of employee for training
            title: Title for the case study
            
        Returns:
            Dictionary containing case study analysis
        """
        try:
            logger.info(f"Generating {analysis_type} case study for {target_employee}")
            
            if analysis_type == 'individual':
                return await self._generate_individual_case_study(calls_data, target_employee, title)
            else:
                return await self._generate_comparative_case_study(calls_data, target_employee, title)
                
        except Exception as e:
            logger.error(f"Case study generation failed: {str(e)}")
            raise
    
    async def _generate_individual_case_study(self, calls_data: List[Dict], 
                                            target_employee: str, title: str) -> Dict[str, Any]:
        """Generate individual employee training case study"""
        
        # Select the best call for detailed analysis
        primary_call = self._select_primary_call(calls_data)
        
        # Generate coaching insights
        coaching_prompt = self._build_individual_coaching_prompt(primary_call, target_employee)
        coaching_analysis = await self.llm_analyzer.generate_response(coaching_prompt, max_tokens=2000)
        
        # Parse the coaching analysis
        parsed_analysis = self._parse_coaching_analysis(coaching_analysis)
        
        # Generate what-was-said vs what-to-say examples
        examples = await self._generate_conversation_examples(primary_call)
        
        # Compile case study
        case_study = {
            'title': title,
            'type': 'individual',
            'target_employee': target_employee,
            'primary_call': primary_call,
            'coaching_analysis': parsed_analysis,
            'conversation_examples': examples,
            'key_principles': self._extract_key_principles(parsed_analysis),
            'follow_up_flow': self._generate_follow_up_flow(primary_call),
            'success_metrics': self._define_success_metrics(parsed_analysis),
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Individual case study generated for {target_employee}")
        return case_study
    
    async def _generate_comparative_case_study(self, calls_data: List[Dict], 
                                             target_employee: str, title: str) -> Dict[str, Any]:
        """Generate comparative analysis case study"""
        
        # Analyze patterns across calls
        pattern_analysis = await self._analyze_call_patterns(calls_data)
        
        # Find best and worst examples
        best_call = max(calls_data, key=lambda x: x.get('representative_score', 0))
        worst_call = min(calls_data, key=lambda x: x.get('representative_score', 100))
        
        # Generate comparative insights
        comparison_prompt = self._build_comparative_prompt(calls_data, best_call, worst_call)
        comparison_analysis = await self.llm_analyzer.generate_response(comparison_prompt, max_tokens=2500)
        
        # Parse comparative analysis
        parsed_comparison = self._parse_comparative_analysis(comparison_analysis)
        
        # Compile case study
        case_study = {
            'title': title,
            'type': 'comparative',
            'target_employee': target_employee,
            'calls_analyzed': len(calls_data),
            'pattern_analysis': pattern_analysis,
            'best_practice_example': best_call,
            'improvement_example': worst_call,
            'comparative_analysis': parsed_comparison,
            'common_patterns': self._identify_common_patterns(calls_data),
            'training_recommendations': self._generate_training_recommendations(parsed_comparison),
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Comparative case study generated with {len(calls_data)} calls")
        return case_study
    
    def _select_primary_call(self, calls_data: List[Dict]) -> Dict:
        """Select the most valuable call for individual analysis"""
        
        # Score calls based on coaching value
        scored_calls = []
        for call in calls_data:
            score = 0
            
            # Prefer calls with clear improvement opportunities
            if call.get('representative_score', 100) < 75:
                score += 30
            
            # Prefer calls with missed opportunities
            if call.get('high_value_missed_opportunity'):
                score += 25
            
            # Prefer calls with good transcript quality
            patient_text = call.get('patient_transcript', '')
            staff_text = call.get('staff_transcript', '')
            if len(patient_text) > 100 and len(staff_text) > 100:
                score += 20
            
            # Prefer calls with performance analysis
            if call.get('performance_analysis', {}).get('coaching_focus'):
                score += 15
            
            # Prefer recent calls
            try:
                call_date = datetime.fromisoformat(call.get('analysis_date', ''))
                days_old = (datetime.now() - call_date).days
                if days_old < 30:
                    score += 10
            except:
                pass
            
            scored_calls.append((call, score))
        
        # Return highest scoring call
        return max(scored_calls, key=lambda x: x[1])[0]
    
    def _build_individual_coaching_prompt(self, call_data: Dict, employee: str) -> str:
        """Build prompt for individual coaching analysis"""
        
        return f"""
You are creating a coaching case study for {employee} based on a real call. 
Analyze this call and provide specific, actionable coaching insights.

CALL DATA:
Employee: {call_data.get('representative_name', employee)}
Date: {call_data.get('analysis_date', 'Unknown')}
Performance Score: {call_data.get('representative_score', 'Unknown')}%
Call Type: {call_data.get('call_tag', 'Unknown')}
Overall Sentiment: {call_data.get('overall_sentiment', 'Unknown')}

PATIENT TRANSCRIPT:
{call_data.get('patient_transcript', 'Not available')}

STAFF TRANSCRIPT:
{call_data.get('staff_transcript', 'Not available')}

CURRENT PERFORMANCE ANALYSIS:
{json.dumps(call_data.get('performance_analysis', {}), indent=2)}

Please provide a detailed coaching analysis in JSON format:
{{
    "overall_assessment": "Comprehensive assessment of the call quality and employee performance",
    "strengths": ["Specific strength 1", "Specific strength 2", "Specific strength 3"],
    "areas_for_improvement": ["Specific area 1", "Specific area 2", "Specific area 3"],
    "coaching_priorities": ["Priority 1", "Priority 2", "Priority 3"],
    "specific_examples": [
        {{
            "what_was_said": "Exact quote from the call",
            "what_should_be_said": "Improved version",
            "coaching_point": "Why this improvement matters"
        }}
    ],
    "training_focus": "Primary area to focus training on",
    "success_indicators": ["How to measure improvement"],
    "follow_up_recommendations": ["Specific next steps for coaching"]
}}

Focus on practical, actionable advice that can be immediately applied.
"""
    
    def _build_comparative_prompt(self, calls_data: List[Dict], best_call: Dict, worst_call: Dict) -> str:
        """Build prompt for comparative analysis"""
        
        return f"""
You are analyzing {len(calls_data)} calls to identify patterns and create comparative coaching insights.

BEST PERFORMING CALL:
Employee: {best_call.get('representative_name', 'Unknown')}
Score: {best_call.get('representative_score', 0)}%
Patient: {best_call.get('patient_transcript', '')[:500]}...
Staff: {best_call.get('staff_transcript', '')[:500]}...

LOWEST PERFORMING CALL:
Employee: {worst_call.get('representative_name', 'Unknown')}
Score: {worst_call.get('representative_score', 0)}%
Patient: {worst_call.get('patient_transcript', '')[:500]}...
Staff: {worst_call.get('staff_transcript', '')[:500]}...

CALL SUMMARY DATA:
{json.dumps([{
    'employee': call.get('representative_name'),
    'score': call.get('representative_score'),
    'sentiment': call.get('overall_sentiment'),
    'call_type': call.get('call_tag')
} for call in calls_data], indent=2)}

Provide comparative analysis in JSON format:
{{
    "pattern_analysis": {{
        "common_strengths": ["Pattern 1", "Pattern 2"],
        "common_weaknesses": ["Pattern 1", "Pattern 2"],
        "performance_factors": ["Factor that drives good performance"]
    }},
    "best_practices": [
        {{
            "practice": "What the best performer did well",
            "example": "Specific example from transcript",
            "impact": "Why this was effective"
        }}
    ],
    "improvement_opportunities": [
        {{
            "opportunity": "What could be improved",
            "example": "Specific example from poor call",
            "solution": "How to improve this"
        }}
    ],
    "training_recommendations": [
        {{
            "focus_area": "What to train on",
            "methods": ["Training method 1", "Training method 2"],
            "expected_outcome": "What improvement to expect"
        }}
    ],
    "success_metrics": ["How to measure improvement across the team"]
}}
"""
    
    async def _generate_conversation_examples(self, call_data: Dict) -> List[Dict]:
        """Generate what-was-said vs what-to-say examples"""
        
        examples_prompt = f"""
Based on this call transcript, create 3-5 specific examples of "What Was Said" vs "What to Say Instead" 
for training purposes.

PATIENT TRANSCRIPT:
{call_data.get('patient_transcript', '')}

STAFF TRANSCRIPT:
{call_data.get('staff_transcript', '')}

PERFORMANCE ISSUES:
{json.dumps(call_data.get('performance_analysis', {}).get('weaknesses', []))}

Create examples in this exact format:
[
    {{
        "what_was_said": "Exact quote from staff member",
        "what_to_say_instead": "Improved version of the same interaction",
        "coaching_point": "Brief explanation of why the improvement is better",
        "impact": "Expected patient experience improvement"
    }}
]

Focus on the most impactful improvements that would enhance patient satisfaction and booking rates.
"""
        
        response = await self.llm_analyzer.generate_response(examples_prompt, max_tokens=1500)
        
        try:
            return json.loads(response)
        except:
            # Fallback to structured examples if JSON parsing fails
            return self._create_fallback_examples(call_data)
    
    def _parse_coaching_analysis(self, analysis_text: str) -> Dict:
        """Parse LLM coaching analysis response"""
        try:
            return json.loads(analysis_text)
        except:
            # Create structured fallback
            return {
                "overall_assessment": "Analysis parsing failed - manual review needed",
                "strengths": ["Communication attempt", "Professional tone"],
                "areas_for_improvement": ["Needs detailed analysis", "Review transcript manually"],
                "coaching_priorities": ["Schedule follow-up review"],
                "training_focus": "Communication skills",
                "success_indicators": ["Improved customer satisfaction"],
                "follow_up_recommendations": ["Manual coaching session needed"]
            }
    
    def _parse_comparative_analysis(self, analysis_text: str) -> Dict:
        """Parse comparative analysis response"""
        try:
            return json.loads(analysis_text)
        except:
            return {
                "pattern_analysis": {
                    "common_strengths": ["Professional greeting"],
                    "common_weaknesses": ["Follow-up inconsistency"],
                    "performance_factors": ["Call preparation"]
                },
                "best_practices": [],
                "improvement_opportunities": [],
                "training_recommendations": [],
                "success_metrics": ["Customer satisfaction scores"]
            }
    
    def _extract_key_principles(self, analysis: Dict) -> List[str]:
        """Extract key coaching principles from analysis"""
        principles = [
            "Build rapport first: Always open with a warm greeting and personal connection",
            "Explain the 'why': Patients need to understand why treatment matters now",
            "Handle objections: Acknowledge concerns, then reframe with benefits",
            "Give two choices: Offer two appointment times, not a yes/no question",
            "Address money early: Mention financing so cost isn't a hidden barrier",
            "Never end at a dead stop: If no booking, set a specific follow-up plan"
        ]
        
        # Add specific principles based on analysis
        if analysis.get('training_focus'):
            principles.append(f"Focus Area: {analysis['training_focus']}")
        
        return principles
    
    def _generate_follow_up_flow(self, call_data: Dict) -> Dict:
        """Generate standard follow-up flow based on call type"""
        
        return {
            "steps": [
                "1. Greeting + rapport",
                "2. Treatment reminder with benefit",
                "3. Offer appointment (2 options)",
                "4. Handle objections (time, cost, fear)",
                "5. Mention financing options",
                "6. Close with booking or scheduled follow-up"
            ],
            "goal": "The goal is not just to 'call and ask,' but to educate, guide, and secure a next step — either a booking or a clear follow-up date.",
            "key_message": "Every patient left without a plan is a lost opportunity."
        }
    
    def _define_success_metrics(self, analysis: Dict) -> List[str]:
        """Define success metrics for coaching improvement"""
        
        metrics = [
            "Increased appointment booking rate",
            "Improved patient satisfaction scores",
            "Reduced call abandonment rate",
            "Higher treatment acceptance rate"
        ]
        
        # Add specific metrics based on analysis
        if "communication" in analysis.get('training_focus', '').lower():
            metrics.append("Better patient rapport scores")
        
        if "booking" in analysis.get('training_focus', '').lower():
            metrics.append("More appointments scheduled per call")
        
        return metrics
    
    async def _analyze_call_patterns(self, calls_data: List[Dict]) -> Dict:
        """Analyze patterns across multiple calls"""
        
        # Calculate statistics
        scores = [call.get('representative_score', 0) for call in calls_data]
        sentiments = [call.get('overall_sentiment', 'neutral') for call in calls_data]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        positive_sentiment_rate = len([s for s in sentiments if s == 'positive']) / len(sentiments) if sentiments else 0
        
        return {
            'total_calls': len(calls_data),
            'average_score': round(avg_score, 1),
            'score_range': {'min': min(scores) if scores else 0, 'max': max(scores) if scores else 0},
            'positive_sentiment_rate': round(positive_sentiment_rate * 100, 1),
            'common_call_types': self._get_common_call_types(calls_data),
            'performance_distribution': self._analyze_score_distribution(scores)
        }
    
    def _get_common_call_types(self, calls_data: List[Dict]) -> List[Dict]:
        """Get distribution of call types"""
        call_types = {}
        for call in calls_data:
            call_type = call.get('call_tag', 'unknown')
            call_types[call_type] = call_types.get(call_type, 0) + 1
        
        return [{'type': k, 'count': v} for k, v in sorted(call_types.items(), key=lambda x: x[1], reverse=True)]
    
    def _analyze_score_distribution(self, scores: List[float]) -> Dict:
        """Analyze performance score distribution"""
        if not scores:
            return {'excellent': 0, 'good': 0, 'needs_improvement': 0}
        
        excellent = len([s for s in scores if s >= 85])
        good = len([s for s in scores if 70 <= s < 85])
        needs_improvement = len([s for s in scores if s < 70])
        
        total = len(scores)
        return {
            'excellent': round(excellent / total * 100, 1),
            'good': round(good / total * 100, 1),
            'needs_improvement': round(needs_improvement / total * 100, 1)
        }
    
    def _identify_common_patterns(self, calls_data: List[Dict]) -> Dict:
        """Identify common patterns across calls"""
        
        # Extract common strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        
        for call in calls_data:
            performance = call.get('performance_analysis', {})
            all_strengths.extend(performance.get('strengths', []))
            all_weaknesses.extend(performance.get('weaknesses', []))
        
        # Count frequency
        strength_counts = {}
        weakness_counts = {}
        
        for strength in all_strengths:
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
            
        for weakness in all_weaknesses:
            weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
        
        return {
            'common_strengths': [k for k, v in sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:5]],
            'common_weaknesses': [k for k, v in sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        }
    
    def _generate_training_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate specific training recommendations"""
        
        recommendations = []
        
        # Add recommendations based on pattern analysis
        if analysis.get('pattern_analysis', {}).get('common_weaknesses'):
            for weakness in analysis['pattern_analysis']['common_weaknesses'][:3]:
                recommendations.append({
                    'area': weakness,
                    'method': 'Role-playing exercises and script practice',
                    'frequency': 'Weekly practice sessions',
                    'measurement': 'Score improvement in weekly assessments'
                })
        
        return recommendations
    
    def _create_fallback_examples(self, call_data: Dict) -> List[Dict]:
        """Create fallback examples when LLM parsing fails"""
        
        return [
            {
                "what_was_said": "I'm calling about your treatment.",
                "what_to_say_instead": "Hi [Name], this is [Your Name] from [Practice]. How have you been since your last visit?",
                "coaching_point": "Build rapport first with a warm, personal greeting",
                "impact": "Patient feels valued and conversation starts positively"
            },
            {
                "what_was_said": "Do you want to schedule that treatment?",
                "what_to_say_instead": "We have availability this Tuesday afternoon or Friday morning. Which works better for you?",
                "coaching_point": "Give two specific options instead of a yes/no question",
                "impact": "Higher booking rate by making scheduling feel easy and inevitable"
            }
        ]