"""
Coaching Library API Routes - CLEANED VERSION
Only includes fields that exist in Google Sheets and are displayed on frontend
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from services.llm_analyzer import LLMAnalyzer
    from services.data_loader import DataLoader
    from services.coaching_service import CoachingService
except ImportError as e:
    print(f"Warning: Could not import services: {e}")
    LLMAnalyzer = None
    DataLoader = None
    CoachingService = None

logger = logging.getLogger(__name__)

coaching_router = APIRouter(prefix="/api/coaching", tags=["coaching"])

# Pydantic models - cleaned
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
    analysis_type: str
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

# Dependencies
def get_data_loader():
    if DataLoader:
        return DataLoader()
    else:
        raise HTTPException(status_code=500, detail="DataLoader not available")

def get_coaching_service():
    """Get the global coaching service initialized during startup"""
    try:
        # Import api_server to access the global coaching_service
        import api_server
        
        # Check if the global coaching_service exists and is initialized
        if hasattr(api_server, 'coaching_service') and api_server.coaching_service is not None:
            logger.debug("Using global coaching service from api_server")
            return api_server.coaching_service
        else:
            logger.error("Global coaching_service is None or not found in api_server")
            raise HTTPException(
                status_code=500, 
                detail="Global coaching service not found - server may not have started properly"
            )
            
    except ImportError as e:
        logger.error(f"Failed to import api_server: {e}")
        # Fallback: try to create a new instance (for testing/debugging)
        try:
            if LLMAnalyzer and CoachingService:
                logger.warning("Creating fallback coaching service instance")
                llm_analyzer = LLMAnalyzer()
                return CoachingService(llm_analyzer)
            else:
                raise HTTPException(status_code=500, detail="Cannot create fallback coaching service - imports not available")
        except Exception as fallback_error:
            logger.error(f"Fallback coaching service creation failed: {fallback_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Coaching service unavailable - API server import failed: {e}"
            )
    except Exception as e:
        logger.error(f"Unexpected error accessing coaching service: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to access coaching service: {str(e)}"
        )

def _generate_unique_call_id(call_data: Dict, existing_ids: set = None) -> str:
    """Generate unique call ID"""
    if existing_ids is None:
        existing_ids = set()
    
    # Use Call_File_Name as base
    audio_file = call_data.get('Call_File_Name') or call_data.get('audio_file', '')
    if audio_file:
        from pathlib import Path
        base_id = Path(audio_file).stem
        if base_id not in existing_ids:
            return base_id
    
    # Fallback to existing ID or generate
    existing_id = call_data.get('id')
    if existing_id and existing_id not in existing_ids:
        return existing_id
    
    # Generate from representative and date
    rep_name = call_data.get('Representative_Name', call_data.get('representative_name', 'unknown'))
    date_str = call_data.get('Analysis_Date', '')[:10]
    base_id = f"{rep_name}_{date_str}_{hash(str(call_data)) % 10000}"
    
    counter = 1
    final_id = base_id
    while final_id in existing_ids:
        final_id = f"{base_id}_{counter}"
        counter += 1
    
    return final_id

def _map_call_data_to_coaching_format(call_data: Dict, existing_ids: set = None) -> Dict:
    """Map call data to coaching format - CLEANED VERSION with only existing/display fields"""
    if existing_ids is None:
        existing_ids = set()
    
    coaching_call = {
        # Required fields
        'id': _generate_unique_call_id(call_data, existing_ids),
        'source': call_data.get('source', 'unknown'),
        
        # ONLY FRONTEND DISPLAY FIELDS (as requested)
        'analysis_date': _standardize_date(call_data.get('Analysis_Date', call_data.get('analysis_date', ''))),
        'analysis_time': call_data.get('Analysis_Time', call_data.get('analysis_time', '')),
        'representative_name': call_data.get('Representative_Name', call_data.get('representative_name', 'Unknown')),
        'full_transcript': call_data.get('Full_Transcript_With_Timestamps', call_data.get('full_transcript', '')),
        'call_tag': call_data.get('Call_Tag', call_data.get('call_tag', 'general_inquiry')),
        'representative_score': _extract_score(call_data),
        'overall_sentiment': call_data.get('Overall_Sentiment', call_data.get('overall_sentiment', 'neutral')),
        'call_summary': call_data.get('Call_Summary', call_data.get('call_summary', '')),
        
        # Additional field that exists in sheets but not displayed on frontend
        'high_value_missed_opportunity': _parse_boolean(call_data.get('High_Value_Missed_Opportunity', False)),
    }
    
    existing_ids.add(coaching_call['id'])
    return coaching_call

def _standardize_date(date_value) -> str:
    """Convert date to ISO format"""
    if not date_value:
        return datetime.now().isoformat()
        
    try:
        if isinstance(date_value, str) and 'T' in date_value:
            return date_value
        
        if isinstance(date_value, str) and '/' in date_value:
            date_obj = datetime.strptime(date_value, '%m/%d/%Y')
            return date_obj.isoformat()
        
    except ValueError:
        pass
    
    return str(date_value) if date_value else datetime.now().isoformat()

def _extract_score(call_data: Dict) -> float:
    """Extract and normalize performance score"""
    score = call_data.get('Representative_Score') or call_data.get('representative_score', 0)
    try:
        score_float = float(score)
        if score_float <= 1.0:
            return score_float * 100
        return max(0, min(100, score_float))
    except:
        return 0.0

def _parse_boolean(value) -> bool:
    """Parse boolean from various formats"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', 'yes', '1', 'y']
    return bool(value)

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
    """Get filtered calls for coaching library - CLEANED VERSION"""
    try:
        data_loader = get_data_loader()
        
        # Load all call data
        all_calls = await data_loader.load_all_calls()
        
        if not all_calls:
            logger.warning("No calls found from data loader")
            return []
        
        logger.info(f"Loaded {len(all_calls)} calls from data loader")
        
        # Convert calls to coaching format
        coaching_calls = []
        existing_ids = set()
        
        for call in all_calls:
            try:
                coaching_call = _map_call_data_to_coaching_format(call, existing_ids)
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
                    call.get('full_transcript', ''),
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
    """Get available call types from actual data"""
    try:
        data_loader = get_data_loader()
        all_calls = await data_loader.load_all_calls()
        
        call_types = set()
        for call in all_calls:
            call_type = call.get('Call_Tag') or call.get('call_tag') or call.get('call_type')
            if call_type and call_type.strip():
                call_types.add(call_type.strip())
        
        call_types = sorted([ct for ct in call_types if ct])
        
        return {"call_types": call_types}
        
    except Exception as e:
        logger.error(f"Error retrieving call types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve call types: {str(e)}")

