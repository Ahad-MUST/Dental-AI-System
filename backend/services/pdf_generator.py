"""
PDF Generator for Coaching Materials
Creates professional training documents from case studies
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from io import BytesIO
import json

# For PDF generation - you'll need to install reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF generation will use fallback method.")

logger = logging.getLogger(__name__)

class CoachingPDFGenerator:
    """
    Generates professional PDF coaching materials from case studies
    """
    
    def __init__(self):
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.margin = 0.75 * inch
        
    def generate_training_pdf(self, case_study_data: Dict[str, Any]) -> bytes:
        """
        Generate a professional training PDF from case study data
        
        Args:
            case_study_data: Complete case study analysis
            
        Returns:
            PDF content as bytes
        """
        try:
            if not REPORTLAB_AVAILABLE:
                return self._generate_fallback_pdf(case_study_data)
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Build content
            story = []
            styles = getSampleStyleSheet()
            
            # Add custom styles
            self._add_custom_styles(styles)
            
            # Generate content based on case study type
            if case_study_data.get('type') == 'individual':
                story.extend(self._build_individual_content(case_study_data, styles))
            else:
                story.extend(self._build_comparative_content(case_study_data, styles))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info(f"Generated PDF training material: {case_study_data.get('title', 'Untitled')}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return self._generate_fallback_pdf(case_study_data)
    
    def _add_custom_styles(self, styles):
        """Add custom paragraph styles"""
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.HexColor('#1e40af')
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#1e40af'),
            borderWidth=1,
            borderColor=colors.HexColor('#e2e8f0'),
            borderPadding=8,
            backColor=colors.HexColor('#f8fafc')
        ))
        
        # Subsection style
        styles.add(ParagraphStyle(
            name='SubHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#374151')
        ))
        
        # Example box style
        styles.add(ParagraphStyle(
            name='ExampleBox',
            parent=styles['Normal'],
            fontSize=10,
            spaceBefore=8,
            spaceAfter=8,
            borderWidth=1,
            borderColor=colors.HexColor('#d1d5db'),
            borderPadding=10,
            backColor=colors.HexColor('#f9fafb')
        ))
        
        # Coaching point style
        styles.add(ParagraphStyle(
            name='CoachingPoint',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=6,
            spaceAfter=6,
            textColor=colors.HexColor('#059669'),
            leftIndent=20
        ))
    
    def _build_individual_content(self, case_study: Dict, styles) -> List:
        """Build content for individual training case study"""
        
        story = []
        
        # Header
        story.append(Paragraph("📞 Patient Follow-Up Training", styles['CustomTitle']))
        story.append(Paragraph(f"<b>{case_study.get('title', 'Training Case Study')}</b>", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Case study section
        primary_call = case_study.get('primary_call', {})
        employee_name = case_study.get('target_employee', 'Employee')
        
        story.append(Paragraph("1. Case Study Analysis", styles['SectionHeader']))
        
        # Call details table
        call_data = [
            ['Employee:', employee_name],
            ['Date:', primary_call.get('analysis_date', 'Unknown')],
            ['Performance Score:', f"{primary_call.get('representative_score', 0)}%"],
            ['Call Type:', primary_call.get('call_tag', 'Unknown').replace('_', ' ').title()],
            ['Overall Sentiment:', primary_call.get('overall_sentiment', 'Unknown').title()]
        ]
        
        call_table = Table(call_data, colWidths=[2*inch, 4*inch])
        call_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(call_table)
        story.append(Spacer(1, 20))
        
        # What was said vs what to say examples
        examples = case_study.get('conversation_examples', [])
        if examples:
            story.append(Paragraph("What Was Said vs. What to Say Instead", styles['SubHeader']))
            
            for i, example in enumerate(examples[:3], 1):  # Limit to 3 examples
                # Create comparison table
                comparison_data = [
                    ['What Was Said', 'What to Say Instead'],
                    [example.get('what_was_said', ''), example.get('what_to_say_instead', '')]
                ]
                
                comparison_table = Table(comparison_data, colWidths=[3*inch, 3*inch])
                comparison_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                    ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#059669')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#374151')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                
                story.append(comparison_table)
                
                # Add coaching point
                coaching_point = example.get('coaching_point', '')
                if coaching_point:
                    story.append(Paragraph(f"<b>Key Point:</b> {coaching_point}", styles['CoachingPoint']))
                
                story.append(Spacer(1, 15))
        
        # Key principles section
        story.append(Paragraph("2. Key Coaching Principles", styles['SectionHeader']))
        
        principles = case_study.get('key_principles', [])
        for i, principle in enumerate(principles, 1):
            story.append(Paragraph(f"{i}. {principle}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 20))
        
        # Follow-up flow
        follow_up = case_study.get('follow_up_flow', {})
        if follow_up:
            story.append(Paragraph("3. Standard Follow-Up Flow", styles['SectionHeader']))
            
            steps = follow_up.get('steps', [])
            for step in steps:
                story.append(Paragraph(f"• {step}", styles['Normal']))
                story.append(Spacer(1, 4))
            
            story.append(Spacer(1, 15))
            
            # Goal
            goal = follow_up.get('goal', '')
            if goal:
                story.append(Paragraph(f"<b>✅ Goal:</b> {goal}", styles['ExampleBox']))
                story.append(Spacer(1, 10))
            
            # Key message
            key_message = follow_up.get('key_message', '')
            if key_message:
                story.append(Paragraph(f"<b>💡 Remember:</b> {key_message}", styles['ExampleBox']))
        
        return story
    
    def _build_comparative_content(self, case_study: Dict, styles) -> List:
        """Build content for comparative analysis case study"""
        
        story = []
        
        # Header
        story.append(Paragraph("📊 Comparative Call Analysis", styles['CustomTitle']))
        story.append(Paragraph(f"<b>{case_study.get('title', 'Comparative Analysis')}</b>", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Overview
        calls_analyzed = case_study.get('calls_analyzed', 0)
        pattern_analysis = case_study.get('pattern_analysis', {})
        
        story.append(Paragraph("1. Analysis Overview", styles['SectionHeader']))
        
        overview_data = [
            ['Total Calls Analyzed:', str(calls_analyzed)],
            ['Average Performance Score:', f"{pattern_analysis.get('average_score', 0)}%"],
            ['Performance Range:', f"{pattern_analysis.get('score_range', {}).get('min', 0)}% - {pattern_analysis.get('score_range', {}).get('max', 0)}%"],
            ['Positive Sentiment Rate:', f"{pattern_analysis.get('positive_sentiment_rate', 0)}%"]
        ]
        
        overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Best practices section
        comparative_analysis = case_study.get('comparative_analysis', {})
        best_practices = comparative_analysis.get('best_practices', [])
        
        if best_practices:
            story.append(Paragraph("2. Best Practices Identified", styles['SectionHeader']))
            
            for practice in best_practices[:3]:  # Limit to top 3
                story.append(Paragraph(f"<b>{practice.get('practice', '')}</b>", styles['SubHeader']))
                story.append(Paragraph(f"Example: {practice.get('example', '')}", styles['Normal']))
                story.append(Paragraph(f"Impact: {practice.get('impact', '')}", styles['CoachingPoint']))
                story.append(Spacer(1, 12))
        
        # Improvement opportunities
        improvements = comparative_analysis.get('improvement_opportunities', [])
        
        if improvements:
            story.append(Paragraph("3. Common Improvement Areas", styles['SectionHeader']))
            
            for improvement in improvements[:3]:  # Limit to top 3
                story.append(Paragraph(f"<b>{improvement.get('opportunity', '')}</b>", styles['SubHeader']))
                story.append(Paragraph(f"Example: {improvement.get('example', '')}", styles['Normal']))
                story.append(Paragraph(f"Solution: {improvement.get('solution', '')}", styles['CoachingPoint']))
                story.append(Spacer(1, 12))
        
        # Training recommendations
        training_recs = comparative_analysis.get('training_recommendations', [])
        
        if training_recs:
            story.append(Paragraph("4. Training Recommendations", styles['SectionHeader']))
            
            for rec in training_recs:
                story.append(Paragraph(f"<b>Focus Area:</b> {rec.get('focus_area', '')}", styles['Normal']))
                
                methods = rec.get('methods', [])
                if methods:
                    story.append(Paragraph("Methods:", styles['Normal']))
                    for method in methods:
                        story.append(Paragraph(f"• {method}", styles['Normal']))
                
                expected_outcome = rec.get('expected_outcome', '')
                if expected_outcome:
                    story.append(Paragraph(f"<b>Expected Outcome:</b> {expected_outcome}", styles['CoachingPoint']))
                
                story.append(Spacer(1, 15))
        
        # Success metrics
        metrics = comparative_analysis.get('success_metrics', [])
        if metrics:
            story.append(Paragraph("5. Success Metrics", styles['SectionHeader']))
            
            for metric in metrics:
                story.append(Paragraph(f"• {metric}", styles['Normal']))
                story.append(Spacer(1, 4))
        
        return story
    
    def _generate_fallback_pdf(self, case_study_data: Dict) -> bytes:
        """Generate a simple text-based PDF when ReportLab is not available"""
        
        # Create a simple HTML-like structure that can be converted to PDF
        html_content = self._generate_html_content(case_study_data)
        
        # For production, you might want to use libraries like weasyprint or pdfkit
        # For now, return the HTML as bytes with a note
        fallback_content = f"""
