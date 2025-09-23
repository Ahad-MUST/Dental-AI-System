"""
Coaching Library API Routes - Complete Fixed Implementation
Handles all API interactions for the coaching library system
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from services.llm_analyzer import LLMAnalyzer
    from services.data_loader import DataLoader
except ImportError as e:
    print(f"Warning: Could not import services: {e}")
    LLMAnalyzer = None
    DataLoader = None

logger = logging.getLogger(__name__)

# Create router
coaching_router = APIRouter(prefix="/api/coaching", tags=["coaching"])

# Pydantic models
class CallFilterRequest(BaseModel):
    employee: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    call_type: Optional[str] = None
    sentiment: Optional[str] = None
    min_score: Optional[float] = 0
    max_score: Optional[float] = 100
    search_term: Optional[str] = None

class CaseStudyRequest(BaseModel):
    calls: List[Dict[str, Any]]
    analysis_type: str  # 'individual' or 'comparative'
    target_employee: str
    title: str

class PDFGenerationRequest(BaseModel):
    case_study_data: Dict[str, Any]
    title: str
    target_employee: str
    analysis_type: str
    format: str = "pdf"

class CoachingSessionRequest(BaseModel):
    employee_name: str
    call_ids: List[str]
    session_notes: str
    action_items: List[str]

# Dependency to get data loader
def get_data_loader():
    """Get data loader instance"""
    if DataLoader:
        return DataLoader()
    else:
        raise HTTPException(status_code=500, detail="DataLoader not available")

# Dependency to get coaching service
def get_coaching_service():
    """Get coaching service instance"""
    try:
        if LLMAnalyzer:
            from services.coaching_service import CoachingService
            llm_analyzer = LLMAnalyzer()
            return CoachingService(llm_analyzer)
        else:
            raise HTTPException(status_code=500, detail="LLM Analyzer not available")
    except ImportError:
        raise HTTPException(status_code=500, detail="Coaching service not available")


def _generate_unique_call_id(call_data: Dict, existing_ids: set = None) -> str:
    """
    Generate a truly unique ID for the call
    """
    if existing_ids is None:
        existing_ids = set()
    
    # Try Call_File_Name first, then audio_file
    audio_file = call_data.get('Call_File_Name') or call_data.get('audio_file', '')
    if audio_file:
        from pathlib import Path
        base_id = Path(audio_file).stem
        if base_id not in existing_ids:
            return base_id
    
    # Try source file
    source_file = call_data.get('source_file', '')
    if source_file:
        from pathlib import Path
        base_id = Path(source_file).stem
        if base_id not in existing_ids:
            return base_id
    
    # Generate based on multiple data points for uniqueness
    rep_name = call_data.get('Representative_Name', call_data.get('representative_name', 'unknown'))
    date_str = call_data.get('Analysis_Date', call_data.get('analysis_date', ''))
    
    # Extract more unique identifiers
    call_summary = call_data.get('Call_Summary', call_data.get('call_summary', ''))
    patient_transcript = call_data.get('Patient_Transcript', call_data.get('patient_transcript', ''))
    
    # Create a more unique hash from multiple fields
    unique_string = f"{rep_name}_{date_str}_{call_summary[:50]}_{patient_transcript[:50]}"
    unique_hash = hash(unique_string) % 1000000  # 6 digit hash
    
    base_id = f"{rep_name}_{date_str[:10]}_{unique_hash}"
    
    # Ensure absolute uniqueness
    counter = 1
    final_id = base_id
    while final_id in existing_ids:
        final_id = f"{base_id}_{counter}"
        counter += 1
    
    return final_id

# Update the _map_call_data_to_coaching_format function
def _map_call_data_to_coaching_format(call_data: Dict, existing_ids: set = None) -> Dict:
    """
    Map various call data formats to the coaching format expected by frontend
    This handles both Analysis_Date and analysis_date formats, scores, etc.
    """
    if existing_ids is None:
        existing_ids = set()
    
    # Create a standardized call object
    coaching_call = {}
    
    # Try different field name variations and map to consistent format
    field_mappings = {
        'representative_name': ['Representative_Name', 'representative_name', 'employee_name'],
        'analysis_date': ['Analysis_Date', 'analysis_date', 'date'],
        'call_summary': ['Call_Summary', 'call_summary', 'summary'],
        'patient_transcript': ['Full_Transcript_With_Timestamps', 'Patient_Transcript', 'patient_transcript', 'patient_text'],
        'staff_transcript': ['Full_Transcript_With_Timestamps', 'Staff_Transcript', 'staff_transcript', 'staff_text'],
        'representative_score': ['Representative_Score', 'representative_score', 'performance_score'],
        'overall_sentiment': ['Overall_Sentiment', 'overall_sentiment', 'sentiment', 'Patient_Sentiment'],
        'call_tag': ['Call_Tag', 'call_tag', 'call_type', 'type'],
        'call_duration': ['call_duration', 'duration', 'Call_Duration'],
        'high_value_missed_opportunity': ['High_Value_Missed_Opportunity', 'high_value_missed_opportunity', 'missed_opportunity'],
        'patient_sentiment': ['Patient_Sentiment', 'patient_sentiment'],
        'staff_sentiment': ['Staff_Sentiment', 'staff_sentiment'],
        'sentiment_confidence': ['Sentiment_Confidence', 'sentiment_confidence'],
        'patient_emotion': ['Patient_Primary_Emotion', 'patient_emotion', 'patient_primary_emotion'],
    }
    
    # Apply field mappings
    for target_field, source_fields in field_mappings.items():
        value = None
        for source_field in source_fields:
            if source_field in call_data and call_data[source_field] is not None:
                value = call_data[source_field]
                break
        
        # Set the value with appropriate type conversion
        if target_field == 'representative_score':
            try:
                coaching_call[target_field] = float(value) if value is not None else 0.0
                # Convert 0-1 scale to 0-100 scale if needed
                if coaching_call[target_field] <= 1.0 and coaching_call[target_field] > 0:
                    coaching_call[target_field] *= 100
            except (ValueError, TypeError):
                coaching_call[target_field] = 0.0
        elif target_field == 'high_value_missed_opportunity':
            if isinstance(value, str):
                coaching_call[target_field] = value.lower() in ['true', 'yes', '1', 'y']
            else:
                coaching_call[target_field] = bool(value) if value is not None else False
        elif target_field == 'analysis_date':
            # Handle different date formats and ensure ISO format output
            if value:
                try:
                    # If it's already in ISO format, keep it
                    if isinstance(value, str) and 'T' in value:
                        coaching_call[target_field] = value
                    # If it's MM/DD/YYYY format, convert to ISO
                    elif isinstance(value, str) and '/' in value:
                        try:
                            date_obj = datetime.strptime(value, '%m/%d/%Y')
                            coaching_call[target_field] = date_obj.isoformat()
                        except ValueError:
                            # Try other date formats
                            try:
                                date_obj = datetime.strptime(value, '%Y-%m-%d')
                                coaching_call[target_field] = date_obj.isoformat()
                            except ValueError:
                                coaching_call[target_field] = datetime.now().isoformat()
                    else:
                        coaching_call[target_field] = str(value)
                except:
                    coaching_call[target_field] = datetime.now().isoformat()
            else:
                coaching_call[target_field] = datetime.now().isoformat()
        else:
            coaching_call[target_field] = str(value) if value is not None else ''
    
    # Generate unique ID
    unique_id = _generate_unique_call_id(call_data, existing_ids)
    coaching_call['id'] = unique_id
    existing_ids.add(unique_id)
    
    # Extract complex analysis data if available - KEEP EXISTING LOGIC
    coaching_call['performance_analysis'] = call_data.get('performance_analysis', {})
    coaching_call['sentiment_analysis'] = call_data.get('sentiment_analysis', {})
    coaching_call['opportunity_analysis'] = call_data.get('opportunity_analysis', {})
    coaching_call['coaching_analysis'] = call_data.get('coaching_analysis', {})
    
    # Set defaults for missing required fields
    coaching_call.setdefault('representative_name', 'Unknown')
    coaching_call.setdefault('call_summary', 'No summary available')
    coaching_call.setdefault('overall_sentiment', 'neutral')
    coaching_call.setdefault('call_tag', 'general_inquiry')
    coaching_call.setdefault('patient_transcript', '')
    coaching_call.setdefault('staff_transcript', '')
    coaching_call.setdefault('high_value_missed_opportunity', False)
    coaching_call.setdefault('call_duration', 0)
    
    return coaching_call

# Update the get_coaching_calls function to use the new ID generation
@coaching_router.get("/calls")
async def get_coaching_calls(
    employee: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    call_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_score: Optional[float] = 0,
    max_score: Optional[float] = 100,
    search_term: Optional[str] = None,
):
    """
    Get filtered calls available for coaching analysis
    """
    try:
        # Create data loader instance
        data_loader = get_data_loader()
        
        # Load all call data
        all_calls = await data_loader.load_all_calls()
        
        if not all_calls:
            logger.warning("No calls found from data loader")
            return []
        
        logger.info(f"Loaded {len(all_calls)} calls from data loader")
        
        # Convert all calls to coaching format with unique IDs
        coaching_calls = []
        existing_ids = set()
        
        for call in all_calls:
            try:
                coaching_call = _map_call_data_to_coaching_format(call, existing_ids)
                coaching_calls.append(coaching_call)
            except Exception as e:
                logger.warning(f"Failed to map call data: {str(e)}")
                continue
        
        logger.info(f"Mapped {len(coaching_calls)} calls to coaching format with unique IDs")
        
        # Apply filters
        filtered_calls = []
        
        for call in coaching_calls:
            # Employee filter
            if employee and call.get('representative_name') != employee:
                continue
            
            # Date filters
            if start_date:
                try:
                    call_date = datetime.fromisoformat(call.get('analysis_date', ''))
                    if call_date.date() < datetime.fromisoformat(start_date).date():
                        continue
                except:
                    continue
            
            if end_date:
                try:
                    call_date = datetime.fromisoformat(call.get('analysis_date', ''))
                    if call_date.date() > datetime.fromisoformat(end_date).date():
                        continue
                except:
                    continue
            
            # Call type filter
            if call_type and call.get('call_tag') != call_type:
                continue
            
            # Sentiment filter
            if sentiment and call.get('overall_sentiment') != sentiment:
                continue
            
            # Score range filter
            score = call.get('representative_score', 0)
            if score < min_score or score > max_score:
                continue
            
            # Search term filter
            if search_term:
                search_lower = search_term.lower()
                searchable_text = ' '.join([
                    call.get('call_summary', ''),
                    call.get('patient_transcript', ''),
                    call.get('staff_transcript', ''),
                    call.get('representative_name', '')
                ]).lower()
                
                if search_lower not in searchable_text:
                    continue
            
            filtered_calls.append(call)
        
        # Sort by analysis date (newest first)
        filtered_calls.sort(key=lambda x: x.get('analysis_date', ''), reverse=True)
        
        logger.info(f"Retrieved {len(filtered_calls)} filtered calls for coaching library")
        return filtered_calls
        
    except Exception as e:
        logger.error(f"Error retrieving coaching calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve calls: {str(e)}")


@coaching_router.get("/calls")
async def get_coaching_calls(
    employee: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    call_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_score: Optional[float] = 0,
    max_score: Optional[float] = 100,
    search_term: Optional[str] = None,
):
    """
    Get filtered calls available for coaching analysis
    """
    try:
        # Create data loader instance
        data_loader = get_data_loader()
        
        # Load all call data
        all_calls = await data_loader.load_all_calls()
        
        if not all_calls:
            logger.warning("No calls found from data loader")
            return []
        
        logger.info(f"Loaded {len(all_calls)} calls from data loader")
        
        # Convert all calls to coaching format
        coaching_calls = []
        for call in all_calls:
            try:
                coaching_call = _map_call_data_to_coaching_format(call)
                coaching_calls.append(coaching_call)
            except Exception as e:
                logger.warning(f"Failed to map call data: {str(e)}")
                continue
        
        logger.info(f"Mapped {len(coaching_calls)} calls to coaching format")
        
        # Apply filters
        filtered_calls = []
        
        for call in coaching_calls:
            # Employee filter
            if employee and call.get('representative_name') != employee:
                continue
            
            # Date filters
            if start_date:
                try:
                    call_date = datetime.fromisoformat(call.get('analysis_date', ''))
                    if call_date.date() < datetime.fromisoformat(start_date).date():
                        continue
                except:
                    continue
            
            if end_date:
                try:
                    call_date = datetime.fromisoformat(call.get('analysis_date', ''))
                    if call_date.date() > datetime.fromisoformat(end_date).date():
                        continue
                except:
                    continue
            
            # Call type filter
            if call_type and call.get('call_tag') != call_type:
                continue
            
            # Sentiment filter
            if sentiment and call.get('overall_sentiment') != sentiment:
                continue
            
            # Score range filter
            score = call.get('representative_score', 0)
            if score < min_score or score > max_score:
                continue
            
            # Search term filter
            if search_term:
                search_lower = search_term.lower()
                searchable_text = ' '.join([
                    call.get('call_summary', ''),
                    call.get('patient_transcript', ''),
                    call.get('staff_transcript', ''),
                    call.get('representative_name', '')
                ]).lower()
                
                if search_lower not in searchable_text:
                    continue
            
            filtered_calls.append(call)
        
        # Sort by analysis date (newest first)
        filtered_calls.sort(key=lambda x: x.get('analysis_date', ''), reverse=True)
        
        logger.info(f"Retrieved {len(filtered_calls)} filtered calls for coaching library")
        return filtered_calls
        
    except Exception as e:
        logger.error(f"Error retrieving coaching calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve calls: {str(e)}")

@coaching_router.get("/call-types")
async def get_call_types():
    """
    Get list of available call types for filtering
    """
    try:
        data_loader = get_data_loader()
        all_calls = await data_loader.load_all_calls()
        call_types = set()
        
        for call in all_calls:
            # Try different field names for call type
            call_type = (call.get('Call_Tag') or 
                        call.get('call_tag') or 
                        call.get('call_type') or
                        call.get('type'))
            if call_type and call_type.strip():
                call_types.add(call_type.strip())
        
        # Remove empty strings and sort
        call_types = sorted([ct for ct in call_types if ct])
        
        if not call_types:
            # Return default call types if none found
            call_types = [
                "appointment_booking",
                "treatment_followup", 
                "billing_inquiry",
                "general_inquiry",
                "complaint_handling",
                "treatment_consultation",
                "emergency",
                "cosmetic",
                "major_treatment"
            ]
        
        return {
            "call_types": call_types
        }
        
    except Exception as e:
        logger.error(f"Error retrieving call types: {str(e)}")
        # Return default call types
        return {
            "call_types": [
                "appointment_booking",
                "treatment_followup", 
                "billing_inquiry",
                "general_inquiry",
                "complaint_handling",
                "treatment_consultation",
                "emergency",
                "cosmetic",
                "major_treatment"
            ]
        }

@coaching_router.get("/test")
async def test_coaching_endpoints():
    """
    Test endpoint to verify coaching system is working
    """
    try:
        data_loader = get_data_loader()
        calls = await data_loader.load_all_calls()
        
        # Map first call to coaching format if available
        sample_call = None
        sample_call_keys = []
        if calls:
            sample_call = _map_call_data_to_coaching_format(calls[0])
            sample_call_keys = list(calls[0].keys())
        
        return {
            "status": "success",
            "message": "Coaching endpoints are working",
            "data_loader_working": True,
            "calls_found": len(calls),
            "sample_call_keys": sample_call_keys,
            "sample_coaching_call": sample_call,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Coaching test failed: {str(e)}")
        return {
            "status": "error",
            "message": "Coaching endpoints have issues",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@coaching_router.post("/generate-case-study")
async def generate_case_study(request: CaseStudyRequest):
    """
    Generate a coaching case study from selected calls
    """
    try:
        if not request.calls:
            raise HTTPException(status_code=400, detail="No calls provided for analysis")
        
        if len(request.calls) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 calls allowed for analysis")
        
        # Validate analysis type
        if request.analysis_type not in ['individual', 'comparative']:
            raise HTTPException(status_code=400, detail="Analysis type must be 'individual' or 'comparative'")
        
        # Generate case study based on real call data
        case_study = {
            "title": request.title,
            "analysis_type": request.analysis_type,
            "target_employee": request.target_employee,
            "calls_analyzed": len(request.calls),
            "generated_at": datetime.now().isoformat(),
            "status": "generated",
            "message": "Case study generated successfully",
            "conversation_examples": _generate_conversation_examples(request.calls),
            "key_principles": [
                "Build rapport first: Always open with a warm greeting and personal connection",
                "Explain the 'why': Patients need to understand why treatment matters now",
                "Handle objections: Acknowledge concerns, then reframe with benefits",
                "Give two choices: Offer two appointment times, not a yes/no question",
                "Address money early: Mention financing so cost isn't a hidden barrier",
                "Never end at a dead stop: If no booking, set a specific follow-up plan"
            ],
            "follow_up_flow": {
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
            },
            "performance_analysis": _analyze_call_performance(request.calls),
            "improvement_recommendations": _generate_improvement_recommendations(request.calls)
        }
        
        logger.info(f"Generated case study: {request.title}")
        return case_study
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Case study generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate case study: {str(e)}")

def _generate_conversation_examples(calls: List[Dict]) -> List[Dict]:
    """Generate conversation examples from actual call data"""
    examples = []
    
    for call in calls[:3]:  # Use up to 3 calls for examples
        patient_text = call.get('patient_transcript', '')
        staff_text = call.get('staff_transcript', '')
        
        if patient_text and staff_text:
            # Extract first meaningful exchange
            patient_lines = [line.strip() for line in patient_text.split('\n') if line.strip()]
            staff_lines = [line.strip() for line in staff_text.split('\n') if line.strip()]
            
            if patient_lines and staff_lines:
                example = {
                    "what_was_said": staff_lines[0][:100] + "..." if len(staff_lines[0]) > 100 else staff_lines[0],
                    "what_to_say_instead": _improve_staff_response(staff_lines[0], patient_lines[0]),
                    "coaching_point": _get_coaching_point(call),
                    "impact": "Improved patient experience and higher booking rate"
                }
                examples.append(example)
    
    # Add default examples if no real examples generated
    if not examples:
        examples = [
            {
                "what_was_said": "I'm calling about your treatment.",
                "what_to_say_instead": "Hi [Name], this is [Your Name] from [Practice]. How have you been since your last visit?",
                "coaching_point": "Build rapport first with a warm, personal greeting",
                "impact": "Patient feels valued and conversation starts positively"
            }
        ]
    
    return examples

def _improve_staff_response(staff_response: str, patient_inquiry: str) -> str:
    """Generate improved version of staff response"""
    # Basic improvement logic based on common patterns
    if "appointment" in patient_inquiry.lower():
        return "I can help you with that! We have availability this Tuesday at 2 PM or Thursday at 10 AM. Which works better for you?"
    elif "cost" in patient_inquiry.lower() or "price" in patient_inquiry.lower():
        return "I understand cost is important. Let me explain your options and our financing plans that can help make this affordable."
    elif "pain" in patient_inquiry.lower() or "hurt" in patient_inquiry.lower():
        return "I'm sorry you're experiencing pain. Let me check our emergency slots to get you seen as soon as possible."
    else:
        return f"Thank you for calling! I'm here to help you with that. Let me get some information so I can assist you better."

def _get_coaching_point(call: Dict) -> str:
    """Extract coaching point based on call analysis"""
    performance_analysis = call.get('performance_analysis', {})
    coaching_focus = performance_analysis.get('coaching_focus', [])
    
    if coaching_focus:
        return f"Focus on: {coaching_focus[0]}"
    elif call.get('representative_score', 100) < 75:
        return "Improve overall communication and patient engagement"
    else:
        return "Maintain professional standards and patient rapport"

def _analyze_call_performance(calls: List[Dict]) -> Dict:
    """Analyze performance across selected calls"""
    if not calls:
        return {}
    
    scores = [call.get('representative_score', 0) for call in calls]
    sentiments = [call.get('overall_sentiment', 'neutral') for call in calls]
    
    avg_score = sum(scores) / len(scores) if scores else 0
    positive_sentiment_rate = len([s for s in sentiments if s == 'positive']) / len(sentiments) if sentiments else 0
    
    # Collect strengths and weaknesses
    all_strengths = []
    all_weaknesses = []
    
    for call in calls:
        perf_analysis = call.get('performance_analysis', {})
        if isinstance(perf_analysis, dict):
            all_strengths.extend(perf_analysis.get('strengths', []))
            all_weaknesses.extend(perf_analysis.get('weaknesses', []))
    
    # Count frequency of strengths and weaknesses
    strength_counts = {}
    weakness_counts = {}
    
    for strength in all_strengths:
        strength_counts[strength] = strength_counts.get(strength, 0) + 1
    
    for weakness in all_weaknesses:
        weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
    
    return {
        "average_score": round(avg_score, 1),
        "positive_sentiment_rate": round(positive_sentiment_rate * 100, 1),
        "total_calls_analyzed": len(calls),
        "common_strengths": sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:3],
        "common_weaknesses": sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:3],
        "score_distribution": {
            "excellent": len([s for s in scores if s >= 85]),
            "good": len([s for s in scores if 70 <= s < 85]),
            "needs_improvement": len([s for s in scores if s < 70])
        }
    }

def _generate_improvement_recommendations(calls: List[Dict]) -> List[str]:
    """Generate specific improvement recommendations"""
    recommendations = []
    
    # Analyze common issues
    low_score_calls = [call for call in calls if call.get('representative_score', 100) < 75]
    missed_opportunities = [call for call in calls if call.get('high_value_missed_opportunity', False)]
    negative_sentiment = [call for call in calls if call.get('overall_sentiment', '') == 'negative']
    
    if low_score_calls:
        recommendations.append(f"Focus on improving basic communication skills - {len(low_score_calls)} calls had scores below 75%")
    
    if missed_opportunities:
        recommendations.append(f"Training needed on opportunity recognition - {len(missed_opportunities)} calls had missed high-value opportunities")
    
    if negative_sentiment:
        recommendations.append(f"Work on patient rapport and empathy - {len(negative_sentiment)} calls had negative sentiment")
    
    # Add general recommendations
    recommendations.extend([
        "Practice active listening techniques to better understand patient needs",
        "Role-play common scenarios to improve confidence and consistency",
        "Review successful call examples to understand best practices"
    ])
    
    return recommendations[:5]  # Return top 5 recommendations

# Replace the PDF generation endpoint in your coaching_api_routes.py with this version

@coaching_router.post("/generate-pdf")
async def generate_training_pdf(request: PDFGenerationRequest):
    """
    Generate PDF training material from case study
    """
    try:
        if not request.case_study_data:
            raise HTTPException(status_code=400, detail="No case study data provided")
        
        # Try to use reportlab if available, otherwise create a simple PDF
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from io import BytesIO
            
            # Create PDF in memory
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                  rightMargin=0.75*inch, leftMargin=0.75*inch,
                                  topMargin=0.75*inch, bottomMargin=0.75*inch)
            
            # Get styles
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title = Paragraph(f"<font size=20><b>{request.title}</b></font>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Add metadata
            metadata = f"""
            <font size=12><b>Training Material</b></font><br/>
            Target Employee: {request.target_employee}<br/>
            Analysis Type: {request.analysis_type.title()}<br/>
            Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
            """
            story.append(Paragraph(metadata, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Add case study content
            case_study = request.case_study_data
            
            # Conversation examples
            if case_study.get('conversation_examples'):
                story.append(Paragraph("<font size=14><b>Conversation Examples</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, example in enumerate(case_study['conversation_examples'][:3], 1):
                    example_text = f"""
                    <font size=12><b>Example {i}:</b></font><br/>
                    <font color="red"><b>What was said:</b></font> {example.get('what_was_said', '')}<br/>
                    <font color="green"><b>What to say instead:</b></font> {example.get('what_to_say_instead', '')}<br/>
                    <font color="blue"><b>Coaching point:</b></font> {example.get('coaching_point', '')}<br/>
                    """
                    story.append(Paragraph(example_text, styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))
            
            # Key principles
            if case_study.get('key_principles'):
                story.append(Paragraph("<font size=14><b>Key Coaching Principles</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, principle in enumerate(case_study['key_principles'], 1):
                    principle_text = f"{i}. {principle}"
                    story.append(Paragraph(principle_text, styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            # Follow-up flow
            if case_study.get('follow_up_flow'):
                flow = case_study['follow_up_flow']
                story.append(Paragraph("<font size=14><b>Standard Follow-Up Flow</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                if flow.get('steps'):
                    for step in flow['steps']:
                        story.append(Paragraph(f"• {step}", styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))
                
                if flow.get('goal'):
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(f"<b>Goal:</b> {flow['goal']}", styles['Normal']))
                
                if flow.get('key_message'):
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(f"<b>Remember:</b> {flow['key_message']}", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF with reportlab: {len(pdf_content)} bytes")
            
        except ImportError:
            # Fallback: Create a simple text-based document
            logger.warning("ReportLab not available, creating text-based document")
            
            content = f"""COACHING TRAINING MATERIAL
{'=' * 50}

