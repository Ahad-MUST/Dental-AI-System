"""
Enhanced Coaching Analyzer - Advanced coaching opportunity detection
Identifies 4 types of coaching opportunities with learning potential scoring
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class CoachingType(Enum):
    """Types of coaching opportunities"""
    EXCELLENCE_EXAMPLE = "excellence_example"
    IMPROVEMENT_OPPORTUNITY = "improvement_opportunity"
    COMMON_MISTAKE = "common_mistake"
    SKILL_SPECIFIC = "skill_specific"

class LearningPotential(Enum):
    """Learning potential levels"""
    EXCELLENT = "excellent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class TargetAudience(Enum):
    """Target audience for coaching"""
    INDIVIDUAL = "individual"
    TEAM = "team"
    ALL_STAFF = "all_staff"

class EnhancedCoachingAnalyzer:
    """Advanced coaching analyzer for identifying learning opportunities"""
    
    def __init__(self):
        # Enhanced scoring thresholds for different coaching types
        self.coaching_thresholds = {
            CoachingType.EXCELLENCE_EXAMPLE: {
                'min_score': 85,
                'min_sentiment_confidence': 0.8,
                'preferred_sentiments': ['positive', 'very_positive'],
                'avoid_emotions': ['anger', 'frustration', 'confusion']
            },
            CoachingType.IMPROVEMENT_OPPORTUNITY: {
                'min_score': 50,
                'max_score': 79,
                'specific_issues_required': True,
                'avoid_emotions': ['extreme_anger']
            },
            CoachingType.COMMON_MISTAKE: {
                'min_score': 40,
                'max_score': 75,
                'pattern_detection': True,
                'recurring_issues': True
            },
            CoachingType.SKILL_SPECIFIC: {
                'min_score': 60,
                'clear_competencies': True,
                'teachable_moments': True
            }
        }
        
        # Skill areas for coaching focus
        self.skill_areas = [
            'communication_clarity',
            'empathy_building',
            'appointment_scheduling',
            'insurance_handling',
            'emergency_management',
            'treatment_explanation',
            'pricing_discussion',
            'follow_up_procedures',
            'complaint_resolution',
            'upselling_techniques',
            'active_listening',
            'professional_tone'
        ]
        
        # Common mistake patterns
        self.mistake_patterns = {
            'missed_appointment_confirmation': ['forgot to confirm', 'no confirmation', 'scheduling without confirming'],
            'insurance_confusion': ['insurance unclear', 'benefits not explained', 'coverage confusion'],
            'pricing_avoidance': ['price not mentioned', 'cost avoided', 'fee discussion missing'],
            'unprofessional_tone': ['casual language', 'inappropriate', 'unprofessional'],
            'poor_listening': ['interrupted patient', 'missed concerns', 'didn\'t address'],
            'incomplete_information': ['missing details', 'partial info', 'unclear instructions']
        }
    
    def analyze_coaching_opportunities(self, call_data: Dict) -> Dict:
        """
        Comprehensive coaching opportunity analysis
        
        Args:
            call_data: Complete call analysis results
            
        Returns:
            Dict with enhanced coaching analysis
        """
        try:
            coaching_opportunities = []
            
            # Analyze for each coaching type
            for coaching_type in CoachingType:
                opportunity = self._analyze_coaching_type(call_data, coaching_type)
                if opportunity:
                    coaching_opportunities.append(opportunity)
            
            # Select best opportunity if multiple found
            primary_opportunity = self._select_primary_opportunity(coaching_opportunities)
            
            # Generate comprehensive analysis
            analysis = {
                'has_coaching_opportunity': len(coaching_opportunities) > 0,
                'coaching_opportunities': coaching_opportunities,
                'primary_opportunity': primary_opportunity,
                'learning_potential': self._assess_learning_potential(call_data, primary_opportunity),
                'target_audience': self._determine_target_audience(call_data, primary_opportunity),
                'implementation_difficulty': self._assess_implementation_difficulty(call_data, primary_opportunity),
                'estimated_impact': self._estimate_impact(call_data, primary_opportunity),
                'coaching_focus_areas': self._identify_focus_areas(call_data, primary_opportunity),
                'opportunity_score': self._calculate_opportunity_score(call_data, primary_opportunity),
                'metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'call_score': call_data.get('representative_score', 0),
                    'call_type': call_data.get('call_tag', 'unknown'),
                    'representative': call_data.get('representative_name', 'Unknown')
                }
            }
            
            logger.info(f"Coaching analysis complete: {len(coaching_opportunities)} opportunities found")
            return analysis
            
        except Exception as e:
            logger.error(f"Enhanced coaching analysis failed: {str(e)}")
            return self._get_empty_analysis()
    
    def _analyze_coaching_type(self, call_data: Dict, coaching_type: CoachingType) -> Optional[Dict]:
        """Analyze for a specific coaching type"""
        
        rep_score = call_data.get('representative_score', 0)
        staff_sentiment = call_data.get('staff_sentiment', {})
        emotion_flags = call_data.get('emotion_flags', [])
        performance_analysis = call_data.get('performance_analysis', {})
        
        criteria = self.coaching_thresholds[coaching_type]
        
        if coaching_type == CoachingType.EXCELLENCE_EXAMPLE:
            return self._analyze_excellence_example(call_data, criteria)
        elif coaching_type == CoachingType.IMPROVEMENT_OPPORTUNITY:
            return self._analyze_improvement_opportunity(call_data, criteria)
        elif coaching_type == CoachingType.COMMON_MISTAKE:
            return self._analyze_common_mistake(call_data, criteria)
        elif coaching_type == CoachingType.SKILL_SPECIFIC:
            return self._analyze_skill_specific(call_data, criteria)
        
        return None
    
    def _analyze_excellence_example(self, call_data: Dict, criteria: Dict) -> Optional[Dict]:
        """Analyze for excellence examples (high scores for best practice demonstrations)"""
        
        rep_score = call_data.get('representative_score', 0)
        staff_sentiment = call_data.get('staff_sentiment', {})
        emotion_flags = call_data.get('emotion_flags', [])
        
        # Check if meets excellence criteria
        if rep_score < criteria['min_score']:
            return None
        
        staff_sentiment_label = staff_sentiment.get('sentiment_label', '').lower()
        if staff_sentiment_label not in criteria['preferred_sentiments']:
            return None
        
        # Check for problematic emotions
        if any(emotion in emotion_flags for emotion in criteria['avoid_emotions']):
            return None
        
        return {
            'type': CoachingType.EXCELLENCE_EXAMPLE.value,
            'score': rep_score,
            'description': f"Excellent call performance (score: {rep_score}) demonstrating best practices",
            'strengths': self._extract_call_strengths(call_data),
            'use_case': 'best_practice_demonstration',
            'confidence': staff_sentiment.get('confidence', 0.8)
        }
    
    def _analyze_improvement_opportunity(self, call_data: Dict, criteria: Dict) -> Optional[Dict]:
        """Analyze for improvement opportunities (scores with specific issues)"""
        
        rep_score = call_data.get('representative_score', 0)
        performance_analysis = call_data.get('performance_analysis', {})
        
        # Check score range
        if not (criteria['min_score'] <= rep_score <= criteria['max_score']):
            return None
        
        # Look for specific improvement areas
        improvement_areas = self._identify_improvement_areas(call_data)
        if not improvement_areas:
            return None
        
        return {
            'type': CoachingType.IMPROVEMENT_OPPORTUNITY.value,
            'score': rep_score,
            'description': f"Clear improvement opportunity (score: {rep_score}) with specific actionable areas",
            'improvement_areas': improvement_areas,
            'use_case': 'before_after_training',
            'potential_score_increase': self._estimate_score_improvement(improvement_areas)
        }
    
    def _analyze_common_mistake(self, call_data: Dict, criteria: Dict) -> Optional[Dict]:
        """Analyze for common mistakes (recurring patterns for team-wide training)"""
        
        rep_score = call_data.get('representative_score', 0)
        performance_analysis = call_data.get('performance_analysis', {})
        
        # Check score range
        if not (criteria['min_score'] <= rep_score <= criteria['max_score']):
            return None
        
        # Detect mistake patterns
        detected_patterns = self._detect_mistake_patterns(call_data)
        if not detected_patterns:
            return None
        
        return {
            'type': CoachingType.COMMON_MISTAKE.value,
            'score': rep_score,
            'description': f"Common mistake patterns detected for team-wide training",
            'mistake_patterns': detected_patterns,
            'use_case': 'team_wide_training',
            'frequency_indicator': self._assess_pattern_frequency(detected_patterns)
        }
    
    def _analyze_skill_specific(self, call_data: Dict, criteria: Dict) -> Optional[Dict]:
        """Analyze for skill-specific training (clear competencies for role training)"""
        
        rep_score = call_data.get('representative_score', 0)
        call_tag = call_data.get('call_tag', 'general_inquiry')
        
        if rep_score < criteria['min_score']:
            return None
        
        # Identify demonstrated skills
        demonstrated_skills = self._identify_demonstrated_skills(call_data)
        if not demonstrated_skills:
            return None
        
        return {
            'type': CoachingType.SKILL_SPECIFIC.value,
            'score': rep_score,
            'description': f"Clear skill demonstration in {call_tag} call",
            'demonstrated_skills': demonstrated_skills,
            'use_case': 'role_specific_training',
            'skill_level': self._assess_skill_level(demonstrated_skills, rep_score)
        }
    
    def _select_primary_opportunity(self, opportunities: List[Dict]) -> Optional[Dict]:
        """Select the best coaching opportunity from multiple candidates"""
        
        if not opportunities:
            return None
        
        # Priority order: Excellence > Skill-specific > Improvement > Common mistakes
        priority_order = [
            CoachingType.EXCELLENCE_EXAMPLE.value,
            CoachingType.SKILL_SPECIFIC.value,
            CoachingType.IMPROVEMENT_OPPORTUNITY.value,
            CoachingType.COMMON_MISTAKE.value
        ]
        
        for priority_type in priority_order:
            for opp in opportunities:
                if opp['type'] == priority_type:
                    return opp
        
        # Fallback to highest score
        return max(opportunities, key=lambda x: x.get('score', 0))
    
    def _assess_learning_potential(self, call_data: Dict, opportunity: Optional[Dict]) -> str:
        """Assess the learning potential of the coaching opportunity"""
        
        if not opportunity:
            return LearningPotential.NONE.value
        
        rep_score = call_data.get('representative_score', 0)
        opportunity_type = opportunity.get('type')
        
        if opportunity_type == CoachingType.EXCELLENCE_EXAMPLE.value and rep_score >= 90:
            return LearningPotential.EXCELLENT.value
        elif opportunity_type == CoachingType.SKILL_SPECIFIC.value and rep_score >= 80:
            return LearningPotential.HIGH.value
        elif opportunity_type == CoachingType.IMPROVEMENT_OPPORTUNITY.value:
            improvement_areas = opportunity.get('improvement_areas', [])
            if len(improvement_areas) >= 2:
                return LearningPotential.HIGH.value
            else:
                return LearningPotential.MEDIUM.value
        elif opportunity_type == CoachingType.COMMON_MISTAKE.value:
            return LearningPotential.MEDIUM.value
        
        return LearningPotential.LOW.value
    
    def _determine_target_audience(self, call_data: Dict, opportunity: Optional[Dict]) -> str:
        """Determine the target audience for the coaching material"""
        
        if not opportunity:
            return TargetAudience.INDIVIDUAL.value
        
        opportunity_type = opportunity.get('type')
        rep_score = call_data.get('representative_score', 0)
        
        if opportunity_type == CoachingType.EXCELLENCE_EXAMPLE.value:
            return TargetAudience.ALL_STAFF.value
        elif opportunity_type == CoachingType.COMMON_MISTAKE.value:
            return TargetAudience.TEAM.value
        elif opportunity_type == CoachingType.SKILL_SPECIFIC.value:
            return TargetAudience.TEAM.value
        else:
            return TargetAudience.INDIVIDUAL.value
    
    def _assess_implementation_difficulty(self, call_data: Dict, opportunity: Optional[Dict]) -> str:
        """Assess how difficult it would be to implement this coaching"""
        
        if not opportunity:
            return "none"
        
        opportunity_type = opportunity.get('type')
        
        if opportunity_type == CoachingType.EXCELLENCE_EXAMPLE.value:
            return "easy"
        elif opportunity_type == CoachingType.SKILL_SPECIFIC.value:
            return "medium"
        elif opportunity_type == CoachingType.IMPROVEMENT_OPPORTUNITY.value:
            improvement_areas = opportunity.get('improvement_areas', [])
            return "medium" if len(improvement_areas) <= 2 else "difficult"
        elif opportunity_type == CoachingType.COMMON_MISTAKE.value:
            return "difficult"
        
        return "medium"
    
    def _estimate_impact(self, call_data: Dict, opportunity: Optional[Dict]) -> str:
        """Estimate the potential impact of this coaching"""
        
        if not opportunity:
            return "none"
        
        opportunity_type = opportunity.get('type')
        rep_score = call_data.get('representative_score', 0)
        
        if opportunity_type == CoachingType.EXCELLENCE_EXAMPLE.value and rep_score >= 90:
            return "high"
        elif opportunity_type == CoachingType.COMMON_MISTAKE.value:
            return "high"
        elif opportunity_type == CoachingType.IMPROVEMENT_OPPORTUNITY.value:
            potential_increase = opportunity.get('potential_score_increase', 0)
            return "high" if potential_increase >= 15 else "medium"
        elif opportunity_type == CoachingType.SKILL_SPECIFIC.value:
            return "medium"
        
        return "low"
    
    def _identify_focus_areas(self, call_data: Dict, opportunity: Optional[Dict]) -> List[str]:
        """Identify the top 2-3 specific skills to improve"""
        
        if not opportunity:
            return []
        
        focus_areas = []
        opportunity_type = opportunity.get('type')
        performance_analysis = call_data.get('performance_analysis', {})
        call_tag = call_data.get('call_tag', 'general_inquiry')
        
        if opportunity_type == CoachingType.EXCELLENCE_EXAMPLE.value:
            # Focus on what they did well
            if call_tag in ['appointment_booking', 'appointment_confirm']:
                focus_areas = ['appointment_scheduling', 'communication_clarity']
            elif call_tag == 'emergency':
                focus_areas = ['emergency_management', 'empathy_building']
            elif call_tag == 'insurance':
                focus_areas = ['insurance_handling', 'professional_tone']
            else:
                focus_areas = ['communication_clarity', 'professional_tone']
        
        elif opportunity_type == CoachingType.IMPROVEMENT_OPPORTUNITY.value:
            improvement_areas = opportunity.get('improvement_areas', [])
            focus_areas = improvement_areas[:3]  # Top 3
        
        elif opportunity_type == CoachingType.COMMON_MISTAKE.value:
            mistake_patterns = opportunity.get('mistake_patterns', [])
            focus_areas = list(mistake_patterns.keys())[:3]
        
        elif opportunity_type == CoachingType.SKILL_SPECIFIC.value:
            demonstrated_skills = opportunity.get('demonstrated_skills', [])
            focus_areas = demonstrated_skills[:3]
        
        return focus_areas[:3]  # Ensure max 3 areas
    
    def _calculate_opportunity_score(self, call_data: Dict, opportunity: Optional[Dict]) -> int:
        """Calculate overall opportunity score (0-100)"""
        
        if not opportunity:
            return 0
        
        base_score = call_data.get('representative_score', 0)
        opportunity_type = opportunity.get('type')
        
        # Boost score based on coaching type value
        boost = 0
        if opportunity_type == CoachingType.EXCELLENCE_EXAMPLE.value:
            boost = 15
        elif opportunity_type == CoachingType.SKILL_SPECIFIC.value:
            boost = 10
        elif opportunity_type == CoachingType.IMPROVEMENT_OPPORTUNITY.value:
            boost = 8
        elif opportunity_type == CoachingType.COMMON_MISTAKE.value:
            boost = 5
        
        # Cap at 100
        return min(100, int(base_score + boost))
    
    def _extract_call_strengths(self, call_data: Dict) -> List[str]:
        """Extract specific strengths from the call"""
        performance_analysis = call_data.get('performance_analysis', {})
        strengths = performance_analysis.get('strengths', [])
        return strengths if isinstance(strengths, list) else [strengths] if strengths else []
    
    def _identify_improvement_areas(self, call_data: Dict) -> List[str]:
        """Identify specific areas for improvement"""
        performance_analysis = call_data.get('performance_analysis', {})
        weaknesses = performance_analysis.get('weaknesses', [])
        coaching_focus = performance_analysis.get('coaching_focus', [])
        
        areas = []
        if isinstance(weaknesses, list):
            areas.extend(weaknesses)
        elif weaknesses:
            areas.append(weaknesses)
        
        if isinstance(coaching_focus, list):
            areas.extend(coaching_focus)
        elif coaching_focus:
            areas.append(coaching_focus)
        
        return list(set(areas))  # Remove duplicates
    
    def _detect_mistake_patterns(self, call_data: Dict) -> Dict[str, List[str]]:
        """Detect common mistake patterns in the call"""
        detected = {}
        combined_transcript = call_data.get('combined_transcript', {})
        staff_text = combined_transcript.get('staff_text', '').lower()
        
        for pattern_name, indicators in self.mistake_patterns.items():
            for indicator in indicators:
                if indicator.lower() in staff_text:
                    if pattern_name not in detected:
                        detected[pattern_name] = []
                    detected[pattern_name].append(indicator)
        
        return detected
    
    def _identify_demonstrated_skills(self, call_data: Dict) -> List[str]:
        """Identify skills clearly demonstrated in the call"""
        demonstrated = []
        call_tag = call_data.get('call_tag', 'general_inquiry')
        rep_score = call_data.get('representative_score', 0)
        
        # Map call types to relevant skills
        if call_tag in ['appointment_booking', 'appointment_confirm']:
            demonstrated.append('appointment_scheduling')
        if call_tag == 'emergency':
            demonstrated.append('emergency_management')
        if call_tag == 'insurance':
            demonstrated.append('insurance_handling')
        if rep_score >= 80:
            demonstrated.extend(['communication_clarity', 'professional_tone'])
        
        return demonstrated
    
    def _estimate_score_improvement(self, improvement_areas: List[str]) -> int:
        """Estimate potential score improvement from addressing areas"""
        if not improvement_areas:
            return 0
        
        # Estimate 5-10 points per major improvement area
        return min(25, len(improvement_areas) * 8)
    
    def _assess_pattern_frequency(self, patterns: Dict) -> str:
        """Assess how frequently these patterns occur"""
        total_indicators = sum(len(indicators) for indicators in patterns.values())
        
        if total_indicators >= 3:
            return "high"
        elif total_indicators >= 2:
            return "medium"
        else:
            return "low"
    
    def _assess_skill_level(self, skills: List[str], score: int) -> str:
        """Assess the skill level demonstrated"""
        if score >= 85:
            return "advanced"
        elif score >= 75:
            return "intermediate"
        else:
            return "basic"
    
    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'has_coaching_opportunity': False,
            'coaching_opportunities': [],
            'primary_opportunity': None,
            'learning_potential': LearningPotential.NONE.value,
            'target_audience': TargetAudience.INDIVIDUAL.value,
            'implementation_difficulty': 'none',
            'estimated_impact': 'none',
            'coaching_focus_areas': [],
            'opportunity_score': 0,
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'call_score': 0,
                'call_type': 'unknown',
                'representative': 'Unknown'
            }
        }