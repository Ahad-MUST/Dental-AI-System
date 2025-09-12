"""
Call Tagging Service - SIMPLIFIED with predefined categories only
"""
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

class CallTaggingService:
    """Service to automatically tag calls with predefined dental categories only"""
    
    def __init__(self, llm_analyzer=None):
        self.llm_analyzer = llm_analyzer
        
        # PREDEFINED CATEGORIES ONLY - No new categories created
        self.predefined_categories = {
            'new_patient': {
                'keywords': ['new patient', 'first time', 'never been', 'looking for dentist', 'need dentist', 'new to area'],
                'patterns': [r'i.{0,10}new.{0,10}patient', r'first.{0,10}time.{0,10}here', r'never.{0,10}been'],
                'priority': 90
            },
            'emergency': {
                'keywords': ['emergency', 'urgent', 'pain', 'toothache', 'tooth hurt', 'severe pain', 'broken tooth', 'swelling', 'bleeding', 'knocked out'],
                'patterns': [r'tooth.{0,10}hurt', r'in.{0,10}pain', r'really.{0,10}hurt', r'severe.{0,10}pain'],
                'priority': 100
            },
            'insurance': {
                'keywords': ['insurance', 'coverage', 'benefits', 'network', 'accept', 'medicaid', 'ppo', 'delta dental', 'aetna', 'cigna', 'verification'],
                'patterns': [r'take.{0,10}insurance', r'accept.{0,10}medicaid', r'in.{0,10}network'],
                'priority': 70
            },
            'appointment_booking': {
                'keywords': ['schedule', 'appointment', 'book', 'available', 'when can', 'time slot', 'open'],
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
        
        # LLM-based tagging prompt for predefined categories only
        self.tagging_prompt = """
Analyze this dental office call and choose ONE category from the predefined list.

PATIENT: {patient_text}
STAFF: {staff_text}

PREDEFINED CATEGORIES (choose ONLY from these):
1. new_patient - First-time patients or people looking for a new dentist
2. emergency - Urgent dental issues, pain, broken teeth, swelling
3. insurance - Insurance verification, coverage questions, benefit inquiries
4. appointment_booking - Scheduling new appointments
5. appointment_confirm - Confirming existing appointments
6. appointment_cancel - Canceling or rescheduling appointments
7. general_inquiry - General questions about hours, location, services, pricing
8. cleaning - Routine cleanings, checkups, preventive care
9. cosmetic - Whitening, braces, veneers, smile makeovers
10. major_treatment - Implants, crowns, root canals, oral surgery
11. billing - Payment questions, billing issues, account inquiries

Choose the BEST MATCH from these 11 categories. If none fit perfectly, choose "general_inquiry".

Respond with ONLY the category name (e.g., "emergency" or "billing").

Category:"""
    
    async def analyze_and_tag_call(self, patient_text: str, staff_text: str, call_summary: str = "") -> Dict:
        """
        Analyze call content and assign appropriate tag from predefined categories ONLY
        
        Returns:
            Dict with primary_tag from predefined categories
        """
        try:
            # Combine all text for analysis
            combined_text = f"{patient_text} {staff_text} {call_summary}".lower()
            
            # First, try rule-based tagging with predefined categories
            rule_based_result = self._rule_based_tagging(combined_text)
            
            # If rule-based gives high confidence, use it
            if rule_based_result['confidence_score'] >= 0.7:
                logger.info(f"Rule-based tag: {rule_based_result['primary_tag']}")
                return rule_based_result
            
            # Otherwise, use LLM for better accuracy (still limited to predefined categories)
            if self.llm_analyzer and self.llm_analyzer.is_initialized:
                llm_result = await self._llm_based_tagging(patient_text, staff_text)
                if llm_result['primary_tag'] in self.predefined_categories:
                    logger.info(f"LLM-based tag: {llm_result['primary_tag']}")
                    return llm_result
            
            # Fallback to rule-based result
            logger.info(f"Fallback to rule-based tag: {rule_based_result['primary_tag']}")
            return rule_based_result
            
        except Exception as e:
            logger.error(f"Call tagging failed: {str(e)}")
            return {
                'primary_tag': 'general_inquiry',
                'confidence_score': 0.5,
                'reasoning': 'Tagging analysis failed, defaulted to general inquiry'
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
    
    async def _llm_based_tagging(self, patient_text: str, staff_text: str) -> Dict:
        """LLM-based tagging limited to predefined categories only"""
        
        try:
            prompt = self.tagging_prompt.format(
                patient_text=patient_text[:1500],  # Limit context length
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
            'emergency': 'Emergency',
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