PDF Generation Fallback Mode

{case_study_data.get('title', 'Training Case Study')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To enable full PDF generation, install ReportLab:
pip install reportlab

Case Study Data:
{json.dumps(case_study_data, indent=2)}
"""
        
        return fallback_content.encode('utf-8')
    
    def _generate_html_content(self, case_study_data: Dict) -> str:
        """Generate HTML content for fallback PDF generation"""
        
        title = case_study_data.get('title', 'Training Case Study')
        case_type = case_study_data.get('type', 'individual')
        employee = case_study_data.get('target_employee', 'Employee')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .section {{ margin-bottom: 25px; }}
        .example-box {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; background-color: #f9f9f9; }}
        .coaching-point {{ color: #059669; font-weight: bold; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .what-was-said {{ background-color: #fee2e2; }}
        .what-to-say {{ background-color: #dcfce7; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📞 {title}</h1>
        <h2>Coaching Training Material</h2>
        <p>Generated on: {datetime.now().strftime('%B %d, %Y')}</p>
        <p>Target Employee: {employee}</p>
    </div>
"""
        
        if case_type == 'individual':
            html += self._generate_individual_html(case_study_data)
        else:
            html += self._generate_comparative_html(case_study_data)
        
        html += """
    <div class="section">
        <p><strong>Note:</strong> This training material was generated from real call analysis. 
        Use these examples and principles to improve patient communication and booking rates.</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_individual_html(self, case_study: Dict) -> str:
        """Generate HTML content for individual case study"""
        
        html = '<div class="section"><h2>1. Case Study Analysis</h2>'
        
        # Add call details
        primary_call = case_study.get('primary_call', {})
        html += f"""
        <table>
            <tr><td><strong>Date:</strong></td><td>{primary_call.get('analysis_date', 'Unknown')}</td></tr>
            <tr><td><strong>Performance Score:</strong></td><td>{primary_call.get('representative_score', 0)}%</td></tr>
            <tr><td><strong>Call Type:</strong></td><td>{primary_call.get('call_tag', 'Unknown').replace('_', ' ').title()}</td></tr>
        </table>
        """
        
        # Add examples
        examples = case_study.get('conversation_examples', [])
        if examples:
            html += '<h3>What Was Said vs. What to Say Instead</h3>'
            
            for example in examples[:3]:
                html += f"""
                <table>
                    <tr>
                        <th class="what-was-said">What Was Said</th>
                        <th class="what-to-say">What to Say Instead</th>
                    </tr>
                    <tr>
                        <td>{example.get('what_was_said', '')}</td>
                        <td>{example.get('what_to_say_instead', '')}</td>
                    </tr>
                </table>
                <div class="coaching-point">Key Point: {example.get('coaching_point', '')}</div>
                """
        
        html += '</div>'
        
        # Add principles
        principles = case_study.get('key_principles', [])
        if principles:
            html += '<div class="section"><h2>2. Key Principles</h2><ul>'
            for principle in principles:
                html += f'<li>{principle}</li>'
            html += '</ul></div>'
        
        return html
    
    def _generate_comparative_html(self, case_study: Dict) -> str:
        """Generate HTML content for comparative case study"""
        
        html = '<div class="section"><h2>1. Analysis Overview</h2>'
        
        pattern_analysis = case_study.get('pattern_analysis', {})
        html += f"""
        <table>
            <tr><td><strong>Calls Analyzed:</strong></td><td>{case_study.get('calls_analyzed', 0)}</td></tr>
            <tr><td><strong>Average Score:</strong></td><td>{pattern_analysis.get('average_score', 0)}%</td></tr>
            <tr><td><strong>Positive Sentiment Rate:</strong></td><td>{pattern_analysis.get('positive_sentiment_rate', 0)}%</td></tr>
        </table>
        </div>
        """
        
        # Add best practices
        comparative_analysis = case_study.get('comparative_analysis', {})
        best_practices = comparative_analysis.get('best_practices', [])
        
        if best_practices:
            html += '<div class="section"><h2>2. Best Practices</h2>'
            
            for practice in best_practices[:3]:
                html += f"""
                <div class="example-box">
                    <h4>{practice.get('practice', '')}</h4>
                    <p><strong>Example:</strong> {practice.get('example', '')}</p>
                    <p class="coaching-point">Impact: {practice.get('impact', '')}</p>
                </div>
                """
            
            html += '</div>'
        
        return html