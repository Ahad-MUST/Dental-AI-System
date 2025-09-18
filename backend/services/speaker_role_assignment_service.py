"""
LLM-based Speaker Role Assignment Service - WITH CHUNKING SUPPORT
Intelligently assigns staff/patient roles using LLM analysis instead of hardcoded assumptions
"""
import logging
import asyncio
import json
from typing import Dict, List, Tuple
from prompts.speaker_role_prompts import SpeakerRolePrompts

logger = logging.getLogger(__name__)

class SpeakerRoleAssignmentService:
    """LLM-based service to assign staff/patient roles to speakers with chunking support"""
    
    def __init__(self, llm_analyzer=None):
        self.llm_analyzer = llm_analyzer
        
        # Initialize prompts from separate file
        self.prompts = SpeakerRolePrompts()
        
        # Chunking configuration for long transcripts
        self.max_single_analysis_length = 2500  # Characters - analyze without chunking
        self.max_chunk_length = 2000  # Characters per chunk for chunking
        
        # Fallback patterns for when LLM fails
        self.staff_patterns = [
            "thank you for calling", "how can i help", "how can we help", 
            "this is", "my name is", "dental office", "schedule", "appointment",
            "we accept", "our hours", "let me check", "i can help", "we offer"
        ]
        
        self.patient_patterns = [
            "i need", "i want", "i have", "my tooth", "pain", "hurt", 
            "insurance", "cost", "price", "how much", "do you take",
            "appointment", "schedule me", "book me"
        ]
        
        self.automated_patterns = [
            "this call may be recorded", "for quality", "training purposes",
            "please hold", "your call is important"
        ]
    
    async def assign_speaker_roles(self, combined_transcript: Dict) -> Tuple[str, str]:
        """
        Assign staff and patient roles to speakers using LLM analysis with chunking support
        
        Args:
            combined_transcript: Dict with segments containing speaker, text, timestamps
            
        Returns:
            Tuple of (patient_text, staff_text) 
        """
        try:
            segments = combined_transcript.get("segments", [])
            if not segments:
                logger.warning("No segments found in transcript")
                return "", ""
            
            # Create transcript with speaker labels for analysis
            transcript_with_speakers = self._create_transcript_with_speakers(segments)
            
            # Check if chunking is needed for long transcripts
            if self._should_use_chunking(transcript_with_speakers):
                logger.info(f"Long transcript detected ({len(transcript_with_speakers)} chars), using chunking for speaker role analysis")
                role_assignments = await self._analyze_with_chunking(segments)
            else:
                logger.info(f"Standard transcript length ({len(transcript_with_speakers)} chars), using direct analysis")
                role_assignments = await self._analyze_directly(transcript_with_speakers, segments)
            
            # Separate text based on role assignments
            patient_text, staff_text = self._separate_text_by_roles(segments, role_assignments)
            
            logger.info(f"Speaker roles assigned - Staff: {role_assignments.get('staff_speaker', 'unknown')}, "
                       f"Patient: {role_assignments.get('patient_speaker', 'unknown')}")
            
            return patient_text, staff_text
            
        except Exception as e:
            logger.error(f"Speaker role assignment failed: {str(e)}")
            # Fallback to enhanced rule-based assignment
            return self._fallback_speaker_assignment(segments)
    
    def _should_use_chunking(self, transcript: str) -> bool:
        """Determine if chunking is needed based on transcript length"""
        return len(transcript) > self.max_single_analysis_length
    
    def _create_transcript_with_speakers(self, segments: List[Dict]) -> str:
        """Create a formatted transcript showing speaker labels and text"""
        transcript_lines = []
        
        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            start_time = segment.get("start_time", 0)
            
            if text:  # Only include segments with actual text
                # Format: [MM:SS] SPEAKER_XX: text
                time_formatted = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
                transcript_lines.append(f"[{time_formatted}] {speaker}: {text}")
        
        return "\n".join(transcript_lines)
    
    async def _analyze_directly(self, transcript_with_speakers: str, segments: List[Dict]) -> Dict:
        """Analyze short transcripts directly without chunking"""
        try:
            if not self.llm_analyzer or not self.llm_analyzer.is_initialized:
                logger.info("LLM not available, using enhanced rule-based analysis")
                return self._rule_based_role_assignment(segments)
            
            prompt = self.prompts.SPEAKER_ROLE_ANALYSIS_PROMPT.format(
                transcript_with_speakers=transcript_with_speakers
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=600)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and self._validate_multi_speaker_assignment(parsed_result, segments):
                    # Convert multi-speaker result to single staff/patient assignment
                    converted_result = self._convert_multi_speaker_to_binary(parsed_result)
                    logger.info("Direct LLM role analysis completed successfully")
                    return converted_result
                else:
                    logger.warning("LLM multi-speaker assignment invalid, using rule-based fallback")
            else:
                logger.warning("Empty LLM response for role assignment")
            
            # Fallback to rule-based
            return self._rule_based_role_assignment(segments)
            
        except Exception as e:
            logger.error(f"Direct role analysis failed: {str(e)}")
            return self._rule_based_role_assignment(segments)
    
    def _validate_multi_speaker_assignment(self, assignment: Dict, segments: List[Dict]) -> bool:
        """Validate multi-speaker assignment"""
        try:
            speakers_in_transcript = set(segment.get("speaker") for segment in segments)
            
            staff_speakers = assignment.get("staff_speakers", [])
            patient_speakers = assignment.get("patient_speakers", [])
            
            # Must have at least one staff and one patient
            if not staff_speakers or not patient_speakers:
                return False
            
            # All assigned speakers must exist in transcript
            all_assigned = staff_speakers + patient_speakers + assignment.get("automated_speakers", [])
            for speaker in all_assigned:
                if speaker and speaker not in speakers_in_transcript:
                    return False
            
            # Staff and patient lists must not overlap
            if set(staff_speakers) & set(patient_speakers):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _convert_multi_speaker_to_binary(self, multi_assignment: Dict) -> Dict:
        """Convert multi-speaker assignment to single staff/patient format"""
        try:
            staff_speakers = multi_assignment.get("staff_speakers", [])
            patient_speakers = multi_assignment.get("patient_speakers", [])
            automated_speakers = multi_assignment.get("automated_speakers", [])
            
            # Use first speaker from each list as primary
            staff_speaker = staff_speakers[0] if staff_speakers else None
            patient_speaker = patient_speakers[0] if patient_speakers else None
            automated_speaker = automated_speakers[0] if automated_speakers else None
            
            # Store all speakers for text separation
            return {
                "staff_speaker": staff_speaker,
                "patient_speaker": patient_speaker,
                "automated_speaker": automated_speaker,
                "all_staff_speakers": staff_speakers,
                "all_patient_speakers": patient_speakers,
                "all_automated_speakers": automated_speakers,
                "confidence": multi_assignment.get("confidence", 0.5),
                "reasoning": multi_assignment.get("reasoning", "Multi-speaker assignment converted")
            }
            
        except Exception as e:
            logger.error(f"Error converting multi-speaker assignment: {str(e)}")
            return {
                "staff_speaker": None,
                "patient_speaker": None,
                "automated_speaker": None,
                "confidence": 0.3,
                "reasoning": "Conversion failed"
            }
    
    async def _analyze_with_chunking(self, segments: List[Dict]) -> Dict:
        """Analyze long transcripts using chunking approach"""
        try:
            # Split segments into chunks
            segment_chunks = self._split_segments_into_chunks(segments)
            logger.info(f"Split transcript into {len(segment_chunks)} chunks for role analysis")
            
            # Analyze each chunk
            chunk_results = []
            for i, chunk_segments in enumerate(segment_chunks, 1):
                context_info = f"Previous {i-1} chunks analyzed" if i > 1 else "First chunk"
                chunk_result = await self._analyze_chunk_roles(chunk_segments, i, len(segment_chunks), context_info)
                chunk_results.append(chunk_result)
                
                # Brief pause between chunks
                await asyncio.sleep(0.2)
            
            # Generate final role assignments from chunk analysis
            final_assignments = await self._generate_final_role_assignments(
                chunk_results, segments
            )
            
            logger.info("Chunked speaker role analysis completed successfully")
            return final_assignments
            
        except Exception as e:
            logger.error(f"Chunked role analysis failed: {str(e)}")
            return self._rule_based_role_assignment(segments)
    
    def _split_segments_into_chunks(self, segments: List[Dict]) -> List[List[Dict]]:
        """Split segments into chunks based on character length"""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for segment in segments:
            text = segment.get("text", "")
            segment_length = len(text)
            
            # If adding this segment would exceed chunk limit
            if current_length + segment_length > self.max_chunk_length and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [segment]
                current_length = segment_length
            else:
                current_chunk.append(segment)
                current_length += segment_length
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _analyze_chunk_roles(self, chunk_segments: List[Dict], chunk_num: int, 
                                  total_chunks: int, context_info: str) -> Dict:
        """Analyze speaker roles for a single chunk"""
        try:
            # Create transcript for this chunk
            transcript_chunk = self._create_transcript_with_speakers(chunk_segments)
            
            if not self.llm_analyzer or not self.llm_analyzer.is_initialized:
                return self._rule_based_chunk_analysis(chunk_segments)
            
            prompt = self.prompts.CHUNKED_ROLE_ANALYSIS_PROMPT.format(
                chunk_num=chunk_num,
                total_chunks=total_chunks,
                transcript_chunk=transcript_chunk,
                context_info=context_info
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=500)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and isinstance(parsed_result, dict):
                    return parsed_result
            
            # Fallback to rule-based chunk analysis
            return self._rule_based_chunk_analysis(chunk_segments)
            
        except Exception as e:
            logger.warning(f"Error analyzing chunk {chunk_num}: {str(e)}")
            return self._rule_based_chunk_analysis(chunk_segments)
    
    def _rule_based_chunk_analysis(self, chunk_segments: List[Dict]) -> Dict:
        """Rule-based analysis for a chunk when LLM fails"""
        speaker_behaviors = {}
        
        for segment in chunk_segments:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").lower()
            
            if speaker not in speaker_behaviors:
                speaker_behaviors[speaker] = {
                    "likely_role": "unknown",
                    "evidence": [],
                    "staff_score": 0,
                    "patient_score": 0,
                    "automated_score": 0
                }
            
            # Check for staff patterns
            for pattern in self.staff_patterns:
                if pattern in text:
                    speaker_behaviors[speaker]["staff_score"] += 1
                    speaker_behaviors[speaker]["evidence"].append(f"staff pattern: {pattern}")
            
            # Check for patient patterns
            for pattern in self.patient_patterns:
                if pattern in text:
                    speaker_behaviors[speaker]["patient_score"] += 1
                    speaker_behaviors[speaker]["evidence"].append(f"patient pattern: {pattern}")
            
            # Check for automated patterns
            for pattern in self.automated_patterns:
                if pattern in text:
                    speaker_behaviors[speaker]["automated_score"] += 2  # Higher weight
                    speaker_behaviors[speaker]["evidence"].append(f"automated pattern: {pattern}")
        
        # Determine likely roles based on scores
        for speaker, data in speaker_behaviors.items():
            if data["automated_score"] > 0:
                data["likely_role"] = "automated"
            elif data["staff_score"] > data["patient_score"]:
                data["likely_role"] = "staff"
            elif data["patient_score"] > data["staff_score"]:
                data["likely_role"] = "patient"
            else:
                data["likely_role"] = "unknown"
        
        return {
            "chunk_analysis": {
                "confidence_level": "medium",
                "key_indicators": ["rule-based pattern matching"]
            },
            "speaker_behaviors": speaker_behaviors
        }
    
    async def _generate_final_role_assignments(self, chunk_results: List[Dict], segments: List[Dict]) -> Dict:
        """Generate final role assignments from all chunk analyses"""
        try:
            if not self.llm_analyzer or not self.llm_analyzer.is_initialized:
                return self._aggregate_chunk_results_manually(chunk_results, segments)
            
            # Get unique speakers
            speakers_found = list(set(segment.get("speaker", "UNKNOWN") for segment in segments))
            
            # Prepare simplified chunk results for LLM
            simplified_results = []
            for i, result in enumerate(chunk_results, 1):
                simplified = {
                    "chunk": i,
                    "speaker_behaviors": result.get("speaker_behaviors", {}),
                    "confidence": result.get("chunk_analysis", {}).get("confidence_level", "unknown")
                }
                simplified_results.append(simplified)
            
            prompt = self.prompts.FINAL_ROLE_ASSIGNMENT_PROMPT.format(
                chunk_count=len(chunk_results),
                chunk_results=json.dumps(simplified_results, indent=2),
                speaker_count=len(speakers_found),
                speakers_list=speakers_found
            )
            
            response = await self.llm_analyzer.generate_response(prompt, max_tokens=600)
            
            if response:
                parsed_result = self._extract_json_from_response(response)
                if parsed_result and self._validate_role_assignment(parsed_result, segments):
                    final_assignments = parsed_result.get("final_assignments", {})
                    logger.info("Final LLM role assignments completed")
                    return final_assignments
            
            # Fallback to manual aggregation
            return self._aggregate_chunk_results_manually(chunk_results, segments)
            
        except Exception as e:
            logger.warning(f"Error generating final role assignments: {str(e)}")
            return self._aggregate_chunk_results_manually(chunk_results, segments)
    
    def _aggregate_chunk_results_manually(self, chunk_results: List[Dict], segments: List[Dict]) -> Dict:
        """Manually aggregate chunk results when LLM fails"""
        speaker_votes = {}
        speakers_found = list(set(segment.get("speaker", "UNKNOWN") for segment in segments))
        
        # Initialize vote counts
        for speaker in speakers_found:
            speaker_votes[speaker] = {"staff": 0, "patient": 0, "automated": 0}
        
        # Count votes from each chunk
        for result in chunk_results:
            speaker_behaviors = result.get("speaker_behaviors", {})
            for speaker, data in speaker_behaviors.items():
                if speaker in speaker_votes:
                    likely_role = data.get("likely_role", "unknown")
                    if likely_role in speaker_votes[speaker]:
                        speaker_votes[speaker][likely_role] += 1
        
        # Determine final assignments based on majority votes
        staff_speaker = None
        patient_speaker = None
        automated_speaker = None
        
        for speaker, votes in speaker_votes.items():
            max_vote = max(votes.values())
            if max_vote > 0:
                winning_role = max(votes, key=votes.get)
                if winning_role == "staff" and staff_speaker is None:
                    staff_speaker = speaker
                elif winning_role == "patient" and patient_speaker is None:
                    patient_speaker = speaker
                elif winning_role == "automated" and automated_speaker is None:
                    automated_speaker = speaker
        
        # Ensure we have at least staff and patient assignments
        if staff_speaker is None or patient_speaker is None:
            # Fallback to original hardcoded logic as last resort
            return self._final_fallback_assignment(segments)
        
        return {
            "staff_speaker": staff_speaker,
            "patient_speaker": patient_speaker,
            "automated_speaker": automated_speaker,
            "confidence": 0.6,  # Moderate confidence for manual aggregation
            "reasoning": "Manual aggregation of chunk analysis votes"
        }
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            # Find JSON boundaries
            start_idx = response.find('{')
            if start_idx == -1:
                return {}
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count == 0:
                json_str = response[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    logger.debug("Successfully extracted JSON from speaker role response")
                    return parsed
        
        except Exception as e:
            logger.warning(f"JSON extraction failed in speaker role analysis: {str(e)}")
        
        return {}
    
    def _validate_role_assignment(self, assignment: Dict, segments: List[Dict]) -> bool:
        """Validate that role assignment makes sense"""
        try:
            speakers_in_transcript = set(segment.get("speaker") for segment in segments)
            
            staff_speaker = assignment.get("staff_speaker")
            patient_speaker = assignment.get("patient_speaker")
            
            # Must have both staff and patient
            if not staff_speaker or not patient_speaker:
                return False
            
            # Speakers must exist in transcript
            if staff_speaker not in speakers_in_transcript or patient_speaker not in speakers_in_transcript:
                return False
            
            # Staff and patient must be different
            if staff_speaker == patient_speaker:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _rule_based_role_assignment(self, segments: List[Dict]) -> Dict:
        """Enhanced rule-based role assignment as fallback"""
        speaker_scores = {}
        
        # Enhanced patterns for dental office calls
        strong_staff_patterns = [
            "thank you for calling", "this is", "how can i help", "how can we help",
            "lincoln wood family dental", "dental office", "let me check", "i can schedule",
            "we have available", "you're scheduled", "have a good day", "you're welcome"
        ]
        
        strong_patient_patterns = [
            "my name is", "i have an appointment", "i need to", "i want to", 
            "can you", "do you have", "what about", "that works", "perfect",
            "thank you so much", "i can do"
        ]
        
        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").lower()
            
            if speaker not in speaker_scores:
                speaker_scores[speaker] = {
                    "staff_score": 0,
                    "patient_score": 0, 
                    "automated_score": 0,
                    "word_count": 0,
                    "evidence": []
                }
            
            speaker_scores[speaker]["word_count"] += len(text.split())
            
            # Score based on strong patterns first
            for pattern in strong_staff_patterns:
                if pattern in text:
                    speaker_scores[speaker]["staff_score"] += 3  # Higher weight for strong patterns
                    speaker_scores[speaker]["evidence"].append(f"staff: {pattern}")
            
            for pattern in strong_patient_patterns:
                if pattern in text:
                    speaker_scores[speaker]["patient_score"] += 3
                    speaker_scores[speaker]["evidence"].append(f"patient: {pattern}")
            
            # Check for automated patterns
            for pattern in self.automated_patterns:
                if pattern in text:
                    speaker_scores[speaker]["automated_score"] += 5
                    speaker_scores[speaker]["evidence"].append(f"automated: {pattern}")
            
            # Weaker general patterns
            for pattern in self.staff_patterns:
                if pattern in text and pattern not in strong_staff_patterns:
                    speaker_scores[speaker]["staff_score"] += 1
            
            for pattern in self.patient_patterns:
                if pattern in text and pattern not in strong_patient_patterns:
                    speaker_scores[speaker]["patient_score"] += 1
        
        # Log analysis for debugging
        logger.debug("Rule-based speaker analysis:")
        for speaker, scores in speaker_scores.items():
            logger.debug(f"  {speaker}: staff={scores['staff_score']}, patient={scores['patient_score']}, "
                        f"automated={scores['automated_score']}, words={scores['word_count']}")
            logger.debug(f"    Evidence: {scores['evidence']}")
        
        # Assign roles based on highest scores
        staff_speakers = []
        patient_speakers = []
        automated_speakers = []
        
        for speaker, scores in speaker_scores.items():
            if scores["automated_score"] > 0:
                automated_speakers.append(speaker)
            elif scores["staff_score"] > scores["patient_score"] and scores["staff_score"] > 0:
                staff_speakers.append(speaker)
            elif scores["patient_score"] > 0:
                patient_speakers.append(speaker)
        
        # Ensure we have at least one staff and one patient
        if not staff_speakers or not patient_speakers:
            logger.warning("Rule-based assignment failed to identify clear roles, using fallback logic")
            return self._final_fallback_assignment(segments)
        
        # Return multi-speaker format
        return {
            "staff_speaker": staff_speakers[0],
            "patient_speaker": patient_speakers[0],
            "automated_speaker": automated_speakers[0] if automated_speakers else None,
            "all_staff_speakers": staff_speakers,
            "all_patient_speakers": patient_speakers,
            "all_automated_speakers": automated_speakers,
            "confidence": 0.6,
            "reasoning": f"Rule-based assignment: {len(staff_speakers)} staff, {len(patient_speakers)} patient speakers"
        }
    
    def _final_fallback_assignment(self, segments: List[Dict]) -> Dict:
        """Final fallback using word count heuristic"""
        speaker_word_counts = {}
        
        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "")
            word_count = len(text.split())
            
            if speaker not in speaker_word_counts:
                speaker_word_counts[speaker] = 0
            speaker_word_counts[speaker] += word_count
        
        if len(speaker_word_counts) >= 2:
            # Sort by word count (descending)
            sorted_speakers = sorted(speaker_word_counts.items(), key=lambda x: x[1], reverse=True)
            staff_speaker = sorted_speakers[0][0]  # Most talkative = staff (original logic)
            patient_speaker = sorted_speakers[1][0]  # Second most = patient
            automated_speaker = sorted_speakers[2][0] if len(sorted_speakers) >= 3 else None
        else:
            # Not enough speakers
            speakers = list(speaker_word_counts.keys())
            staff_speaker = speakers[0] if speakers else "SPEAKER_00"
            patient_speaker = speakers[1] if len(speakers) > 1 else "SPEAKER_01"
            automated_speaker = None
        
        logger.warning("Using final fallback assignment based on word count")
        
        return {
            "staff_speaker": staff_speaker,
            "patient_speaker": patient_speaker,
            "automated_speaker": automated_speaker,
            "confidence": 0.3,
            "reasoning": "Final fallback - word count heuristic"
        }
    
    def _separate_text_by_roles(self, segments: List[Dict], role_assignments: Dict) -> Tuple[str, str]:
        """Separate transcript text based on assigned roles (handles multiple speakers per role)"""
        # Get all speakers for each role
        all_staff_speakers = role_assignments.get("all_staff_speakers", [role_assignments.get("staff_speaker")])
        all_patient_speakers = role_assignments.get("all_patient_speakers", [role_assignments.get("patient_speaker")])
        all_automated_speakers = role_assignments.get("all_automated_speakers", [role_assignments.get("automated_speaker")])
        
        # Clean up None values
        all_staff_speakers = [s for s in all_staff_speakers if s]
        all_patient_speakers = [s for s in all_patient_speakers if s]
        all_automated_speakers = [s for s in all_automated_speakers if s]
        
        patient_text_parts = []
        staff_text_parts = []
        
        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            
            if not text:
                continue
            
            # Skip automated voice segments (check by content and speaker)
            if speaker in all_automated_speakers or self._is_automated_content(text):
                logger.debug(f"Skipping automated content: {text[:50]}...")
                continue
            elif speaker in all_staff_speakers:
                staff_text_parts.append(text)
            elif speaker in all_patient_speakers:
                patient_text_parts.append(text)
            else:
                # Unknown speaker - classify by content
                if self._is_likely_staff_content(text):
                    staff_text_parts.append(text)
                    logger.debug(f"Unknown speaker {speaker} classified as staff by content: {text[:30]}...")
                else:
                    # Default to patient for unknown speakers
                    patient_text_parts.append(text)
                    logger.debug(f"Unknown speaker {speaker} classified as patient by default: {text[:30]}...")
        
        patient_text = " ".join(patient_text_parts)
        staff_text = " ".join(staff_text_parts)
        
        # Validation: Check if assignment makes sense
        if len(staff_text) == 0 or len(patient_text) == 0:
            logger.warning(f"Role assignment resulted in empty text - Staff: {len(staff_text)} chars, Patient: {len(patient_text)} chars")
            
            # Try to fix by content analysis
            if len(staff_text) == 0:
                logger.warning("No staff text found - attempting to recover using content analysis")
                return self._emergency_content_based_separation(segments)
        
        logger.debug(f"Role-based separation - Patient: {len(patient_text)} chars, Staff: {len(staff_text)} chars")
        
        return patient_text, staff_text
    
    def _emergency_content_based_separation(self, segments: List[Dict]) -> Tuple[str, str]:
        """Emergency content-based separation when role assignment fails"""
        logger.warning("Using emergency content-based separation")
        
        patient_parts = []
        staff_parts = []
        
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text or self._is_automated_content(text):
                continue
            
            # Strong staff indicators
            if any(indicator in text.lower() for indicator in [
                "thank you for calling", "this is", "how can i help", "let me check",
                "we have", "available", "i can schedule", "have a good day"
            ]):
                staff_parts.append(text)
            # Strong patient indicators  
            elif any(indicator in text.lower() for indicator in [
                "my name is", "i have an appointment", "i need", "i want to",
                "do you have", "can you", "what about", "that works"
            ]):
                patient_parts.append(text)
            else:
                # Ambiguous - assign based on sentence structure or default to patient
                if "?" in text:  # Questions often from patients
                    patient_parts.append(text)
                else:
                    staff_parts.append(text)  # Statements often from staff
        
        patient_text = " ".join(patient_parts)
        staff_text = " ".join(staff_parts)
        
        logger.info(f"Emergency separation result - Patient: {len(patient_text)} chars, Staff: {len(staff_text)} chars")
        
        return patient_text, staff_text
    
    def _is_automated_content(self, text: str) -> bool:
        """Check if content is from automated voice by patterns"""
        text_lower = text.lower()
        automated_indicators = [
            "this call may be recorded",
            "for quality and training purposes", 
            "your call is important",
            "please hold",
            "press 1 for",
            "all representatives are currently busy"
        ]
        
        return any(indicator in text_lower for indicator in automated_indicators)
    
    def _is_likely_staff_content(self, text: str) -> bool:
        """Quick content-based check for staff speech"""
        text_lower = text.lower()
        staff_indicators = [
            "thank you for calling",
            "how can i help",
            "i can help",
            "let me check",
            "we have",
            "our schedule",
            "available",
            "book you"
        ]
        
        return any(indicator in text_lower for indicator in staff_indicators)
    
    def _fallback_speaker_assignment(self, segments: List[Dict]) -> Tuple[str, str]:
        """Final fallback when all analysis fails"""
        logger.warning("All speaker role analysis methods failed, using basic separation")
        
        # Simple fallback - just separate by first two speakers found
        speakers_found = []
        for segment in segments:
            speaker = segment.get("speaker")
            if speaker and speaker not in speakers_found:
                speakers_found.append(speaker)
        
        if len(speakers_found) >= 2:
            # Use first speaker as staff, second as patient
            patient_text_parts = []
            staff_text_parts = []
            
            for segment in segments:
                speaker = segment.get("speaker")
                text = segment.get("text", "").strip()
                
                if not text:
                    continue
                
                if speaker == speakers_found[0]:  # First speaker = staff
                    staff_text_parts.append(text)
                elif speaker == speakers_found[1]:  # Second speaker = patient  
                    patient_text_parts.append(text)
                # Ignore additional speakers
            
            return " ".join(patient_text_parts), " ".join(staff_text_parts)
        else:
            # Only one speaker or no speakers - return empty
            return "", ""