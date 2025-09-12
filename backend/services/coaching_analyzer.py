"""
Coaching Analyzer - Identify calls suitable for coaching/training reference
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CoachingAnalyzer:
    """Analyze calls to determine if they should be used for coaching/training purposes"""
    
    def __init__(self):
        # Criteria for excellent coaching calls
        self.coaching_criteria = {
            'min_representative_score': 80,  # Minimum score threshold
            'min_sentiment_confidence': 0.7,  # Minimum sentiment confidence
            'preferred_sentiments': ['positive'],  # Staff sentiment should be positive
            'avoid_missed_opportunities': True,  # Avoid calls with missed opportunities
            'min_call_duration': 30,  # Minimum call duration in seconds (if available)
            'exclude_emotions': ['anger', 'frustration'],  # Exclude calls with these emotions
            'preferred_call_types': [  # Prioritize these call types for coaching
                'new_patient',
                'appointment_booking', 
                'emergency',
                'major_treatment',
                'cosmetic'
            ]
        }
    
    def analyze_for_coaching(self, call_data: Dict) -> Dict:
        """
        Analyze a call to determine if it's suitable for coaching purposes
        
        Args:
            call_data: Dictionary containing call analysis results
            
        Returns:
            Dict with coaching analysis results
        """
        try:
            # Extract relevant data
            rep_score = call_data.get('representative_score', 0)
            staff_sentiment = call_data.get('staff_sentiment', {})
            overall_sentiment = call_data.get('overall_sentiment', {})
            missed_opportunity = call_data.get('high_value_missed_opportunity', False)
            call_tag = call_data.get('call_tag', 'general_inquiry')
            emotion_flags = call_data.get('emotion_flags', [])
            
            # Initialize coaching analysis
            coaching_analysis = {
                'is_coaching_candidate': False,
                'coaching_score': 0,
                'coaching_category': None,
                'strengths_demonstrated': [],
                'coaching_value': 'none',  # none, low, medium, high, excellent
                'usage_recommendations': [],
                'reasons_included': [],
                'reasons_excluded': []
            }
            
            # Check basic eligibility criteria
            eligibility_checks = self._check_basic_eligibility(
                rep_score, staff_sentiment, missed_opportunity, emotion_flags
            )
            
            if not eligibility_checks['eligible']:
                coaching_analysis['reasons_excluded'] = eligibility_checks['reasons']
                return coaching_analysis
            
            # Calculate coaching score
            coaching_score = self._calculate_coaching_score(call_data)
            coaching_analysis['coaching_score'] = coaching_score
            
            # Determine if this is a coaching candidate
            if coaching_score >= 75:
                coaching_analysis['is_coaching_candidate'] = True
                coaching_analysis['reasons_included'] = eligibility_checks['positive_reasons']
                
                # Determine coaching category and value
                coaching_analysis.update(self._determine_coaching_value(call_data, coaching_score))
                
                # Add usage recommendations
                coaching_analysis['usage_recommendations'] = self._generate_usage_recommendations(call_data)
                
                # Identify demonstrated strengths
                coaching_analysis['strengths_demonstrated'] = self._identify_strengths(call_data)
                
                logger.info(f"Coaching candidate identified: score={coaching_score}, category={coaching_analysis['coaching_category']}")
            else:
                coaching_analysis['reasons_excluded'].extend([
                    f"Coaching score too low: {coaching_score} (minimum 75 required)"
                ])
            
            return coaching_analysis
            
        except Exception as e:
            logger.error(f"Coaching analysis failed: {str(e)}")
            return {
                'is_coaching_candidate': False,
                'coaching_score': 0,
                'coaching_category': None,
                'strengths_demonstrated': [],
                'coaching_value': 'none',
                'usage_recommendations': [],
                'reasons_included': [],
                'reasons_excluded': ['Analysis failed due to error']
            }
    
    def _check_basic_eligibility(self, rep_score: float, staff_sentiment: Dict, 
                                missed_opportunity: bool, emotion_flags: List) -> Dict:
        """Check basic eligibility criteria for coaching"""
        
        reasons_excluded = []
        positive_reasons = []
        
        # Check representative score
        if rep_score < self.coaching_criteria['min_representative_score']:
            reasons_excluded.append(f"Representative score too low: {rep_score} (minimum {self.coaching_criteria['min_representative_score']})")
        else:
            positive_reasons.append(f"Excellent representative score: {rep_score}")
        
        # Check for missed opportunities
        if self.coaching_criteria['avoid_missed_opportunities'] and missed_opportunity:
            reasons_excluded.append("Call contains missed high-value opportunity")
        else:
            positive_reasons.append("No missed opportunities detected")
        
        # Check staff sentiment
        staff_sentiment_label = staff_sentiment.get('sentiment_label', 'unknown').lower()
        if staff_sentiment_label not in self.coaching_criteria['preferred_sentiments']:
            if staff_sentiment_label in ['negative', 'very_negative']:
                reasons_excluded.append(f"Staff sentiment is negative: {staff_sentiment_label}")
        else:
            positive_reasons.append(f"Positive staff sentiment: {staff_sentiment_label}")
        
        # Check emotion flags for problematic emotions
        problematic_emotions = [emotion for emotion in emotion_flags 
                              if any(exclude in emotion.lower() for exclude in self.coaching_criteria['exclude_emotions'])]
        if problematic_emotions:
            reasons_excluded.append(f"Contains problematic emotions: {', '.join(problematic_emotions)}")
        else:
            positive_reasons.append("No problematic emotions detected")
        
        return {
            'eligible': len(reasons_excluded) == 0,
            'reasons': reasons_excluded,
            'positive_reasons': positive_reasons
        }
    
    def _calculate_coaching_score(self, call_data: Dict) -> int:
        """Calculate overall coaching suitability score (0-100)"""
        
        score = 0
        
        # Base score from representative performance (40% weight)
        rep_score = call_data.get('representative_score', 0)
        score += (rep_score * 0.4)
        
        # Sentiment quality bonus (20% weight)
        staff_sentiment = call_data.get('staff_sentiment', {})
        staff_confidence = staff_sentiment.get('confidence', 0)
        if staff_sentiment.get('sentiment_label', '').lower() == 'positive':
            score += (staff_confidence * 20)
        
        # Call type preference bonus (15% weight)
        call_tag = call_data.get('call_tag', 'general_inquiry')
        if call_tag in self.coaching_criteria['preferred_call_types']:
            type_bonus = {
                'new_patient': 15,
                'emergency': 12,
                'major_treatment': 10,
                'appointment_booking': 8,
                'cosmetic': 8
            }
            score += type_bonus.get(call_tag, 5)
        
        # Overall sentiment bonus (10% weight)
        overall_sentiment = call_data.get('overall_sentiment', {})
        if overall_sentiment.get('sentiment_label', '').lower() == 'positive':
            score += (overall_sentiment.get('confidence', 0) * 10)
        
        # Professional communication bonus (10% weight)
        emotion_flags = call_data.get('emotion_flags', [])
        if any('professional' in flag.lower() for flag in emotion_flags):
            score += 10
        
        # Success achievement bonus (5% weight)
        if call_data.get('success_achieved', False):
            score += 5
        
        return min(100, max(0, int(score)))
    
    def _determine_coaching_value(self, call_data: Dict, coaching_score: int) -> Dict:
        """Determine the coaching value and category"""
        
        call_tag = call_data.get('call_tag', 'general_inquiry')
        rep_score = call_data.get('representative_score', 0)
        
        # Determine coaching value level
        if coaching_score >= 90 and rep_score >= 90:
            coaching_value = 'excellent'
            category = 'masterclass'
        elif coaching_score >= 85:
            coaching_value = 'high'
            category = 'advanced_training'
        elif coaching_score >= 80:
            coaching_value = 'medium'
            category = 'standard_training'
        else:
            coaching_value = 'low'
            category = 'basic_example'
        
        # Adjust category based on call type
        if call_tag in ['emergency', 'new_patient']:
            if coaching_value in ['high', 'excellent']:
                category = f'{call_tag}_excellence'
        elif call_tag in ['major_treatment', 'cosmetic']:
            if coaching_value in ['high', 'excellent']:
                category = f'sales_excellence'
        
        return {
            'coaching_value': coaching_value,
            'coaching_category': category
        }
    
    def _generate_usage_recommendations(self, call_data: Dict) -> List[str]:
        """Generate specific recommendations for how to use this call in training"""
        
        recommendations = []
        call_tag = call_data.get('call_tag', 'general_inquiry')
        rep_score = call_data.get('representative_score', 0)
        coaching_value = call_data.get('coaching_value', 'medium')
        
        # Base recommendations
        recommendations.append("Use for new representative training")
        
        if rep_score >= 90:
            recommendations.append("Excellent example of best practices")
            recommendations.append("Use in advanced coaching sessions")
        
        # Call-type specific recommendations
        if call_tag == 'new_patient':
            recommendations.extend([
                "Demonstrate new patient onboarding excellence",
                "Show proper welcome and scheduling techniques"
            ])
        elif call_tag == 'emergency':
            recommendations.extend([
                "Excellent emergency handling example",
                "Demonstrate urgency recognition and appropriate response"
            ])
        elif call_tag in ['major_treatment', 'cosmetic']:
            recommendations.extend([
                "Great sales conversation example",
                "Show consultation booking techniques"
            ])
        elif call_tag == 'appointment_booking':
            recommendations.extend([
                "Perfect scheduling call example",
                "Demonstrate efficiency and professionalism"
            ])
        
        # Quality-based recommendations
        if coaching_value == 'excellent':
            recommendations.append("Use as gold standard example")
        elif coaching_value == 'high':
            recommendations.append("Excellent training material")
        
        return recommendations
    
    def _identify_strengths(self, call_data: Dict) -> List[str]:
        """Identify specific strengths demonstrated in the call"""
        
        strengths = []
        
        # Performance-based strengths
        rep_score = call_data.get('representative_score', 0)
        if rep_score >= 90:
            strengths.append("Exceptional overall performance")
        elif rep_score >= 85:
            strengths.append("Strong overall performance")
        
        # Sentiment-based strengths
        staff_sentiment = call_data.get('staff_sentiment', {})
        if staff_sentiment.get('sentiment_label', '').lower() == 'positive':
            strengths.append("Maintained positive attitude")
        
        overall_sentiment = call_data.get('overall_sentiment', {})
        if overall_sentiment.get('sentiment_label', '').lower() == 'positive':
            strengths.append("Created positive call experience")
        
        # Emotion-based strengths
        emotion_flags = call_data.get('emotion_flags', [])
        emotion_strength_map = {
            'empathy': "Demonstrated empathy with patient",
            'professional': "Maintained professional demeanor",
            'confidence': "Showed confidence in responses",
            'patience': "Exhibited patience with patient questions"
        }
        
        for emotion in emotion_flags:
            for key, strength in emotion_strength_map.items():
                if key in emotion.lower():
                    strengths.append(strength)
        
        # Success-based strengths
        if call_data.get('success_achieved', False):
            strengths.append("Successfully achieved call objectives")
        
        if not call_data.get('high_value_missed_opportunity', False):
            strengths.append("Identified and captured all opportunities")
        
        # Call type specific strengths
        call_tag = call_data.get('call_tag', 'general_inquiry')
        if call_tag == 'emergency':
            strengths.append("Excellent emergency situation handling")
        elif call_tag == 'new_patient':
            strengths.append("Outstanding new patient welcome")
        
        return strengths
    
    def generate_coaching_report(self, calls_data: List[Dict]) -> Dict:
        """Generate a comprehensive coaching opportunities report"""
        
        coaching_candidates = []
        total_calls = len(calls_data)
        
        # Analyze each call for coaching potential
        for call in calls_data:
            coaching_analysis = self.analyze_for_coaching(call)
            if coaching_analysis['is_coaching_candidate']:
                # Add call metadata
                coaching_analysis['call_file'] = call.get('Call_File_Name', 'unknown')
                coaching_analysis['analysis_date'] = call.get('Analysis_Date', 'unknown')
                coaching_analysis['representative_name'] = call.get('Representative_Name', 'unknown')
                coaching_analysis['call_tag'] = call.get('call_tag', 'general_inquiry')
                coaching_analysis['representative_score'] = call.get('representative_score', 0)
                coaching_candidates.append(coaching_analysis)
        
        # Sort by coaching score (highest first)
        coaching_candidates.sort(key=lambda x: x['coaching_score'], reverse=True)
        
        # Generate statistics
        category_stats = {}
        value_stats = {}
        rep_stats = {}
        
        for candidate in coaching_candidates:
            # Category distribution
            category = candidate['coaching_category']
            category_stats[category] = category_stats.get(category, 0) + 1
            
            # Value distribution
            value = candidate['coaching_value']
            value_stats[value] = value_stats.get(value, 0) + 1
            
            # Representative performance
            rep_name = candidate['representative_name']
            if rep_name not in rep_stats:
                rep_stats[rep_name] = {'count': 0, 'avg_score': 0, 'scores': []}
            rep_stats[rep_name]['count'] += 1
            rep_stats[rep_name]['scores'].append(candidate['coaching_score'])
        
        # Calculate representative averages
        for rep_name in rep_stats:
            scores = rep_stats[rep_name]['scores']
            rep_stats[rep_name]['avg_score'] = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_calls_analyzed': total_calls,
            'total_coaching_candidates': len(coaching_candidates),
            'coaching_percentage': (len(coaching_candidates) / total_calls * 100) if total_calls > 0 else 0,
            'coaching_candidates': coaching_candidates,
            'category_distribution': category_stats,
            'value_distribution': value_stats,
            'representative_performance': rep_stats,
            'top_coaching_calls': coaching_candidates[:10],  # Top 10 calls
            'recommendations': self._generate_coaching_recommendations(coaching_candidates, category_stats)
        }
    
    def _generate_coaching_recommendations(self, candidates: List[Dict], category_stats: Dict) -> List[str]:
        """Generate coaching program recommendations based on available calls"""
        
        recommendations = []
        
        if not candidates:
            recommendations.append("No coaching candidates found. Review scoring criteria.")
            return recommendations
        
        # Excellence examples
        excellent_calls = [c for c in candidates if c['coaching_value'] == 'excellent']
        if excellent_calls:
            recommendations.append(f"Use {len(excellent_calls)} excellent calls as gold standard examples")
        
        # Category-specific recommendations
        if 'new_patient_excellence' in category_stats:
            recommendations.append("Create new patient onboarding training module")
        
        if 'emergency_excellence' in category_stats:
            recommendations.append("Develop emergency handling training program")
        
        if 'sales_excellence' in category_stats:
            recommendations.append("Build sales conversation masterclass")
        
        # Representative development
        high_performers = [c for c in candidates if c['representative_score'] >= 90]
        if high_performers:
            unique_reps = set(c['representative_name'] for c in high_performers)
            recommendations.append(f"Recognize {len(unique_reps)} high-performing representatives")
        
        return recommendations