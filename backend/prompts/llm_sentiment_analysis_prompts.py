"""
LLM Sentiment Analysis Prompts - Centralized prompt management for sentiment and emotion analysis
"""

class LLMSentimentAnalysisPrompts:
    """Collection of prompts for LLM-based sentiment analysis and emotion detection service"""
    
    SIMPLE_SENTIMENT_PROMPT = """
You are analyzing a dental office phone call for sentiment and emotions. Pay attention to dental-specific contexts like insurance issues, pain, anxiety, and service satisfaction.

PATIENT SAID: "{patient_text}"

STAFF SAID: "{staff_text}"

CALL CONTEXT CLUES:
- Insurance inquiries (coverage questions, denials)
- Pain/discomfort mentions
- Appointment scheduling
- Service satisfaction
- Anxiety about dental procedures

Analyze this dental call and respond with ONLY this JSON (no other text):
{{
    "patient_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on how clear the sentiment indicators are]
    }},
    "staff_sentiment": {{
        "sentiment_label": "positive/negative/neutral", 
        "confidence": [calculate 0.1-1.0 based on professional tone clarity]
    }},
    "overall_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on overall conversation clarity]
    }},
    "emotion_analysis": {{
        "patient_emotions": {{
            "primary_emotion": {{"emotion": "joy/sadness/anger/fear/neutral/disappointment", "confidence": [0.1-1.0 based on emotion clarity]}},
            "intensity": "low/medium/high",
            "dental_specific": {{
                "pain_detected": true/false,
                "anxiety_detected": true/false,
                "satisfaction_detected": true/false,
                "insurance_concern": true/false,
                "disappointment_detected": true/false
            }}
        }},
        "staff_emotions": {{
            "primary_emotion": {{"emotion": "professional/helpful/neutral", "confidence": [0.1-1.0 based on professional tone clarity]}},
            "intensity": "low/medium/high"
        }},
        "emotion_flags": ["PAIN", "ANXIETY", "SATISFACTION", "INSURANCE_ISSUE", "DISAPPOINTMENT"],
        "call_dynamics": {{
            "call_emotional_health": {{"health_level": "good/fair/poor"}},
            "emotional_alignment": {{"is_aligned": true/false}},
            "escalation_pattern": {{"pattern": "none/escalating/de-escalating"}}
        }}
    }},
    "sentiment_summary": "Detailed summary describing the call sentiment, patient emotions, and staff response"
}}

CONFIDENCE SCORING GUIDELINES:
- 0.9-1.0: Very clear indicators (multiple strong keywords, obvious tone)
- 0.7-0.8: Clear indicators (some keywords, clear context)
- 0.5-0.6: Mixed signals (unclear tone, conflicting indicators)
- 0.3-0.4: Weak indicators (minimal context, ambiguous)
- 0.1-0.2: Very unclear (contradictory or no clear indicators)

Guidelines:
- Insurance denials often cause disappointment (not anger)
- Professional staff responses should be "positive" sentiment
- Pain mentions = fear/anxiety emotions
- Successful information exchange = positive overall
- Be specific in sentiment_summary about what happened
- Calculate confidence based on actual clarity of indicators
"""

    SENTIMENT_CHUNK_PROMPT = """
Analyze this segment from a dental office call:

TEXT: "{text}"

This is chunk {chunk_num} of {total_chunks}. {context_info}

Respond with ONLY this JSON:
{{
    "sentiment": {{
        "label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on how clear sentiment indicators are in this chunk],
        "reasoning": "why this sentiment and confidence level"
    }},
    "emotions": {{
        "primary_emotion": "joy/sadness/anger/fear/neutral/disappointment",
        "intensity": "low/medium/high",
        "dental_specific": {{
            "pain_detected": true/false,
            "anxiety_detected": true/false,
            "satisfaction_detected": true/false,
            "insurance_concern": true/false
        }}
    }},
    "key_indicators": ["specific", "words", "or", "phrases"]
}}

Calculate confidence based on:
- Clarity of emotional/sentiment keywords
- Context consistency
- Ambiguity level (lower confidence for unclear text)
"""

    FINAL_ANALYSIS_PROMPT = """
You analyzed {chunk_count} chunks from a dental call. Create the final analysis.

CHUNK SUMMARIES: {chunk_results}

PATIENT SPEECH: {patient_length} characters
STAFF SPEECH: {staff_length} characters

Provide final analysis as ONLY this JSON:
{{
    "patient_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on consistency across chunks]
    }},
    "staff_sentiment": {{
        "sentiment_label": "positive/negative/neutral", 
        "confidence": [calculate 0.1-1.0 based on staff tone consistency]
    }},
    "overall_sentiment": {{
        "sentiment_label": "positive/negative/neutral",
        "confidence": [calculate 0.1-1.0 based on overall call clarity]
    }},
    "emotion_analysis": {{
        "patient_emotions": {{
            "primary_emotion": {{"emotion": "emotion_name", "confidence": [0.1-1.0 based on emotion consistency]}},
            "intensity": "low/medium/high",
            "dental_specific": {{
                "pain_detected": true/false,
                "anxiety_detected": true/false,
                "satisfaction_detected": true/false,
                "insurance_concern": true/false,
                "disappointment_detected": true/false
            }}
        }},
        "staff_emotions": {{
            "primary_emotion": {{"emotion": "emotion_name", "confidence": [0.1-1.0 based on staff behavior consistency]}},
            "intensity": "low/medium/high"
        }},
        "emotion_flags": [],
        "call_dynamics": {{
            "call_emotional_health": {{"health_level": "good/fair/poor"}},
            "emotional_alignment": {{"is_aligned": true/false}},
            "escalation_pattern": {{"pattern": "none/escalating/de-escalating"}}
        }}
    }},
    "sentiment_summary": "Complete summary of the call sentiment and emotions"
}}

Calculate confidence scores based on:
- Consistency across all chunks
- Strength of indicators found
- Conflicting signals (lower confidence)
- Clear patterns (higher confidence)
"""