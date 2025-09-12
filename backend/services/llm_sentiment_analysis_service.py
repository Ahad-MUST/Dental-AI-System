"""
Improved LLM-based Sentiment Analysis and Emotion Detection Service using Qwen 7B
Enhanced with dynamic confidence scoring based on actual analysis factors
"""
import logging
import aiohttp
import asyncio
import json
import re
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMSentimentAnalysisService:
    """LLM-based sentiment analysis and emotion detection using Qwen 7B with intelligent chunking"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.session = None
        self.is_initialized = False
        self.max_single_analysis_length = 1500  # Characters - analyze without chunking
        self.max_chunk_length = 2000  # Characters per chunk for chunking
        
        # Enhanced sentiment analysis prompt for short texts with dental context - NO HARD-CODED CONFIDENCE
        self.simple_sentiment_prompt = """
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

        # Chunk analysis prompt - NO HARD-CODED CONFIDENCE
        self.sentiment_chunk_prompt = """
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

        # Final aggregation prompt - NO HARD-CODED CONFIDENCE
        self.final_analysis_prompt = """
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

    async def initialize(self) -> None:
        """Initialize LLM sentiment analysis service"""
        if self.is_initialized:
            return
            
        try:
            logger.info("Initializing LLM-based sentiment analysis service...")
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Check Ollama connection
            await self._check_ollama_connection()
            
            # Verify model availability
            await self._verify_model()
            
            self.is_initialized = True
            logger.info(f"LLM sentiment analysis service ready with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"LLM sentiment analysis initialization failed: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
            raise

    async def _check_ollama_connection(self):
        """Check if Ollama server is running"""
        try:
            async with self.session.get(f"{self.ollama_url}/api/tags", timeout=5) as response:
                if response.status != 200:
                    raise Exception(f"Ollama server not responding (status: {response.status})")
        except Exception as e:
            raise Exception(f"Cannot connect to Ollama at {self.ollama_url}: {str(e)}")

    async def _verify_model(self):
        """Verify model is available"""
        try:
            async with self.session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model['name'] for model in data.get('models', [])]
                    
                    if self.model_name not in available_models:
                        logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                        raise Exception(f"Model {self.model_name} not available")
        except Exception as e:
            raise Exception(f"Error verifying model: {str(e)}")

    async def _generate_llm_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate LLM response with improved error handling"""
        try:
            if not self.is_initialized or not self.session:
                return ""
            
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Slightly higher for more varied confidence scores
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                    "repeat_penalty": 1.1,
                    "stop": ["Human:", "Assistant:", "\n\n\n"]
                }
            }
            
            async with self.session.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("response", "").strip()
                    logger.debug(f"LLM Response length: {len(result)} chars")
                    return result
                else:
                    logger.error(f"Ollama API error: {response.status}")
                    return ""
                    
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            return ""

    def _should_use_chunking(self, combined_text: str) -> bool:
        """Determine if text needs chunking based on length"""
        return len(combined_text) > self.max_single_analysis_length

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks for LLM processing"""
        if not text or len(text) <= self.max_chunk_length:
            return [text] if text else []
        
        # Split by sentences first to maintain context
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed chunk limit
            if len(current_chunk) + len(sentence) + 2 > self.max_chunk_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk += sentence + ". "
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from LLM response with multiple strategies"""
        if not response:
            return None
        
        try:
            # Strategy 1: Clean and parse directly
            cleaned = response.strip()
            
            # Remove common prefixes/suffixes
            for prefix in ['```json', '```', 'json', 'JSON']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            
            for suffix in ['```', '`']:
                if cleaned.endswith(suffix):
                    cleaned = cleaned[:-len(suffix)].strip()
            
            # Strategy 2: Find JSON boundaries
            start_idx = cleaned.find('{')
            if start_idx == -1:
                return None
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(cleaned)):
                if cleaned[i] == '{':
                    brace_count += 1
                elif cleaned[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count == 0:
                json_str = cleaned[start_idx:end_idx + 1]
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        logger.debug("Successfully extracted JSON from LLM response")
                        return parsed
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {str(e)}")
            
            # Strategy 3: Regex-based extraction
            json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
            matches = re.findall(json_pattern, cleaned, re.DOTALL)
            
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, dict) and len(parsed) > 3:  # Reasonable size
                        logger.debug("JSON extracted via regex")
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            logger.warning(f"JSON extraction error: {str(e)}")
        
        logger.warning("Failed to extract valid JSON from LLM response")
        return None

    def _calculate_dynamic_confidence(self, text: str, sentiment_label: str, emotion: str, analysis_type: str = "sentiment") -> float:
        """Calculate dynamic confidence based on actual text analysis factors"""
        
        confidence_factors = []
        text_lower = text.lower()
        
        # Factor 1: Keyword strength and clarity
        strong_positive = ["excellent", "wonderful", "amazing", "fantastic", "love", "perfect"]
        strong_negative = ["terrible", "awful", "horrible", "hate", "worst", "disgusting"]
        moderate_positive = ["good", "nice", "happy", "satisfied", "pleased", "glad"]
        moderate_negative = ["bad", "poor", "disappointed", "frustrated", "upset", "worried"]
        
        strong_pos_count = sum(1 for word in strong_positive if word in text_lower)
        strong_neg_count = sum(1 for word in strong_negative if word in text_lower)
        mod_pos_count = sum(1 for word in moderate_positive if word in text_lower)
        mod_neg_count = sum(1 for word in moderate_negative if word in text_lower)
        
        # Calculate keyword strength factor
        total_strong = strong_pos_count + strong_neg_count
        total_moderate = mod_pos_count + mod_neg_count
        
        if total_strong >= 2:
            confidence_factors.append(0.9)  # Very strong indicators
        elif total_strong >= 1:
            confidence_factors.append(0.8)  # Strong indicators
        elif total_moderate >= 2:
            confidence_factors.append(0.7)  # Moderate indicators
        elif total_moderate >= 1:
            confidence_factors.append(0.6)  # Some indicators
        else:
            confidence_factors.append(0.4)  # Weak indicators
        
        # Factor 2: Text length and context
        if len(text) > 100:
            confidence_factors.append(0.8)  # More context = higher confidence
        elif len(text) > 50:
            confidence_factors.append(0.7)
        elif len(text) > 20:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)  # Very short text = lower confidence
        
        # Factor 3: Consistency check (conflicting signals reduce confidence)
        if sentiment_label == "positive" and (strong_neg_count > 0 or mod_neg_count > strong_pos_count + mod_pos_count):
            confidence_factors.append(0.3)  # Conflicting signals
        elif sentiment_label == "negative" and (strong_pos_count > 0 or mod_pos_count > strong_neg_count + mod_neg_count):
            confidence_factors.append(0.3)  # Conflicting signals
        else:
            confidence_factors.append(0.8)  # Consistent signals
        
        # Factor 4: Dental-specific context boost
        dental_keywords = ["insurance", "medicaid", "ppo", "pain", "tooth", "dental", "appointment", "coverage"]
        dental_count = sum(1 for word in dental_keywords if word in text_lower)
        
        if dental_count >= 2:
            confidence_factors.append(0.8)  # Strong dental context
        elif dental_count >= 1:
            confidence_factors.append(0.7)  # Some dental context
        else:
            confidence_factors.append(0.6)  # General context
        
        # Factor 5: Emotion-specific adjustments
        if analysis_type == "emotion":
            emotion_keywords = {
                "anger": ["angry", "mad", "furious", "rage"],
                "fear": ["scared", "afraid", "nervous", "worried", "anxiety"],
                "joy": ["happy", "excited", "thrilled", "delighted"],
                "sadness": ["sad", "depressed", "down", "unhappy"],
                "disappointment": ["disappointed", "let down", "unfortunate"]
            }
            
            emotion_indicators = emotion_keywords.get(emotion, [])
            emotion_count = sum(1 for word in emotion_indicators if word in text_lower)
            
            if emotion_count >= 2:
                confidence_factors.append(0.9)
            elif emotion_count >= 1:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.5)
        
        # Calculate final confidence as weighted average
        if confidence_factors:
            base_confidence = sum(confidence_factors) / len(confidence_factors)
            
            # Apply bounds and slight randomization to avoid identical scores
            final_confidence = max(0.15, min(0.95, base_confidence))
            
            # Add small variation to avoid identical scores (±0.05)
            import random
            variation = random.uniform(-0.03, 0.03)
            final_confidence = max(0.15, min(0.95, final_confidence + variation))
            
            return round(final_confidence, 3)
        else:
            return 0.5  # Default moderate confidence

    async def analyze_call_segments_sentiment(self, patient_text: str, staff_text: str) -> Dict:
        """
        Analyze sentiment and emotions for patient and staff segments with intelligent chunking
        """
        try:
            logger.info("Starting improved LLM-based sentiment analysis...")
            
            if not self.is_initialized:
                logger.warning("LLM not initialized, using fallback analysis")
                return await self._fallback_sentiment_analysis(patient_text, staff_text)
            
            # Clean and prepare texts
            patient_text = patient_text.strip()[:2000]  # Limit length
            staff_text = staff_text.strip()[:2000]
            
            # Combine texts to check if chunking is needed
            combined_text = f"PATIENT: {patient_text}\n\nSTAFF: {staff_text}"
            
            # Decision: Use chunking only if text is long enough
            if self._should_use_chunking(combined_text):
                logger.info(f"Text is long ({len(combined_text)} chars), using chunking approach")
                return await self._analyze_with_chunking(patient_text, staff_text, combined_text)
            else:
                logger.info(f"Text is short ({len(combined_text)} chars), using direct analysis")
                return await self._analyze_directly(patient_text, staff_text)
                
        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {str(e)}")
            return await self._fallback_sentiment_analysis(patient_text, staff_text)

    async def _analyze_directly(self, patient_text: str, staff_text: str) -> Dict:
        """Analyze short texts directly without chunking"""
        try:
            prompt = self.simple_sentiment_prompt.format(
                patient_text=patient_text,
                staff_text=staff_text
            )
            
            logger.debug("Sending prompt to LLM for direct analysis")
            response = await self._generate_llm_response(prompt, max_tokens=1200)
            
            if response:
                logger.debug(f"Received LLM response: {response[:200]}...")
                parsed_result = self._extract_json_from_response(response)
                if parsed_result:
                    validated_result = self._validate_final_result(parsed_result)
                    logger.info("Direct LLM analysis completed successfully")
                    return validated_result
                else:
                    logger.warning("Failed to parse LLM JSON response")
            else:
                logger.warning("Empty response from LLM")
            
            # If parsing failed, create enhanced manual analysis
            logger.info("LLM parsing failed, using enhanced manual analysis")
            return self._create_enhanced_manual_analysis(patient_text, staff_text)
            
        except Exception as e:
            logger.error(f"Direct analysis error: {str(e)}")
            return self._create_enhanced_manual_analysis(patient_text, staff_text)

    async def _analyze_with_chunking(self, patient_text: str, staff_text: str, combined_text: str) -> Dict:
        """Analyze long texts using chunking approach"""
        try:
            # Split into chunks
            chunks = self._split_text_into_chunks(combined_text)
            logger.info(f"Split text into {len(chunks)} chunks for analysis")
            
            # Analyze each chunk
            chunk_results = []
            for i, chunk in enumerate(chunks, 1):
                context_info = f"Previous {i-1} chunks analyzed" if i > 1 else "First chunk"
                chunk_result = await self._analyze_chunk(chunk, i, len(chunks), context_info)
                chunk_results.append(chunk_result)
                
                # Brief pause between chunks
                await asyncio.sleep(0.3)
            
            # Generate final aggregated analysis
            final_result = await self._generate_final_analysis(
                chunk_results, patient_text, staff_text
            )
            
            logger.info("LLM chunked sentiment analysis completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Chunked analysis error: {str(e)}")
            return self._create_enhanced_manual_analysis(patient_text, staff_text)

    async def _analyze_chunk(self, chunk_text: str, chunk_num: int, total_chunks: int, context_info: str = "") -> Dict:
        """Analyze sentiment and emotions for a single chunk"""
        try:
            prompt = self.sentiment_chunk_prompt.format(
                text=chunk_text,
                chunk_num=chunk_num,
                total_chunks=total_chunks,
                context_info=context_info
            )
            
            response = await self._generate_llm_response(prompt, max_tokens=600)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and isinstance(parsed_result, dict):
                    return parsed_result
            
            # Fallback result
            return self._create_fallback_chunk_result(chunk_text)
            
        except Exception as e:
            logger.warning(f"Error analyzing chunk {chunk_num}: {str(e)}")
            return self._create_fallback_chunk_result(chunk_text)

    def _create_fallback_chunk_result(self, text: str) -> Dict:
        """Create fallback result for chunk analysis with dynamic confidence"""
        text_lower = text.lower()
        
        # Enhanced keyword detection
        pain_keywords = ["pain", "hurt", "ache", "sore", "painful", "hurting"]
        anxiety_keywords = ["nervous", "scared", "worried", "anxiety", "afraid", "concerned"]
        satisfaction_keywords = ["happy", "satisfied", "pleased", "great", "wonderful", "excellent"]
        insurance_keywords = ["insurance", "coverage", "medicaid", "blue cross", "ppo", "covered"]
        
        sentiment_label = self._determine_keyword_sentiment(text_lower)
        primary_emotion = self._determine_primary_emotion(text_lower)
        
        # Calculate dynamic confidence
        confidence = self._calculate_dynamic_confidence(text, sentiment_label, primary_emotion)
        
        return {
            "sentiment": {
                "label": sentiment_label,
                "confidence": confidence,
                "reasoning": "Keyword-based analysis with dynamic confidence"
            },
            "emotions": {
                "primary_emotion": primary_emotion,
                "intensity": self._determine_intensity(text_lower),
                "dental_specific": {
                    "pain_detected": any(word in text_lower for word in pain_keywords),
                    "anxiety_detected": any(word in text_lower for word in anxiety_keywords),
                    "satisfaction_detected": any(word in text_lower for word in satisfaction_keywords),
                    "insurance_concern": any(word in text_lower for word in insurance_keywords)
                }
            },
            "key_indicators": self._extract_key_indicators(text_lower)
        }

    def _determine_keyword_sentiment(self, text: str) -> str:
        """Determine sentiment based on keywords"""
        positive_count = sum(1 for word in ["happy", "satisfied", "pleased", "great", "excellent", "wonderful", "good", "thank you"] if word in text)
        negative_count = sum(1 for word in ["pain", "hurt", "terrible", "awful", "bad", "angry", "frustrated", "worried", "can't", "don't"] if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _determine_primary_emotion(self, text: str) -> str:
        """Determine primary emotion from text"""
        if any(word in text for word in ["pain", "hurt", "ache"]):
            return "fear"
        elif any(word in text for word in ["nervous", "scared", "worried", "anxiety"]):
            return "fear"
        elif any(word in text for word in ["happy", "satisfied", "pleased"]):
            return "joy"
        elif any(word in text for word in ["angry", "frustrated", "terrible"]):
            return "anger"
        elif any(word in text for word in ["unfortunately", "can't", "don't take", "not covered"]):
            return "disappointment"
        else:
            return "neutral"

    def _determine_intensity(self, text: str) -> str:
        """Determine emotion intensity"""
        high_intensity_words = ["terrible", "awful", "severe", "extremely", "very", "really"]
        medium_intensity_words = ["worried", "concerned", "disappointed", "frustrated"]
        
        if any(word in text for word in high_intensity_words):
            return "high"
        elif any(word in text for word in medium_intensity_words):
            return "medium"
        else:
            return "low"

    def _extract_key_indicators(self, text: str) -> List[str]:
        """Extract key indicator words"""
        indicators = []
        key_words = ["pain", "insurance", "medicaid", "worried", "thank", "sorry", "help", "coverage"]
        
        for word in key_words:
            if word in text:
                indicators.append(word)
        
        return indicators[:5]  # Limit to 5 indicators

    async def _generate_final_analysis(self, chunk_results: List[Dict], patient_text: str, staff_text: str) -> Dict:
        """Generate final aggregated analysis from all chunks"""
        try:
            # Create simplified summary for LLM
            simplified_results = []
            for i, result in enumerate(chunk_results, 1):
                simplified = {
                    "chunk": i,
                    "sentiment": result.get("sentiment", {}).get("label", "neutral"),
                    "emotion": result.get("emotions", {}).get("primary_emotion", "neutral"),
                    "key_words": result.get("key_indicators", [])
                }
                simplified_results.append(simplified)
            
            prompt = self.final_analysis_prompt.format(
                chunk_count=len(chunk_results),
                chunk_results=json.dumps(simplified_results, indent=2),
                patient_length=len(patient_text),
                staff_length=len(staff_text)
            )
            
            response = await self._generate_llm_response(prompt, max_tokens=1200)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result:
                    return self._validate_final_result(parsed_result)
            
            # Fallback to manual aggregation
            return self._manual_chunk_aggregation(chunk_results, patient_text, staff_text)
            
        except Exception as e:
            logger.warning(f"Error generating final analysis: {str(e)}")
            return self._manual_chunk_aggregation(chunk_results, patient_text, staff_text)

    def _validate_final_result(self, result: Dict) -> Dict:
        """Validate and ensure final result has proper structure with dynamic confidence"""
        # Ensure all required keys exist with defaults
        patient_sentiment = result.get("patient_sentiment", {})
        staff_sentiment = result.get("staff_sentiment", {})
        overall_sentiment = result.get("overall_sentiment", {})
        emotion_analysis = result.get("emotion_analysis", {})
        
        # Get LLM-provided confidence or calculate dynamic fallback
        patient_conf = patient_sentiment.get("confidence")
        if patient_conf is None or not isinstance(patient_conf, (int, float)) or patient_conf <= 0:
            patient_conf = 0.6  # Default fallback
        
        staff_conf = staff_sentiment.get("confidence")
        if staff_conf is None or not isinstance(staff_conf, (int, float)) or staff_conf <= 0:
            staff_conf = 0.6  # Default fallback
            
        overall_conf = overall_sentiment.get("confidence")
        if overall_conf is None or not isinstance(overall_conf, (int, float)) or overall_conf <= 0:
            overall_conf = 0.6  # Default fallback
        
        # Get emotion confidence
        patient_emotions = emotion_analysis.get("patient_emotions", {})
        primary_emotion = patient_emotions.get("primary_emotion", {})
        emotion_conf = primary_emotion.get("confidence")
        if emotion_conf is None or not isinstance(emotion_conf, (int, float)) or emotion_conf <= 0:
            emotion_conf = 0.6  # Default fallback
        
        staff_emotions = emotion_analysis.get("staff_emotions", {})
        staff_primary_emotion = staff_emotions.get("primary_emotion", {})
        staff_emotion_conf = staff_primary_emotion.get("confidence")
        if staff_emotion_conf is None or not isinstance(staff_emotion_conf, (int, float)) or staff_emotion_conf <= 0:
            staff_emotion_conf = 0.6  # Default fallback
        
        validated_result = {
            "patient_sentiment": {
                "sentiment_label": patient_sentiment.get("sentiment_label", "neutral"),
                "confidence": min(max(float(patient_conf), 0.1), 1.0)
            },
            "staff_sentiment": {
                "sentiment_label": staff_sentiment.get("sentiment_label", "neutral"),
                "confidence": min(max(float(staff_conf), 0.1), 1.0)
            },
            "overall_sentiment": {
                "sentiment_label": overall_sentiment.get("sentiment_label", "neutral"),
                "confidence": min(max(float(overall_conf), 0.1), 1.0)
            },
            "emotion_analysis": {
                "patient_emotions": {
                    "primary_emotion": {
                        "emotion": primary_emotion.get("emotion", "neutral"),
                        "confidence": min(max(float(emotion_conf), 0.1), 1.0)
                    },
                    "intensity": patient_emotions.get("intensity", "low"),
                    "dental_specific": patient_emotions.get("dental_specific", {
                        "pain_detected": False,
                        "anxiety_detected": False,
                        "satisfaction_detected": False,
                        "insurance_concern": False,
                        "disappointment_detected": False
                    })
                },
                "staff_emotions": {
                    "primary_emotion": {
                        "emotion": staff_primary_emotion.get("emotion", "neutral"),
                        "confidence": min(max(float(staff_emotion_conf), 0.1), 1.0)
                    },
                    "intensity": staff_emotions.get("intensity", "low")
                },
                "emotion_flags": emotion_analysis.get("emotion_flags", []),
                "call_dynamics": {
                    "call_emotional_health": {"health_level": emotion_analysis.get("call_dynamics", {}).get("call_emotional_health", {}).get("health_level", "fair")},
                    "emotional_alignment": {"is_aligned": emotion_analysis.get("call_dynamics", {}).get("emotional_alignment", {}).get("is_aligned", True)},
                    "escalation_pattern": {"pattern": emotion_analysis.get("call_dynamics", {}).get("escalation_pattern", {}).get("pattern", "none")}
                }
            },
            "sentiment_summary": result.get("sentiment_summary", "Analysis completed with dynamic confidence scoring")
        }
        
        return validated_result

    def _create_enhanced_manual_analysis(self, patient_text: str, staff_text: str) -> Dict:
        """Create enhanced manual analysis with dynamic confidence scoring"""
        patient_lower = patient_text.lower()
        staff_lower = staff_text.lower()
        
        # Enhanced analysis for dental context
        insurance_inquiry = any(word in patient_lower for word in ["insurance", "medicaid", "blue cross", "coverage", "take", "accept"])
        insurance_denial = any(phrase in staff_lower for phrase in ["only take ppo", "don't take", "not covered", "only accept"])
        professional_response = any(word in staff_lower for word in ["understand", "help", "welcome", "thank"])
        
        # Determine patient sentiment
        if insurance_inquiry and insurance_denial:
            patient_sentiment_label = "neutral"
            patient_emotion = "disappointment"
            emotion_flags = ["INSURANCE_ISSUE"]
        else:
            patient_sentiment_label = "neutral"
            patient_emotion = "neutral"
            emotion_flags = []
        
        # Calculate dynamic confidence for patient sentiment
        patient_conf = self._calculate_dynamic_confidence(patient_text, patient_sentiment_label, patient_emotion, "sentiment")
        
        # Determine staff sentiment
        if professional_response:
            staff_sentiment_label = "positive"
            staff_emotion = "professional"
            staff_conf = self._calculate_dynamic_confidence(staff_text, staff_sentiment_label, staff_emotion, "sentiment")
        else:
            staff_sentiment_label = "neutral"
            staff_emotion = "neutral"
            staff_conf = self._calculate_dynamic_confidence(staff_text, staff_sentiment_label, staff_emotion, "sentiment")
        
        # Overall sentiment with dynamic confidence
        if professional_response and not any(word in patient_lower for word in ["angry", "frustrated", "terrible"]):
            overall_sentiment_label = "positive"
        else:
            overall_sentiment_label = "neutral"
        
        combined_text = patient_text + " " + staff_text
        overall_conf = self._calculate_dynamic_confidence(combined_text, overall_sentiment_label, "neutral", "sentiment")
        
        # Calculate emotion confidence
        emotion_conf = self._calculate_dynamic_confidence(patient_text, patient_sentiment_label, patient_emotion, "emotion")
        staff_emotion_conf = self._calculate_dynamic_confidence(staff_text, staff_sentiment_label, staff_emotion, "emotion")
        
        # Detailed summary
        if insurance_inquiry and insurance_denial:
            summary = "Insurance inquiry call - Patient asked about coverage, staff professionally explained services not covered under patient's plan"
        else:
            summary = f"Professional call interaction - Patient: {patient_sentiment_label}, Staff: {staff_sentiment_label}"
        
        return {
            "patient_sentiment": {
                "sentiment_label": patient_sentiment_label,
                "confidence": patient_conf
            },
            "staff_sentiment": {
                "sentiment_label": staff_sentiment_label,
                "confidence": staff_conf
            },
            "overall_sentiment": {
                "sentiment_label": overall_sentiment_label,
                "confidence": overall_conf
            },
            "emotion_analysis": {
                "patient_emotions": {
                    "primary_emotion": {"emotion": patient_emotion, "confidence": emotion_conf},
                    "intensity": "medium" if insurance_denial else "low",
                    "dental_specific": {
                        "pain_detected": any(word in patient_lower for word in ["pain", "hurt", "ache", "sore"]),
                        "anxiety_detected": any(word in patient_lower for word in ["nervous", "scared", "worried", "anxiety"]),
                        "satisfaction_detected": any(word in patient_lower for word in ["happy", "satisfied", "pleased", "thank"]),
                        "insurance_concern": insurance_inquiry,
                        "disappointment_detected": insurance_denial and insurance_inquiry
                    }
                },
                "staff_emotions": {
                    "primary_emotion": {"emotion": staff_emotion, "confidence": staff_emotion_conf},
                    "intensity": "low"
                },
                "emotion_flags": emotion_flags,
                "call_dynamics": {
                    "call_emotional_health": {"health_level": "good" if professional_response else "fair"},
                    "emotional_alignment": {"is_aligned": professional_response},
                    "escalation_pattern": {"pattern": "none"}
                }
            },
            "sentiment_summary": summary
        }

    def _manual_chunk_aggregation(self, chunk_results: List[Dict], patient_text: str, staff_text: str) -> Dict:
        """Manually aggregate chunk results with dynamic confidence"""
        if not chunk_results:
            return self._create_enhanced_manual_analysis(patient_text, staff_text)
        
        # Aggregate data from all chunks
        all_sentiments = []
        all_emotions = []
        detected_flags = set()
        confidence_scores = []
        
        for chunk in chunk_results:
            sentiment_data = chunk.get("sentiment", {})
            emotion_data = chunk.get("emotions", {})
            dental_specific = emotion_data.get("dental_specific", {})
            
            all_sentiments.append(sentiment_data.get("label", "neutral"))
            all_emotions.append(emotion_data.get("primary_emotion", "neutral"))
            confidence_scores.append(sentiment_data.get("confidence", 0.5))
            
            # Collect detected conditions
            if dental_specific.get("pain_detected", False):
                detected_flags.add("PAIN")
            if dental_specific.get("anxiety_detected", False):
                detected_flags.add("ANXIETY")
            if dental_specific.get("satisfaction_detected", False):
                detected_flags.add("SATISFACTION")
            if dental_specific.get("insurance_concern", False):
                detected_flags.add("INSURANCE_ISSUE")
        
        # Determine most common patterns
        most_common_sentiment = max(set(all_sentiments), key=all_sentiments.count) if all_sentiments else "neutral"
        most_common_emotion = max(set(all_emotions), key=all_emotions.count) if all_emotions else "neutral"
        
        # Calculate aggregate confidence (average of chunk confidences)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Adjust confidence based on consistency
        sentiment_consistency = all_sentiments.count(most_common_sentiment) / len(all_sentiments) if all_sentiments else 1.0
        final_confidence = avg_confidence * sentiment_consistency
        final_confidence = max(0.2, min(0.95, final_confidence))  # Bound confidence
        
        # Determine intensity based on detected conditions
        if "PAIN" in detected_flags:
            intensity = "high"
        elif "ANXIETY" in detected_flags or "INSURANCE_ISSUE" in detected_flags:
            intensity = "medium"
        else:
            intensity = "low"
        
        # Generate summary
        conditions = list(detected_flags)
        if conditions:
            summary = f"Multi-chunk analysis detected: {', '.join(conditions).lower().replace('_', ' ')} - Overall sentiment: {most_common_sentiment}"
        else:
            summary = f"Multi-chunk analysis completed - Overall sentiment: {most_common_sentiment}"
        
        # Calculate emotion confidence
        emotion_conf = self._calculate_dynamic_confidence(patient_text, most_common_sentiment, most_common_emotion, "emotion")
        staff_emotion_conf = self._calculate_dynamic_confidence(staff_text, "neutral", "professional", "emotion")
        
        return {
            "patient_sentiment": {
                "sentiment_label": most_common_sentiment,
                "confidence": round(final_confidence, 3)
            },
            "staff_sentiment": {
                "sentiment_label": "positive" if "SATISFACTION" in detected_flags else "neutral", 
                "confidence": round(max(0.6, final_confidence * 0.9), 3)
            },
            "overall_sentiment": {
                "sentiment_label": most_common_sentiment,
                "confidence": round(final_confidence, 3)
            },
            "emotion_analysis": {
                "patient_emotions": {
                    "primary_emotion": {"emotion": most_common_emotion, "confidence": round(emotion_conf, 3)},
                    "intensity": intensity,
                    "dental_specific": {
                        "pain_detected": "PAIN" in detected_flags,
                        "anxiety_detected": "ANXIETY" in detected_flags,
                        "satisfaction_detected": "SATISFACTION" in detected_flags,
                        "insurance_concern": "INSURANCE_ISSUE" in detected_flags,
                        "disappointment_detected": "INSURANCE_ISSUE" in detected_flags and most_common_sentiment == "negative"
                    }
                },
                "staff_emotions": {
                    "primary_emotion": {"emotion": "professional", "confidence": round(staff_emotion_conf, 3)},
                    "intensity": "low"
                },
                "emotion_flags": list(detected_flags),
                "call_dynamics": {
                    "call_emotional_health": {"health_level": "poor" if "PAIN" in detected_flags else ("fair" if detected_flags else "good")},
                    "emotional_alignment": {"is_aligned": most_common_sentiment != "negative"},
                    "escalation_pattern": {"pattern": "escalating" if "PAIN" in detected_flags and "ANXIETY" in detected_flags else "none"}
                }
            },
            "sentiment_summary": summary
        }

    async def _fallback_sentiment_analysis(self, patient_text: str, staff_text: str) -> Dict:
        """Fallback sentiment analysis using enhanced keyword approach with dynamic confidence"""
        logger.warning("Using enhanced fallback sentiment analysis with dynamic confidence")
        return self._create_enhanced_manual_analysis(patient_text, staff_text)

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
        logger.info("LLM sentiment analysis service cleaned up")