{request.title}

Target Employee: {request.target_employee}
Analysis Type: {request.analysis_type.title()}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

{'=' * 50}

"""
            
            case_study = request.case_study_data
            
            # Add conversation examples
            if case_study.get('conversation_examples'):
                content += "\nCONVERSATION EXAMPLES:\n" + "-" * 25 + "\n\n"
                
                for i, example in enumerate(case_study['conversation_examples'][:3], 1):
                    content += f"Example {i}:\n"
                    content += f"What was said: {example.get('what_was_said', '')}\n"
                    content += f"What to say instead: {example.get('what_to_say_instead', '')}\n"
                    content += f"Coaching point: {example.get('coaching_point', '')}\n\n"
            
            # Add key principles
            if case_study.get('key_principles'):
                content += "\nKEY COACHING PRINCIPLES:\n" + "-" * 25 + "\n\n"
                
                for i, principle in enumerate(case_study['key_principles'], 1):
                    content += f"{i}. {principle}\n"
                
                content += "\n"
            
            # Add follow-up flow
            if case_study.get('follow_up_flow'):
                flow = case_study['follow_up_flow']
                content += "\nSTANDARD FOLLOW-UP FLOW:\n" + "-" * 25 + "\n\n"
                
                if flow.get('steps'):
                    for step in flow['steps']:
                        content += f"• {step}\n"
                
                if flow.get('goal'):
                    content += f"\nGoal: {flow['goal']}\n"
                
                if flow.get('key_message'):
                    content += f"\nRemember: {flow['key_message']}\n"
            
            content += "\n" + "=" * 50 + "\n"
            content += "End of Training Material\n"
            
            pdf_content = content.encode('utf-8')
            logger.info(f"Generated text document: {len(pdf_content)} bytes")
        
        from fastapi.responses import Response
        
        # Clean filename
        safe_filename = "".join(c for c in request.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        
        # Return the PDF/document
        return Response(
            content=pdf_content,
            media_type='application/pdf',
            headers={
                "Content-Disposition": f"attachment; filename={safe_filename}.pdf",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@coaching_router.get("/analytics")
async def get_coaching_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get coaching analytics and statistics
    """
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().isoformat()
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        data_loader = get_data_loader()
        all_calls = await data_loader.load_all_calls()
        
        # Filter calls by date range
        filtered_calls = []
        for call in all_calls:
            try:
                call_date_str = call.get('Analysis_Date') or call.get('analysis_date', '')
                if call_date_str:
                    # Handle MM/DD/YYYY format
                    if '/' in call_date_str:
                        call_date = datetime.strptime(call_date_str, '%m/%d/%Y')
                    else:
                        call_date = datetime.fromisoformat(call_date_str)
                    
                    start_dt = datetime.fromisoformat(start_date)
                    end_dt = datetime.fromisoformat(end_date)
                    
                    if start_dt <= call_date <= end_dt:
                        filtered_calls.append(call)
            except:
                continue
        
        # Calculate analytics
        total_calls = len(filtered_calls)
        if total_calls == 0:
            return {
                "total_calls": 0,
                "coaching_candidates": 0,
                "average_score": 0,
                "performance_distribution": {},
                "sentiment_distribution": {},
                "employee_performance": {},
                "improvement_opportunities": []
            }
        
        # Convert calls to coaching format for analysis
        coaching_calls = [_map_call_data_to_coaching_format(call) for call in filtered_calls]
        
        # Performance statistics
        scores = [call.get('representative_score', 0) for call in coaching_calls]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Performance distribution
        excellent = len([s for s in scores if s >= 85])
        good = len([s for s in scores if 70 <= s < 85])
        needs_improvement = len([s for s in scores if s < 70])
        
        performance_distribution = {
            "excellent": round(excellent / total_calls * 100, 1),
            "good": round(good / total_calls * 100, 1),
            "needs_improvement": round(needs_improvement / total_calls * 100, 1)
        }
        
        # Sentiment distribution
        sentiments = [call.get('overall_sentiment', 'neutral') for call in coaching_calls]
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        sentiment_distribution = {
            sentiment: round(count / total_calls * 100, 1)
            for sentiment, count in sentiment_counts.items()
        }
        
        # Employee performance
        employee_performance = {}
        for call in coaching_calls:
            employee = call.get('representative_name', 'Unknown')
            if employee not in employee_performance:
                employee_performance[employee] = {
                    'total_calls': 0,
                    'scores': [],
                    'coaching_candidates': 0
                }
            
            employee_performance[employee]['total_calls'] += 1
            employee_performance[employee]['scores'].append(call.get('representative_score', 0))
            
            # Check if coaching candidate
            if (call.get('representative_score', 100) < 75 or 
                call.get('high_value_missed_opportunity', False)):
                employee_performance[employee]['coaching_candidates'] += 1
        
        # Calculate averages
        for employee, data in employee_performance.items():
            if data['scores']:
                data['average_score'] = round(sum(data['scores']) / len(data['scores']), 1)
            else:
                data['average_score'] = 0
        
        # Coaching candidates
        coaching_candidates = len([
            call for call in coaching_calls 
            if (call.get('representative_score', 100) < 75 or 
                call.get('high_value_missed_opportunity', False))
        ])
        
        # Improvement opportunities
        improvement_opportunities = []
        
        # Analyze common weaknesses
        all_weaknesses = []
        for call in coaching_calls:
            performance_analysis = call.get('performance_analysis', {})
            if isinstance(performance_analysis, dict):
                weaknesses = performance_analysis.get('weaknesses', [])
                all_weaknesses.extend(weaknesses)
        
        # Count weakness frequency
        weakness_counts = {}
        for weakness in all_weaknesses:
            weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
        
        # Top 5 improvement opportunities
        top_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        improvement_opportunities = [
            {
                "area": weakness,
                "frequency": count,
                "percentage": round(count / total_calls * 100, 1)
            }
            for weakness, count in top_weaknesses
        ]
        
        analytics = {
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "total_calls": total_calls,
            "coaching_candidates": coaching_candidates,
            "coaching_percentage": round(coaching_candidates / total_calls * 100, 1) if total_calls > 0 else 0,
            "average_score": round(average_score, 1),
            "performance_distribution": performance_distribution,
            "sentiment_distribution": sentiment_distribution,
            "employee_performance": employee_performance,
            "improvement_opportunities": improvement_opportunities,
            "call_types": list(set([call.get('call_tag', 'Unknown') for call in coaching_calls]))
        }
        
        logger.info(f"Generated coaching analytics for {total_calls} calls")
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating coaching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")

