"""
Coaching Analysis Prompts - Enhanced for Better LLM Results
"""

def get_individual_call_analysis_prompt(call_data: dict, employee: str) -> str:
    """
    Enhanced prompt for individual call analysis with better context awareness
    """
    
    # Extract call details
    summary = call_data.get('call_summary', 'No summary available')
    full_transcript = call_data.get('Full_Transcript_With_Timestamps', '') or call_data.get('full_transcript', '')
    score = call_data.get('representative_score', 0)
    sentiment = call_data.get('overall_sentiment', 'neutral')
    call_type = call_data.get('call_tag', 'general_inquiry')
    
    # Use full transcript if available, otherwise use summary
    transcript_content = full_transcript if full_transcript.strip() else summary
    
    # Check for potential technical issues
    technical_flag = ""
    if full_transcript and ("his last name is" in full_transcript.lower() and full_transcript.lower().count("his last name is") > 5):
        technical_flag = "\n⚠️ IMPORTANT: This transcript shows excessive repetition which may indicate a technical/system issue rather than employee performance. Consider this in your analysis."
    
    prompt = f"""You are an expert dental office coaching analyst. Analyze this call transcript to provide specific, actionable coaching insights.

CALL CONTEXT:
- Employee: {employee}
- Call Type: {call_type.replace('_', ' ').title()}
- Performance Score: {score}%
- Overall Sentiment: {sentiment}
- Transcript Length: {len(transcript_content)} characters
{technical_flag}

FULL CALL TRANSCRIPT:
{transcript_content}

ANALYSIS REQUIREMENTS:
1. Read the ENTIRE transcript carefully before analyzing
2. Identify SPECIFIC moments from the actual conversation (with exact quotes)
3. Distinguish between technical/system issues vs. performance issues
4. Provide actionable behavioral changes, not generic advice
5. Base all recommendations on actual transcript evidence

CRITICAL ANALYSIS POINTS:
- Does this transcript show technical malfunctions (excessive repetition, system glitches)?
- What specific words/phrases did the employee actually use?
- What concrete behaviors need improvement?
- What did the employee do well in this specific call?

Respond in this exact JSON format:
{{
    "technical_issues_detected": false or true (if repetitive patterns suggest system problems),
    "strengths": [
        "Specific strength with exact quote from transcript",
        "Another specific strength with evidence"
    ],
    "areas_for_improvement": [
        "Specific behavior to change with exact transcript reference",
        "Another concrete improvement with evidence"
    ],
    "coaching_priorities": [
        "Specific skill to practice based on this call",
        "Another specific coaching focus"
    ],
    "training_focus": "Most important training need based on transcript evidence",
    "conversation_examples": [
        {{
            "what_employee_said": "Exact quote from transcript",
            "what_to_say_instead": "Specific improved version",
            "coaching_point": "Why this change matters",
            "expected_outcome": "What this achieves"
        }},
        {{
            "what_employee_said": "Another exact quote",
            "what_to_say_instead": "Specific improvement",
            "coaching_point": "Specific reason for change",
            "expected_outcome": "Concrete benefit"
        }}
    ],
    "follow_up_recommendations": [
        "Specific practice exercise based on this call",
        "Concrete next step for improvement"
    ],
    "transcript_based_insights": [
        "Specific observation from actual conversation",
        "Another insight based on real dialogue"
    ]
}}

CRITICAL REMINDERS:
- Use ONLY actual quotes from the transcript
- If transcript shows technical issues (excessive repetition, system glitches), flag this
- Focus on specific behavioral changes, not generic communication advice
- Provide actionable recommendations based on what actually happened
- Be specific about what to practice and how to measure improvement"""

    return prompt

def get_comparative_analysis_prompt(calls_data: list, target_employee: str, title: str) -> str:
    """
    Enhanced prompt for comparative analysis across multiple calls
    """
    
    # Prepare call summaries
    call_summaries = []
    for i, call in enumerate(calls_data, 1):
        score = call.get('representative_score', 0)
        call_type = call.get('call_tag', 'general_inquiry')
        sentiment = call.get('overall_sentiment', 'neutral')
        summary = call.get('call_summary', '')[:300]  # Truncate for prompt length
        
        call_summaries.append(f"""
CALL {i}:
- Score: {score}%
- Type: {call_type.replace('_', ' ').title()}
- Sentiment: {sentiment}
- Summary: {summary}
""")
    
    calls_text = "\n".join(call_summaries)
    
    prompt = f"""You are an expert dental office performance analyst. Compare these {len(calls_data)} calls to identify patterns and create targeted training recommendations.

TARGET EMPLOYEE: {target_employee}
ANALYSIS TITLE: {title}

CALLS TO ANALYZE:
{calls_text}

ANALYSIS REQUIREMENTS:
1. Identify specific performance patterns across all calls
2. Compare high-scoring vs. low-scoring calls to find success factors
3. Provide concrete training recommendations based on actual performance gaps
4. Focus on measurable behavioral changes

Respond in this exact JSON format:
{{
    "performance_analysis": {{
        "score_range": "X% to Y%",
        "average_performance": "Z%",
        "consistency_assessment": "Specific observation about performance consistency"
    }},
    "best_practices": [
        {{
            "practice": "Specific behavior from high-scoring calls",
            "example": "Concrete example from the calls",
            "impact": "Measurable benefit of this practice"
        }}
    ],
    "improvement_opportunities": [
        {{
            "opportunity": "Specific area needing improvement",
            "evidence": "Pattern observed across calls",
            "solution": "Concrete training approach"
        }}
    ],
    "key_lessons": [
        "Specific lesson from comparing calls",
        "Another concrete insight from pattern analysis",
        "Third specific lesson for training"
    ],
    "training_recommendations": [
        {{
            "focus_area": "Specific skill to develop",
            "methods": [
                "Concrete training method 1",
                "Specific practice exercise 2"
            ],
            "expected_outcome": "Measurable improvement target",
            "success_metrics": "How to measure progress"
        }}
    ]
}}

Focus on SPECIFIC, ACTIONABLE insights based on actual call performance patterns."""

    return prompt

def get_conversation_example_extraction_prompt(transcript: str) -> str:
    """
    Prompt specifically for extracting real conversation examples from transcripts
    """
    
    prompt = f"""Extract 2-3 specific conversation examples from this dental office call transcript that could be used for coaching purposes.

TRANSCRIPT:
{transcript}

REQUIREMENTS:
- Find actual employee responses that could be improved
- Provide the EXACT words the employee said
- Suggest specific improvements
- Focus on concrete behavioral changes

Respond in this exact JSON format:
{{
    "conversation_examples": [
        {{
            "employee_quote": "Exact words from transcript",
            "context": "What was happening in the call",
            "improvement": "Specific better response",
            "coaching_point": "Why this change helps",
            "skill_focus": "What skill this develops"
        }}
    ]
}}

Only use actual quotes from the provided transcript."""

    return prompt