@coaching_router.post("/generate-case-study")
async def generate_case_study(request: CaseStudyRequest):
    """Generate LLM-driven case study"""
    try:
        if not request.calls:
            raise HTTPException(status_code=400, detail="No calls provided for analysis")
        
        if len(request.calls) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 calls allowed for analysis")
        
        if request.analysis_type not in ['individual', 'comparative']:
            raise HTTPException(status_code=400, detail="Analysis type must be 'individual' or 'comparative'")
        
        # Get the global coaching service
        coaching_service = get_coaching_service()
        logger.info(f"Using coaching service for case study generation: {type(coaching_service)}")
        
        # Convert request calls to proper format for the coaching service
        calls_data = []
        for call_dict in request.calls:
            calls_data.append(call_dict)
        
        logger.info(f"Generating {request.analysis_type} case study with {len(calls_data)} calls")
        
        # Use the correct method names from the CoachingService
        if request.analysis_type == 'individual':
            case_study = await coaching_service.generate_individual_case_study(
                calls_data, request.target_employee, request.title
            )
        else:
            case_study = await coaching_service.generate_comparative_case_study(
                calls_data, request.target_employee, request.title
            )
        
        logger.info(f"Successfully generated LLM-driven case study: {request.title}")
        return case_study
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Case study generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate case study: {str(e)}")

