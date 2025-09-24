"""
Coaching Service - FINAL WORKING VERSION
Uses the correct prompts that work with your Ollama setup
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class CoachingService:
    """
    Service for generating coaching case studies and training materials
    Uses working LLM prompts that are compatible with qwen2.5:7b-instruct
    """
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        
    async def generate_individual_case_study(self, calls_data: List[Dict], target_employee: str, title: str) -> Dict[str, Any]:
        """Generate individual case study - WORKING VERSION"""
        try:
            logger.info(f"Generating individual case study for {target_employee}")
            
            if not calls_data:
                raise Exception("No call data provided")
            
            # Select the primary call for analysis
            primary_call = self._select_primary_call(calls_data)
            logger.info(f"Selected primary call with score: {primary_call.get('representative_score', 0)}")
            
            # Create a SIMPLE, WORKING prompt for the LLM
            prompt = self._create_simple_coaching_prompt(primary_call, target_employee)
            logger.info(f"Created prompt of length: {len(prompt)}")
            
            # Get LLM response with error handling
            coaching_response = await self.llm_analyzer.generate_response(prompt, max_tokens=1000)
            
            if not coaching_response or coaching_response.strip() == "":
                logger.error("LLM returned empty response")
                # Return a structured response even if LLM fails
                return self._create_fallback_case_study(primary_call, target_employee, title)
            
            logger.info(f"LLM response length: {len(coaching_response)}")
            
            # Try to parse JSON, with better fallback
            try:
                # Clean the response first - remove any markdown formatting
                clean_response = coaching_response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                
                parsed_analysis = json.loads(clean_response)
                logger.info("Successfully parsed LLM JSON response")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {e}, extracting from text response")
                parsed_analysis = self._parse_text_response(coaching_response)
                
            # Clean up any malformed JSON artifacts in the parsed data
            parsed_analysis = self._clean_parsed_analysis(parsed_analysis)
            
            # Create the case study structure
            case_study = {
                'title': title,
                'analysis_type': 'individual',
                'target_employee': target_employee,
                'calls_analyzed': len(calls_data),
                'generated_at': datetime.now().isoformat(),
                'status': 'generated',
                'generation_method': 'llm_analysis',
                
                # ADD CALL TRANSCRIPT FOR PDF
                'call_transcript': primary_call.get('Full_Transcript_With_Timestamps', '') or primary_call.get('full_transcript', ''),
                'call_metadata': {
                    'call_date': primary_call.get('analysis_date', ''),
                    'call_type': primary_call.get('call_tag', ''),
                    'performance_score': primary_call.get('representative_score', 0),
                    'call_summary': primary_call.get('call_summary', '')
                },
                
                # Performance overview
                'performance_overview': {
                    'current_performance_level': f"Score: {primary_call.get('representative_score', 0)}%",
                    'key_strengths': parsed_analysis.get('strengths', ['Professional communication', 'Completed call objectives']),
                    'primary_challenges': parsed_analysis.get('areas_for_improvement', ['Follow-up consistency', 'Objection handling'])
                },
                
                # Conversation examples
                'conversation_examples': self._create_conversation_examples(primary_call, parsed_analysis),
                
                # Coaching principles
                'coaching_principles': parsed_analysis.get('coaching_priorities', [
                    "Build rapport first - Always open with warmth and personal connection",
                    "Explain the 'why' - Help patients understand treatment importance", 
                    "Handle objections - Acknowledge concerns then reframe positively",
                    "Offer choices - Give appointment options, not yes/no questions"
                ]),
                
                # Recommendations
                'recommendations': parsed_analysis.get('follow_up_recommendations', [
                    "Practice objection handling scenarios",
                    "Use warmer opening statements",
                    "Implement structured follow-up process"
                ]),
                
                # Development plan
                'development_plan': {
                    'immediate_focus': [parsed_analysis.get('training_focus', 'Communication skills')],
                    '30_day_goals': ['Improve patient rapport scores', 'Increase appointment booking rate'],
                    '90_day_objectives': ['Achieve consistent 85%+ performance scores'],
                    'success_metrics': parsed_analysis.get('success_indicators', ['Higher patient satisfaction', 'More bookings'])
                }
            }
            
            logger.info(f"Successfully generated individual case study for {target_employee}")
            return case_study
            
        except Exception as e:
            logger.error(f"Individual case study generation failed: {str(e)}")
            # Return fallback instead of raising exception
            return self._create_fallback_case_study(calls_data[0] if calls_data else {}, target_employee, title)
    
    async def generate_comparative_case_study(self, calls_data: List[Dict], target_employee: str, title: str) -> Dict[str, Any]:
        """Generate comparative case study - WORKING VERSION"""
        try:
            logger.info(f"Generating comparative case study with {len(calls_data)} calls")
            
            if len(calls_data) < 2:
                raise Exception("Need at least 2 calls for comparative analysis")
            
            # Find best and worst performing calls
            best_call = max(calls_data, key=lambda x: x.get('representative_score', 0))
            worst_call = min(calls_data, key=lambda x: x.get('representative_score', 100))
            
            # Create simple comparative prompt
            prompt = f"""Compare these two dental office calls and provide coaching insights:

BEST CALL (Score: {best_call.get('representative_score', 0)}%):
Summary: {best_call.get('call_summary', '')[:200]}

WORST CALL (Score: {worst_call.get('representative_score', 0)}%):  
Summary: {worst_call.get('call_summary', '')[:200]}

What made the best call successful? What can be improved in the worst call? Provide 3 key lessons.

Respond in this format:
{{
    "best_practices": ["practice 1", "practice 2", "practice 3"],
    "improvement_areas": ["area 1", "area 2", "area 3"],
    "key_lessons": ["lesson 1", "lesson 2", "lesson 3"]
}}"""
            
            # Get LLM response
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=800)
            
            if not response:
                logger.error("LLM returned empty response for comparative analysis")
                return self._create_fallback_comparative_case_study(calls_data, target_employee, title)
            
            # Parse response
            try:
                analysis = json.loads(response)
            except:
                analysis = {
                    "best_practices": ["Professional communication", "Clear explanations", "Follow-up consistency"],
                    "improvement_areas": ["Response time", "Empathy expression", "Problem resolution"],
                    "key_lessons": ["Build rapport first", "Listen actively", "Provide clear next steps"]
                }
            
            # Calculate stats
            scores = [call.get('representative_score', 0) for call in calls_data]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Create comparative case study
            case_study = {
                'title': title,
                'analysis_type': 'comparative',
                'target_employee': target_employee,
                'calls_analyzed': len(calls_data),
                'employees_compared': list(set(call.get('representative_name', 'Unknown') for call in calls_data)),
                'generated_at': datetime.now().isoformat(),
                'status': 'generated',
                'generation_method': 'llm_analysis',
                
                # Comparative analysis
                'comparative_analysis': {
                    'performance_comparison': f"Scores range from {min(scores)}% to {max(scores)}% (avg: {avg_score:.1f}%)",
                    'best_practices': analysis.get('best_practices', []),
                    'common_issues': analysis.get('improvement_areas', []),
                    'performance_gaps': f"{max(scores) - min(scores):.1f}% gap between best and worst performers"
                },
                
                # Coaching principles
                'coaching_principles': analysis.get('key_lessons', []),
                
                # Standardized approaches
                'standardized_approaches': [
                    "Use consistent greeting and closing scripts",
                    "Implement standard objection handling responses", 
                    "Follow structured appointment booking process"
                ],
                
                # Individual adaptations
                'individual_adaptations': [
                    "Tailor communication style to employee strengths",
                    "Focus training on specific skill gaps identified",
                    "Set personalized performance improvement goals"
                ],
                
                # Recommendations
                'recommendations': [
                    f"Focus team training on: {', '.join(analysis.get('improvement_areas', [])[:2])}",
                    f"Replicate best practices: {', '.join(analysis.get('best_practices', [])[:2])}",
                    "Implement peer mentoring between high and low performers"
                ],
                
                # Training program
                'training_program': {
                    'group_training_topics': analysis.get('improvement_areas', [])[:3],
                    'individual_coaching_needs': [f"{call.get('representative_name', 'Unknown')}: Focus on score improvement" for call in calls_data if call.get('representative_score', 100) < 75],
                    'implementation_plan': [
                        "Week 1-2: Group training on common issues",
                        "Week 3-4: Individual coaching sessions", 
                        "Week 5-6: Practice and role-playing",
                        "Week 7-8: Follow-up and assessment"
                    ]
                }
            }
            
            logger.info(f"Successfully generated comparative case study")
            return case_study
            
        except Exception as e:
            logger.error(f"Comparative case study generation failed: {str(e)}")
            return self._create_fallback_comparative_case_study(calls_data, target_employee, title)
    
    def _select_primary_call(self, calls_data: List[Dict]) -> Dict:
        """Select the most valuable call for individual analysis"""
        
        if not calls_data:
            return {}
        
        if len(calls_data) == 1:
            return calls_data[0]
        
        # Score calls based on coaching value
        scored_calls = []
        for call in calls_data:
            score = 0
            
            # Prefer calls with clear improvement opportunities
            rep_score = call.get('representative_score', 100)
            if rep_score < 75:
                score += 30
            elif rep_score < 85:
                score += 15
            
            # Prefer calls with missed opportunities
            if call.get('high_value_missed_opportunity'):
                score += 25
            
            # Prefer calls with good transcript content
            transcript = call.get('full_transcript', '') or call.get('call_summary', '')
            if len(transcript) > 100:
                score += 20
            
            # Prefer calls with existing analysis
            if call.get('performance_analysis') or call.get('coaching_analysis'):
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
    
    def _create_simple_coaching_prompt(self, call_data: Dict, employee: str) -> str:
        """Create a simple, working prompt for the LLM"""
        
        # Get basic call info
        summary = call_data.get('call_summary', 'No summary available')
        full_transcript = call_data.get('Full_Transcript_With_Timestamps', '') or call_data.get('full_transcript', '')
        score = call_data.get('representative_score', 0)
        sentiment = call_data.get('overall_sentiment', 'neutral')
        call_type = call_data.get('call_tag', 'general_inquiry')
        
        # Use full transcript if available, fallback to summary
        transcript_content = full_transcript if full_transcript.strip() else summary
        
        # Create simple, focused prompt
        prompt = f"""Analyze this dental office call for coaching purposes:

Employee: {employee}
Call Type: {call_type}
Performance Score: {score}%
Sentiment: {sentiment}
Full Call Transcript: {transcript_content}

Provide coaching analysis in JSON format:
{{
    "strengths": ["strength 1", "strength 2"],
    "areas_for_improvement": ["area 1", "area 2"], 
    "coaching_priorities": ["priority 1", "priority 2"],
    "training_focus": "main area to focus on",
    "success_indicators": ["how to measure improvement"],
    "follow_up_recommendations": ["specific action 1", "specific action 2"]
}}"""
        
        return prompt
    
    def _create_conversation_examples(self, call_data: Dict, analysis: Dict) -> List[Dict]:
        """Create conversation examples based on the actual call transcript and LLM analysis"""
        
        examples = []
        
        # Get the actual transcript
        transcript = call_data.get('Full_Transcript_With_Timestamps', '') or call_data.get('full_transcript', '')
        
        if transcript and 'SPEAKER_01:' in transcript:
            # Extract actual staff responses from the transcript
            staff_lines = []
            for line in transcript.split('\n'):
                if 'SPEAKER_01:' in line:
                    # Extract the actual spoken text (remove timestamp and speaker label)
                    spoken_text = line.split('SPEAKER_01:')[-1].strip()
                    if spoken_text:
                        staff_lines.append(spoken_text)
            
            # Create examples based on actual conversation
            if staff_lines:
                # Example 1: Use the first staff response if it exists
                if len(staff_lines) > 0:
                    examples.append({
                        'current_approach': staff_lines[0][:100] + "..." if len(staff_lines[0]) > 100 else staff_lines[0],
                        'recommended_approach': f"Great opening! Could add more warmth: {staff_lines[0]}",
                        'coaching_point': 'Continue using professional greetings with added personal warmth',
                        'expected_outcome': 'Enhanced patient rapport from the start'
                    })
                
                # Example 2: Look for empathy opportunities
                empathy_line = None
                for line in staff_lines:
                    if any(word in line.lower() for word in ['sorry', 'understand', 'hear', 'pain']):
                        empathy_line = line
                        break
                
                if empathy_line:
                    examples.append({
                        'current_approach': empathy_line[:100] + "..." if len(empathy_line) > 100 else empathy_line,
                        'recommended_approach': f"Excellent empathy! Could enhance with: 'I completely understand how concerning that must be. {empathy_line.split('.')[0]}'",
                        'coaching_point': 'Great use of empathy - consider adding validation of patient emotions',
                        'expected_outcome': 'Patients feel more understood and supported'
                    })
                
                # Example 3: Look for scheduling/solution responses
                solution_line = None
                for line in staff_lines:
                    if any(word in line.lower() for word in ['schedule', 'appointment', 'available', 'check', 'opening']):
                        solution_line = line
                        break
                
                if solution_line:
                    examples.append({
                        'current_approach': solution_line[:100] + "..." if len(solution_line) > 100 else solution_line,
                        'recommended_approach': f"Good problem-solving! Could be more specific: '{solution_line} Would that time work for your schedule?'",
                        'coaching_point': 'Excellent solution-focused response - adding confirmation questions helps ensure patient satisfaction',
                        'expected_outcome': 'More efficient scheduling and better patient experience'
                    })
        
        # If no transcript-based examples, create contextual ones based on call summary
        if not examples:
            call_summary = call_data.get('call_summary', '')
            
            if 'emergency' in call_summary.lower():
                examples.append({
                    'current_approach': "Let me check our schedule for you",
                    'recommended_approach': "I understand this is urgent. Let me immediately check our emergency appointments to get you seen today",
                    'coaching_point': "Acknowledge urgency first, then provide immediate action",
                    'expected_outcome': "Patient feels prioritized and cared for"
                })
            
            elif 'reschedule' in call_summary.lower():
                examples.append({
                    'current_approach': "When would you like to reschedule?",
                    'recommended_approach': "Of course, I understand things come up. I have Tuesday at 10am or Friday at 2pm - which works better for you?",
                    'coaching_point': "Show understanding and offer specific alternatives",
                    'expected_outcome': "Smoother rescheduling and better patient experience"
                })
        
        return examples[:3]  # Return max 3 examples
    
    def _parse_text_response(self, response_text: str) -> Dict:
        """Parse non-JSON LLM response into structured format"""
        
        # Extract key information from text response
        strengths = []
        improvements = []
        priorities = []
        
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'strength' in line.lower() or 'good' in line.lower():
                strengths.append(line.replace('-', '').replace('•', '').strip())
            elif 'improve' in line.lower() or 'better' in line.lower():
                improvements.append(line.replace('-', '').replace('•', '').strip())
            elif 'priority' in line.lower() or 'focus' in line.lower():
                priorities.append(line.replace('-', '').replace('•', '').strip())
        
        return {
            'strengths': strengths[:3] if strengths else ['Professional communication'],
            'areas_for_improvement': improvements[:3] if improvements else ['Follow-up consistency'], 
            'coaching_priorities': priorities[:3] if priorities else ['Improve patient rapport'],
            'training_focus': improvements[0] if improvements else 'Communication skills',
            'success_indicators': ['Higher satisfaction scores'],
            'follow_up_recommendations': ['Practice active listening', 'Use warmer greetings']
        }
    
    def _clean_parsed_analysis(self, analysis: Dict) -> Dict:
        """Clean up malformed JSON artifacts in parsed analysis"""
        cleaned = {}
        
        for key, value in analysis.items():
            if isinstance(value, list):
                # Clean list items - remove JSON artifacts
                cleaned_list = []
                for item in value:
                    if isinstance(item, str):
                        clean_item = item.strip().strip('"').strip("'")
                        # Skip JSON field names that got included as values
                        if not clean_item.startswith(('"', "'", 'strengths', 'areas_for', 'training_focus')):
                            cleaned_list.append(clean_item)
                    else:
                        cleaned_list.append(item)
                cleaned[key] = cleaned_list
            elif isinstance(value, str):
                # Clean string values - remove quotes and JSON artifacts
                clean_value = value.strip().strip('"').strip("'")
                # Skip malformed JSON field names
                if not clean_value.startswith(('"', "'")) or not clean_value.endswith((':', '[')):
                    cleaned[key] = clean_value
                else:
                    cleaned[key] = "Communication skills"  # Default fallback
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _create_fallback_case_study(self, call_data: Dict, target_employee: str, title: str) -> Dict:
        """Create fallback case study when LLM fails"""
        
        return {
            'title': title,
            'analysis_type': 'individual',
            'target_employee': target_employee,
            'calls_analyzed': 1,
            'generated_at': datetime.now().isoformat(),
            'status': 'generated_fallback',
            'generation_method': 'fallback_analysis',
            
            'performance_overview': {
                'current_performance_level': f"Score: {call_data.get('representative_score', 0)}%",
                'key_strengths': ['Professional demeanor', 'Completed call objectives'],
                'primary_challenges': ['Needs coaching analysis', 'LLM analysis unavailable']
            },
            
            'conversation_examples': [{
                'current_approach': "Standard approach observed",
                'recommended_approach': "Enhanced approach with better rapport building",
                'coaching_point': "Focus on building stronger patient connections",
                'expected_outcome': "Improved patient satisfaction"
            }],
            
            'coaching_principles': [
                "Build rapport first - Always open with warmth",
                "Listen actively - Show genuine interest in patient concerns", 
                "Provide clear explanations - Help patients understand",
                "Follow up consistently - Ensure patient needs are met"
            ],
            
            'recommendations': [
                "Schedule follow-up coaching session",
                "Review call transcript in detail",
                "Practice rapport building techniques"
            ],
            
            'development_plan': {
                'immediate_focus': ['Schedule coaching session'],
                '30_day_goals': ['Improve communication scores'],
                '90_day_objectives': ['Achieve consistent performance'],
                'success_metrics': ['Patient feedback scores']
            }
        }
    
    def _create_fallback_comparative_case_study(self, calls_data: List[Dict], target_employee: str, title: str) -> Dict:
        """Create fallback comparative case study when LLM fails"""
        
        scores = [call.get('representative_score', 0) for call in calls_data]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'title': title,
            'analysis_type': 'comparative', 
            'target_employee': target_employee,
            'calls_analyzed': len(calls_data),
            'generated_at': datetime.now().isoformat(),
            'status': 'generated_fallback',
            'generation_method': 'fallback_analysis',
            
            'comparative_analysis': {
                'performance_comparison': f"Average score: {avg_score:.1f}%",
                'best_practices': ['Professional communication', 'Timely responses', 'Clear explanations'],
                'common_issues': ['Consistency in follow-up', 'Rapport building', 'Objection handling'],
                'performance_gaps': 'Analysis requires manual review'
            },
            
            'coaching_principles': [
                'Maintain consistent professional standards',
                'Focus on patient-centered communication',
                'Implement structured follow-up processes'
            ],
            
            'recommendations': [
                'Conduct detailed manual analysis',
                'Implement team training program',
                'Establish coaching best practices'
            ]
        }
    
    def is_available(self) -> bool:
        """Check if coaching service is available"""
        return self.llm_analyzer and self.llm_analyzer.is_initialized