@coaching_router.post("/sessions")
async def save_coaching_session(request: CoachingSessionRequest):
    """
    Save a coaching session record
    """
    try:
        # In a real implementation, you would save this to a database
        session_record = {
            "id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "employee_name": request.employee_name,
            "call_ids": request.call_ids,
            "session_notes": request.session_notes,
            "action_items": request.action_items,
            "session_date": datetime.now().isoformat(),
            "status": "active"
        }
        
        # TODO: Save to database
        # await save_coaching_session_to_db(session_record)
        
        logger.info(f"Saved coaching session for {request.employee_name}")
        return {
            "success": True,
            "session_id": session_record["id"],
            "message": "Coaching session saved successfully (mock implementation)"
        }
        
    except Exception as e:
        logger.error(f"Error saving coaching session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save coaching session: {str(e)}")

@coaching_router.get("/sessions")
async def get_coaching_sessions(
    employee: Optional[str] = None,
    limit: int = 50
):
    """
    Get coaching session history
    """
    try:
        # In a real implementation, you would fetch from a database
        sessions = []
        
        # TODO: Fetch from database
        # sessions = await fetch_coaching_sessions_from_db(employee, limit)
        
        return {
            "sessions": sessions,
            "total": len(sessions),
            "employee_filter": employee,
            "message": "Session history not yet implemented - would return coaching session records"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving coaching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve coaching sessions: {str(e)}")

# Additional utility routes

@coaching_router.get("/employees/performance-summary")
async def get_employee_performance_summary():
    """
    Get performance summary for all employees
    """
    try:
        data_loader = get_data_loader()
        all_calls = await data_loader.load_all_calls()
        
        # Convert calls to coaching format
        coaching_calls = [_map_call_data_to_coaching_format(call) for call in all_calls]
        
        employee_summary = {}
        
        for call in coaching_calls:
            employee = call.get('representative_name', 'Unknown')
            if employee == 'Unknown':
                continue
                
            if employee not in employee_summary:
                employee_summary[employee] = {
                    'total_calls': 0,
                    'scores': [],
                    'recent_calls': [],
                    'coaching_opportunities': 0,
                    'improvement_trend': 'stable'
                }
            
            summary = employee_summary[employee]
            summary['total_calls'] += 1
            summary['scores'].append(call.get('representative_score', 0))
            
            # Add recent calls (for trend analysis)
            summary['recent_calls'].append({
                'date': call.get('analysis_date'),
                'score': call.get('representative_score', 0),
                'sentiment': call.get('overall_sentiment')
            })
            
            # Count coaching opportunities
            if (call.get('representative_score', 100) < 75 or 
                call.get('high_value_missed_opportunity', False)):
                summary['coaching_opportunities'] += 1
        
        # Calculate averages and trends
        for employee, data in employee_summary.items():
            if data['scores']:
                data['average_score'] = round(sum(data['scores']) / len(data['scores']), 1)
                
                # Simple trend analysis (last 5 calls vs previous 5)
                recent_scores = data['scores'][-5:] if len(data['scores']) >= 5 else data['scores']
                previous_scores = data['scores'][-10:-5] if len(data['scores']) >= 10 else []
                
                if previous_scores:
                    recent_avg = sum(recent_scores) / len(recent_scores)
                    previous_avg = sum(previous_scores) / len(previous_scores)
                    
                    if recent_avg > previous_avg + 5:
                        data['improvement_trend'] = 'improving'
                    elif recent_avg < previous_avg - 5:
                        data['improvement_trend'] = 'declining'
                    else:
                        data['improvement_trend'] = 'stable'
            else:
                data['average_score'] = 0
            
            # Calculate coaching opportunity percentage
            data['coaching_percentage'] = round(
                data['coaching_opportunities'] / data['total_calls'] * 100, 1
            ) if data['total_calls'] > 0 else 0
        
        # Sort by coaching opportunities (highest first)
        sorted_employees = sorted(
            employee_summary.items(), 
            key=lambda x: x[1]['coaching_opportunities'], 
            reverse=True
        )
        
        return {
            "employee_performance": dict(sorted_employees),
            "summary_stats": {
                "total_employees": len(employee_summary),
                "employees_needing_coaching": len([
                    emp for emp, data in employee_summary.items() 
                    if data['coaching_opportunities'] > 0
                ]),
                "average_score_across_team": round(
                    sum([data['average_score'] for data in employee_summary.values()]) / len(employee_summary), 1
                ) if employee_summary else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating employee performance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate performance summary: {str(e)}")

# Health check for coaching system
@coaching_router.get("/health")
async def coaching_system_health():
    """
    Check the health of the coaching system
    """
    try:
        # Check data loader
        data_loader_status = "available"
        calls_count = 0
        sample_call = None
        
        try:
            data_loader = get_data_loader()
            calls = await data_loader.load_all_calls()
            calls_count = len(calls)
            sample_call = calls[0] if calls else None
        except Exception as e:
            data_loader_status = f"error: {str(e)}"
        
        # Check LLM availability
        llm_status = "available" if LLMAnalyzer else "unavailable"
        
        return {
            "status": "healthy" if data_loader_status == "available" else "partial",
            "components": {
                "data_loader": data_loader_status,
                "llm_analyzer": llm_status,
                "coaching_router": "available"
            },
            "features": {
                "call_filtering": True,
                "call_types": True,
                "analytics": True,
                "case_study_generation": True,
                "pdf_generation": False  # Not implemented yet
            },
            "data_summary": {
                "total_calls": calls_count,
                "data_sources": ["local_files", "google_sheets"] if data_loader_status == "available" else [],
                "sample_call_keys": list(sample_call.keys()) if sample_call else []
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Export router for inclusion in main app
__all__ = ['coaching_router']