"""
Coaching Service - UPDATED VERSION WITH ENHANCED PROMPTS
Now uses dedicated prompt file for improved LLM analysis quality
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Import the enhanced prompts
from prompts.coaching_prompts import (
    get_individual_call_analysis_prompt,
    get_comparative_analysis_prompt,
    get_conversation_example_extraction_prompt
)

logger = logging.getLogger(__name__)

class CoachingService:
    """
    Service for generating coaching case studies and training materials
    UPDATED: Now uses enhanced prompts for better LLM analysis quality
    """
    
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer
        
    async def generate_individual_case_study(self, calls_data: List[Dict], target_employee: str, title: str) -> Dict[str, Any]:
        """Generate individual case study - UPDATED WITH ENHANCED PROMPTS"""
        try:
            logger.info(f"Generating individual case study for {target_employee} with {len(calls_data)} calls")
            
            if not calls_data:
                raise Exception("No call data provided")
            
            # UPDATED: Analyze ALL calls individually with enhanced prompts
            individual_call_analyses = []
            
            for i, call in enumerate(calls_data, 1):
                logger.info(f"Analyzing call {i} of {len(calls_data)}: {call.get('representative_name', 'Unknown')} - Score: {call.get('representative_score', 0)}")
                
                try:
                    # UPDATED: Use enhanced prompt for better analysis
                    call_analysis = await self._analyze_single_call_enhanced(call, target_employee, i)
                    individual_call_analyses.append(call_analysis)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze call {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully analyzed {len(individual_call_analyses)} calls with enhanced prompts")
            
            # Create comprehensive case study structure with ALL call analyses
            case_study = {
                'title': title,
                'analysis_type': 'individual',
                'target_employee': target_employee,
                'calls_analyzed': len(calls_data),
                'generated_at': datetime.now().isoformat(),
                'status': 'generated',
                'generation_method': 'enhanced_llm_analysis',
                
                # UPDATED: Include all enhanced individual call analyses
                'individual_call_analyses': individual_call_analyses,
                
                # Overall summary combining all calls
                'overall_summary': self._create_overall_summary(individual_call_analyses, target_employee),
                
                # Combined insights from all calls
                'combined_insights': self._combine_insights_from_all_calls(individual_call_analyses),
                
                # Comprehensive development plan
                'comprehensive_development_plan': self._create_comprehensive_development_plan(individual_call_analyses, target_employee)
            }
            
            logger.info(f"Successfully generated enhanced individual case study for {target_employee}")
            return case_study
            
        except Exception as e:
            logger.error(f"Individual case study generation failed: {str(e)}")
            raise e
    
    async def _analyze_single_call_enhanced(self, call_data: Dict, employee: str, call_number: int) -> Dict:
        """Analyze a single call with enhanced LLM prompt - UPDATED"""
        
        # UPDATED: Use enhanced prompt from prompts file
        prompt = get_individual_call_analysis_prompt(call_data, employee)
        
        # Get LLM response for this specific call with enhanced prompt
        coaching_response = await self.llm_analyzer.generate_response(prompt, max_tokens=1500)
        
        if not coaching_response or coaching_response.strip() == "":
            logger.warning(f"LLM returned empty response for call {call_number}")
            raise Exception("Empty LLM response")
        
        try:
            # Clean and parse JSON response
            clean_response = coaching_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            
            parsed_analysis = json.loads(clean_response)
            logger.info(f"Successfully parsed enhanced LLM response for call {call_number}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed for call {call_number}: {e}")
            # UPDATED: Try to extract conversation examples separately if main parsing fails
            await self._try_extract_conversation_examples(call_data, call_number)
            raise e
        
        # UPDATED: Create enhanced call analysis structure with new fields
        call_analysis = {
            'call_number': call_number,
            'call_metadata': {
                'call_date': call_data.get('analysis_date', ''),
                'call_time': call_data.get('analysis_time', ''),
                'call_type': call_data.get('call_tag', ''),
                'performance_score': call_data.get('representative_score', 0),
                'overall_sentiment': call_data.get('overall_sentiment', 'neutral'),
                'call_summary': call_data.get('call_summary', ''),
                'representative_name': call_data.get('representative_name', employee)
            },
            
            # Full transcript for this call
            'call_transcript': call_data.get('full_transcript', '') or call_data.get('Full_Transcript_With_Timestamps', ''),
            
            # UPDATED: Enhanced LLM analysis results with new fields
            'llm_analysis': parsed_analysis,
            
            # UPDATED: Enhanced performance overview
            'performance_overview': {
                'current_performance_level': f"Score: {call_data.get('representative_score', 0)}%",
                'key_strengths': parsed_analysis.get('strengths', []),
                'primary_challenges': parsed_analysis.get('areas_for_improvement', []),
                'technical_issues_detected': parsed_analysis.get('technical_issues_detected', False)
            },
            
            # UPDATED: Real conversation examples from enhanced prompt
            'conversation_examples': parsed_analysis.get('conversation_examples', []),
            
            # UPDATED: Enhanced coaching recommendations 
            'call_specific_recommendations': parsed_analysis.get('follow_up_recommendations', []),
            
            # Training focus for this call
            'training_focus': parsed_analysis.get('training_focus', 'Communication skills'),
            
            # UPDATED: New field for transcript-based insights
            'transcript_insights': parsed_analysis.get('transcript_based_insights', [])
        }
        
        return call_analysis
    
    async def _try_extract_conversation_examples(self, call_data: Dict, call_number: int):
        """Try to extract conversation examples separately if main analysis fails"""
        try:
            transcript = call_data.get('full_transcript', '') or call_data.get('Full_Transcript_With_Timestamps', '')
            if not transcript:
                return []
            
            prompt = get_conversation_example_extraction_prompt(transcript)
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=800)
            
            if response:
                examples_data = json.loads(response.strip())
                logger.info(f"Successfully extracted conversation examples for call {call_number}")
                return examples_data.get('conversation_examples', [])
        except Exception as e:
            logger.warning(f"Failed to extract conversation examples for call {call_number}: {e}")
            return []
    
    async def generate_comparative_case_study(self, calls_data: List[Dict], target_employee: str, title: str) -> Dict[str, Any]:
        """Generate comparative case study - UPDATED WITH ENHANCED PROMPT"""
        try:
            logger.info(f"Generating comparative case study with {len(calls_data)} calls")
            
            if len(calls_data) < 2:
                raise Exception("Need at least 2 calls for comparative analysis")
            
            # UPDATED: Use enhanced comparative analysis prompt
            prompt = get_comparative_analysis_prompt(calls_data, target_employee, title)
            
            # Get LLM response with enhanced prompt
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=1200)
            
            if not response:
                logger.error("LLM returned empty response for comparative analysis")
                raise Exception("Empty LLM response for comparative analysis")
            
            # Parse enhanced response
            try:
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                analysis = json.loads(clean_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse comparative analysis response: {e}")
                raise e
            
            # Calculate stats
            scores = [call.get('representative_score', 0) for call in calls_data]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # UPDATED: Create enhanced comparative case study
            case_study = {
                'title': title,
                'analysis_type': 'comparative',
                'target_employee': target_employee,
                'calls_analyzed': len(calls_data),
                'employees_compared': list(set(call.get('representative_name', 'Unknown') for call in calls_data)),
                'generated_at': datetime.now().isoformat(),
                'status': 'generated',
                'generation_method': 'enhanced_llm_analysis',
                
                # UPDATED: Enhanced comparative analysis with new structure
                'comparative_analysis': analysis,
                
                # UPDATED: Enhanced coaching principles from LLM
                'coaching_principles': analysis.get('key_lessons', []),
                
                # Performance metrics
                'performance_metrics': {
                    'average_score': round(avg_score, 1),
                    'score_range': f"{min(scores)}% to {max(scores)}%",
                    'total_calls': len(calls_data)
                },
                
                # UPDATED: Enhanced training program from LLM analysis
                'training_program': analysis.get('training_recommendations', [])
            }
            
            logger.info(f"Successfully generated enhanced comparative case study")
            return case_study
            
        except Exception as e:
            logger.error(f"Comparative case study generation failed: {str(e)}")
            raise e
    
    # Keep all existing helper methods unchanged - they work with the new enhanced data structure
    def _create_overall_summary(self, call_analyses: List[Dict], target_employee: str) -> Dict:
        """Create overall summary combining insights from all analyzed calls"""
        
        total_calls = len(call_analyses)
        if total_calls == 0:
            return {'message': 'No calls analyzed'}
        
        # Calculate average performance
        scores = [call.get('call_metadata', {}).get('performance_score', 0) for call in call_analyses]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Collect all strengths across calls
        all_strengths = []
        all_challenges = []
        all_focus_areas = []
        technical_issues_count = 0
        
        for call in call_analyses:
            strengths = call.get('performance_overview', {}).get('key_strengths', [])
            challenges = call.get('performance_overview', {}).get('primary_challenges', [])
            focus = call.get('training_focus', '')
            technical_issues = call.get('performance_overview', {}).get('technical_issues_detected', False)
            
            all_strengths.extend(strengths)
            all_challenges.extend(challenges)
            if focus:
                all_focus_areas.append(focus)
            if technical_issues:
                technical_issues_count += 1
        
        # Find most common patterns
        from collections import Counter
        common_strengths = [item for item, count in Counter(all_strengths).most_common(5)]
        common_challenges = [item for item, count in Counter(all_challenges).most_common(5)]
        common_focus_areas = [item for item, count in Counter(all_focus_areas).most_common(3)]
        
        return {
            'total_calls_analyzed': total_calls,
            'average_performance_score': round(avg_score, 1),
            'score_range': {
                'highest': max(scores) if scores else 0,
                'lowest': min(scores) if scores else 0
            },
            'common_strengths': common_strengths,
            'common_challenges': common_challenges,
            'primary_focus_areas': common_focus_areas,
            'technical_issues_detected': technical_issues_count,
            'target_employee': target_employee,
            'analysis_period': {
                'start_date': min([call.get('call_metadata', {}).get('call_date', '') for call in call_analyses]),
                'end_date': max([call.get('call_metadata', {}).get('call_date', '') for call in call_analyses])
            }
        }
    
    def _combine_insights_from_all_calls(self, call_analyses: List[Dict]) -> Dict:
        """Combine insights from all calls to create comprehensive coaching principles"""
        
        # Collect all coaching priorities and recommendations
        all_priorities = []
        all_recommendations = []
        all_transcript_insights = []
        
        for call in call_analyses:
            llm_analysis = call.get('llm_analysis', {})
            priorities = llm_analysis.get('coaching_priorities', [])
            recommendations = call.get('call_specific_recommendations', [])
            insights = call.get('transcript_insights', [])
            
            all_priorities.extend(priorities)
            all_recommendations.extend(recommendations)
            all_transcript_insights.extend(insights)
        
        # Remove duplicates while preserving order
        unique_priorities = []
        unique_recommendations = []
        unique_insights = []
        
        for item in all_priorities:
            if item not in unique_priorities:
                unique_priorities.append(item)
        
        for item in all_recommendations:
            if item not in unique_recommendations:
                unique_recommendations.append(item)
                
        for item in all_transcript_insights:
            if item not in unique_insights:
                unique_insights.append(item)
        
        return {
            'coaching_principles': unique_priorities[:8],  # Top 8 principles
            'comprehensive_recommendations': unique_recommendations[:10],  # Top 10 recommendations
            'transcript_based_insights': unique_insights[:8],  # Top 8 transcript insights
            'pattern_analysis': {
                'consistently_strong_areas': self._find_consistent_strengths(call_analyses),
                'recurring_challenges': self._find_recurring_challenges(call_analyses),
                'improvement_opportunities': self._identify_improvement_patterns(call_analyses)
            }
        }
    
    def _create_comprehensive_development_plan(self, call_analyses: List[Dict], target_employee: str) -> Dict:
        """Create comprehensive development plan based on all calls"""
        
        # Analyze performance trends
        scores = [call.get('call_metadata', {}).get('performance_score', 0) for call in call_analyses]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Determine immediate focus based on most common challenges
        all_challenges = []
        for call in call_analyses:
            challenges = call.get('performance_overview', {}).get('primary_challenges', [])
            all_challenges.extend(challenges)
        
        from collections import Counter
        top_challenges = [item for item, count in Counter(all_challenges).most_common(3)]
        
        # Create development plan
        return {
            'immediate_focus': top_challenges,
            '30_day_goals': [
                f'Improve consistency in {top_challenges[0] if top_challenges else "communication skills"}',
                f'Achieve {min(avg_score + 10, 95)}% average performance score',
                'Implement feedback from call analyses'
            ],
            '90_day_objectives': [
                f'Maintain {min(avg_score + 20, 95)}%+ performance across all call types',
                'Demonstrate mastery of identified improvement areas',
                'Mentor other team members in strong areas'
            ],
            'success_metrics': [
                'Performance score improvement',
                'Reduced number of missed opportunities',
                'Improved patient satisfaction feedback',
                'Consistent application of coaching principles'
            ],
            'training_recommendations': self._create_training_recommendations(call_analyses)
        }
    
    def _find_consistent_strengths(self, call_analyses: List[Dict]) -> List[str]:
        """Find strengths that appear consistently across multiple calls"""
        strength_counts = {}
        total_calls = len(call_analyses)
        
        for call in call_analyses:
            strengths = call.get('performance_overview', {}).get('key_strengths', [])
            for strength in strengths:
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
        
        # Return strengths that appear in at least 50% of calls
        threshold = max(1, total_calls // 2)
        consistent_strengths = [strength for strength, count in strength_counts.items() if count >= threshold]
        
        return consistent_strengths[:5]  # Top 5 consistent strengths
    
    def _find_recurring_challenges(self, call_analyses: List[Dict]) -> List[str]:
        """Find challenges that appear across multiple calls"""
        challenge_counts = {}
        total_calls = len(call_analyses)
        
        for call in call_analyses:
            challenges = call.get('performance_overview', {}).get('primary_challenges', [])
            for challenge in challenges:
                challenge_counts[challenge] = challenge_counts.get(challenge, 0) + 1
        
        # Return challenges that appear in at least 40% of calls
        threshold = max(1, total_calls * 2 // 5)
        recurring_challenges = [challenge for challenge, count in challenge_counts.items() if count >= threshold]
        
        return recurring_challenges[:5]  # Top 5 recurring challenges
    
    def _identify_improvement_patterns(self, call_analyses: List[Dict]) -> List[str]:
        """Identify patterns for improvement across all calls"""
        patterns = []
        
        # Check score patterns
        scores = [call.get('call_metadata', {}).get('performance_score', 0) for call in call_analyses]
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score < 75:
                patterns.append("Overall performance needs improvement across all call types")
            
            score_variance = max(scores) - min(scores)
            if score_variance > 20:
                patterns.append("Performance inconsistency - focus on standardizing approach")
        
        # Check call type patterns
        call_types = [call.get('call_metadata', {}).get('call_type', '') for call in call_analyses]
        type_scores = {}
        for i, call_type in enumerate(call_types):
            if call_type and i < len(scores):
                if call_type not in type_scores:
                    type_scores[call_type] = []
                type_scores[call_type].append(scores[i])
        
        # Identify weak call types
        for call_type, type_score_list in type_scores.items():
            avg_type_score = sum(type_score_list) / len(type_score_list)
            if avg_type_score < 70:
                patterns.append(f"Needs focused training on {call_type.replace('_', ' ')} calls")
        
        return patterns[:5]  # Top 5 improvement patterns
    
    def _create_training_recommendations(self, call_analyses: List[Dict]) -> List[str]:
        """Create specific training recommendations based on all call analyses"""
        recommendations = []
        
        # Collect all training focuses
        training_focuses = []
        for call in call_analyses:
            focus = call.get('training_focus', '')
            if focus:
                training_focuses.append(focus)
        
        from collections import Counter
        common_focuses = [item for item, count in Counter(training_focuses).most_common(3)]
        
        for focus in common_focuses:
            recommendations.append(f"Intensive training in {focus}")
        
        # Add general recommendations
        recommendations.extend([
            "Role-play exercises based on actual call scenarios",
            "Regular coaching sessions to reinforce learning",
            "Peer review sessions with high-performing team members"
        ])
        
        return recommendations[:6]  # Top 6 training recommendations
    
    def is_available(self) -> bool:
        """Check if coaching service is available"""
        return self.llm_analyzer and self.llm_analyzer.is_initialized