@coaching_router.post("/generate-pdf")
async def generate_training_pdf(request: PDFGenerationRequest):
    """Generate PDF using REAL LLM analysis data"""
    try:
        if not request.case_study_data:
            raise HTTPException(status_code=400, detail="No case study data provided")
        
        # Try ReportLab for proper PDF generation
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                  rightMargin=0.75*inch, leftMargin=0.75*inch,
                                  topMargin=0.75*inch, bottomMargin=0.75*inch)
            
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph(f"<font size=20><b>{request.title}</b></font>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Metadata
            metadata = f"""
            <font size=12><b>LLM-Generated Training Material</b></font><br/>
            Target Employee: {request.target_employee}<br/>
            Analysis Type: {request.analysis_type.title()}<br/>
            Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
            """
            story.append(Paragraph(metadata, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            case_study = request.case_study_data
            
            # REAL LLM-generated conversation examples
            if case_study.get('conversation_examples'):
                story.append(Paragraph("<font size=14><b>Conversation Examples (LLM Generated)</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, example in enumerate(case_study['conversation_examples'][:3], 1):
                    example_text = f"""
                    <font size=12><b>Example {i}:</b></font><br/>
                    <font color="red"><b>What Was Said:</b></font> {example.get('current_approach', '')}<br/>
                    <font color="green"><b>What to Say Instead:</b></font> {example.get('recommended_approach', '')}<br/>
                    <font color="blue"><b>Coaching Point:</b></font> {example.get('coaching_point', '')}<br/>
                    <font color="purple"><b>Expected Outcome:</b></font> {example.get('expected_outcome', '')}<br/>
                    """
                    story.append(Paragraph(example_text, styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))
            
            # REAL LLM-generated coaching principles
            principles = case_study.get('coaching_principles', [])
            if principles:
                story.append(Paragraph("<font size=14><b>Key Coaching Principles (LLM Generated)</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, principle in enumerate(principles, 1):
                    clean_principle = str(principle).strip().strip('"').strip("'")
                    if clean_principle and not clean_principle.startswith(('training_focus', 'strengths', 'areas_for')):
                        principle_text = f"{i}. {clean_principle}"
                        story.append(Paragraph(principle_text, styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            # REAL Performance Analysis
            if case_study.get('performance_overview'):
                perf_analysis = case_study['performance_overview']
                story.append(Paragraph("<font size=14><b>Performance Analysis (LLM Generated)</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                if perf_analysis.get('current_performance_level'):
                    story.append(Paragraph(f"<b>Current Performance:</b> {perf_analysis['current_performance_level']}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                if perf_analysis.get('key_strengths'):
                    story.append(Paragraph("<font size=12><b>Strengths:</b></font>", styles['Normal']))
                    for strength in perf_analysis['key_strengths'][:5]:
                        clean_strength = str(strength).strip().strip('"').strip("'")
                        if clean_strength and not clean_strength.startswith(('"', "'", 'strengths')):
                            story.append(Paragraph(f"• {clean_strength}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                if perf_analysis.get('primary_challenges'):
                    story.append(Paragraph("<font size=12><b>Areas for Improvement:</b></font>", styles['Normal']))
                    for challenge in perf_analysis['primary_challenges'][:5]:
                        clean_challenge = str(challenge).strip().strip('"').strip("'")
                        if clean_challenge and not clean_challenge.startswith(('"', "'", 'areas_for')):
                            story.append(Paragraph(f"• {clean_challenge}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # REAL Development plan
            if case_study.get('development_plan'):
                plan = case_study['development_plan']
                story.append(Paragraph("<font size=14><b>Development Plan (LLM Generated)</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                if plan.get('immediate_focus'):
                    story.append(Paragraph("<font size=12><b>Immediate Focus:</b></font>", styles['Normal']))
                    for focus in plan['immediate_focus'][:3]:
                        clean_focus = str(focus).strip().strip('"').strip("'")
                        if clean_focus:
                            story.append(Paragraph(f"• {clean_focus}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                if plan.get('30_day_goals'):
                    story.append(Paragraph("<font size=12><b>30-Day Goals:</b></font>", styles['Normal']))
                    for goal in plan['30_day_goals'][:3]:
                        clean_goal = str(goal).strip().strip('"').strip("'")
                        if clean_goal:
                            story.append(Paragraph(f"• {clean_goal}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                if plan.get('success_metrics'):
                    story.append(Paragraph("<font size=12><b>Success Metrics:</b></font>", styles['Normal']))
                    for metric in plan['success_metrics'][:3]:
                        clean_metric = str(metric).strip().strip('"').strip("'")
                        if clean_metric:
                            story.append(Paragraph(f"• {clean_metric}", styles['Normal']))
            
            # REAL Recommendations
            if case_study.get('recommendations'):
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("<font size=14><b>Specific Recommendations (LLM Generated)</b></font>", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, recommendation in enumerate(case_study['recommendations'], 1):
                    clean_rec = str(recommendation).strip().strip('"').strip("'")
                    if clean_rec:
                        rec_text = f"{i}. {clean_rec}"
                        story.append(Paragraph(rec_text, styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))
            
            # ADD CALL TRANSCRIPT SECTION
            if case_study.get('call_transcript'):
                transcript = case_study.get('call_transcript')
                if transcript and transcript.strip():
                    story.append(Spacer(1, 0.3*inch))
                    story.append(Paragraph("<font size=14><b>Original Call Transcript</b></font>", styles['Heading2']))
                    story.append(Spacer(1, 0.1*inch))
                    
                    transcript_lines = transcript.split('\n')
                    for line in transcript_lines:
                        line = line.strip()
                        if line:
                            if line.startswith('[') and ']' in line and 'SPEAKER_' in line:
                                story.append(Paragraph(f"<font color='blue'><b>{line}</b></font>", styles['Normal']))
                            else:
                                story.append(Paragraph(line, styles['Normal']))
                            story.append(Spacer(1, 0.02*inch))
            
            doc.build(story)
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated REAL LLM-driven PDF: {len(pdf_content)} bytes")
            
        except ImportError:
            logger.warning("ReportLab not available, creating text document")
            
            content = f"""COACHING TRAINING MATERIAL (LLM-GENERATED)
{'=' * 60}

{request.title}

Target Employee: {request.target_employee}
Analysis Type: {request.analysis_type.title()}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

{'=' * 60}

"""
            
            case_study = request.case_study_data
            
            # Add REAL LLM-generated content
            if case_study.get('conversation_examples'):
                content += "\nCONVERSATION EXAMPLES (LLM GENERATED):\n" + "-" * 40 + "\n\n"
                for i, example in enumerate(case_study['conversation_examples'], 1):
                    content += f"Example {i}:\n"
                    content += f"Current Approach: {example.get('current_approach', '')}\n"
                    content += f"Recommended Approach: {example.get('recommended_approach', '')}\n"
                    content += f"Coaching Point: {example.get('coaching_point', '')}\n"
                    content += f"Expected Outcome: {example.get('expected_outcome', '')}\n\n"
            
            if case_study.get('coaching_principles'):
                content += "\nKEY COACHING PRINCIPLES (LLM GENERATED):\n" + "-" * 40 + "\n\n"
                for i, principle in enumerate(case_study['coaching_principles'], 1):
                    clean_principle = str(principle).strip().strip('"').strip("'")
                    if clean_principle and not clean_principle.startswith(('training_focus', 'strengths')):
                        content += f"{i}. {clean_principle}\n"
                content += "\n"
            
            if case_study.get('call_transcript'):
                transcript = case_study['call_transcript']
                if transcript and transcript.strip():
                    content += "\nORIGINAL CALL TRANSCRIPT:\n" + "=" * 60 + "\n\n"
                    content += transcript
                    content += "\n\n" + "=" * 60 + "\n\n"
            
            content += "\n" + "=" * 60 + "\n"
            content += "End of LLM-Generated Training Material\n"
            
            pdf_content = content.encode('utf-8')
            logger.info(f"Generated REAL LLM text document: {len(pdf_content)} bytes")
        
        from fastapi.responses import Response
        
        safe_filename = "".join(c for c in request.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        
        return Response(
            content=pdf_content,
            media_type='application/pdf',
            headers={
                "Content-Disposition": f"attachment; filename={safe_filename}_LLM_Generated.pdf",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@coaching_router.get("/test")
async def test_coaching_system():
    """Test endpoint to verify coaching system and global service access"""
    try:
        # Test data loader
        data_loader = get_data_loader()
        calls = await data_loader.load_all_calls()
        
        # Test coaching service access
        coaching_service = get_coaching_service()
        
        # Basic service info
        service_info = {
            "service_type": type(coaching_service).__name__,
            "has_llm_analyzer": hasattr(coaching_service, 'llm_analyzer'),
            "llm_analyzer_type": type(coaching_service.llm_analyzer).__name__ if hasattr(coaching_service, 'llm_analyzer') else None,
            "available_methods": [method for method in dir(coaching_service) if not method.startswith('_') and callable(getattr(coaching_service, method))]
        }
        
        return {
            "status": "success",
            "message": "Coaching system is working correctly",
            "data_loader_working": True,
            "coaching_service_available": True,
            "calls_found": len(calls),
            "sample_call_keys": list(calls[0].keys()) if calls else [],
            "coaching_service_info": service_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Coaching test failed: {str(e)}")
        return {
            "status": "error",
            "message": "Coaching system has issues",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Export router
__all__ = ['coaching_router']