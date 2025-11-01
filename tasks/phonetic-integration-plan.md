# Phonetic Integration Implementation Plan

This document outlines the steps required to complete the integration of phonetic processing capabilities into the TextToSpeech system, including the LLM Coach JSON structure and phonetic markup support.

## Overview

The TextToSpeech system has been reorganized into a proper `src/` package structure. We now need to implement the comprehensive phonetic processing features that were designed during our chat discussions. This includes:

1. **Enhanced PhoneticProcessor** - Complete implementation with IPA validation, markup parsing, and SSML generation
2. **JSON-based LLM Coach** - Enhanced conversational interface with structured responses and numbered options
3. **Phonetic Markup Integration** - Universal support for `[phonetic:...]`, `[ipa:...]`, `[ph:...]` tags throughout the TTS pipeline
4. **Cross-Platform Support** - Azure SSML generation and ElevenLabs text hints

## Current State Analysis

### ✅ What's Already Done (COMPLETED as of September 8, 2025)
- [x] Repository reorganized to `src/texttospeech/` package structure
- [x] **COMPLETE: PhoneticProcessor implementation** (`src/texttospeech/phonetics/processing.py`)
  - [x] Full IPA validation with character sets (vowels, consonants, suprasegmentals)
  - [x] Notation type classification (IPA, SIMPLIFIED, SYLLABIC, TEXT, UNKNOWN)
  - [x] Phonetic markup parsing ([ipa:...], [phonetic:...], [ph:...], [pron:...])
  - [x] Azure SSML generation with proper `<speak>` and `<voice>` tags
  - [x] ElevenLabs text hint generation
  - [x] Complete validation with issue reporting
- [x] **COMPLETE: TTS Interface Updates**
  - [x] Added `is_ssml` parameter to all TTS interfaces
  - [x] Azure TTS updated to support SSML processing
  - [x] ElevenLabs TTS updated to handle SSML gracefully
- [x] **COMPLETE: Pipeline Integration**
  - [x] PhoneticProcessor integrated into ModalityToSpeech
  - [x] Markdown parser updated with default voice fallback
  - [x] End-to-end phonetic processing working with real TTS
- [x] **COMPLETE: Testing & Validation**
  - [x] All phonetic markup processing tests passing
  - [x] Real Azure TTS generation working with phonetic SSML
  - [x] Cross-platform compatibility validated
  - [x] Multiple test files successfully processed
- [x] CLI structure established (`tts_cli.py`, `phonetics_cli.py`)
- [x] Markdown parser supports voice aliases and voice switching
- [x] TTS pipeline architecture in place (`ModalityToSpeech`)

### ❌ What Needs Implementation (NEXT PHASE)
- [ ] Enhanced LLM Coach with JSON responses (Step 2)
- [ ] Complete Phonetics CLI implementation 
- [ ] Interactive phonetic management system
- [ ] Audio recording and phonetic extraction
- [ ] Personal phonetic lookup overlay system

## Implementation Steps

### Phase 1: Core Phonetic Processing ✅ **COMPLETED**

#### Step 1.1: Implement PhoneticProcessor ✅ **DONE**
**File:** `src/texttospeech/phonetics/processing.py`

**Status: FULLY IMPLEMENTED AND WORKING**

Comprehensive implementation completed including:

- [x] `PhoneticNotationType` enum (IPA, SIMPLIFIED, SYLLABIC, TEXT, UNKNOWN)
- [x] `PhoneticSegment` dataclass for text segments with phonetic data
- [x] `PhoneticNotationValidator` class:
  - [x] IPA character validation (vowels, consonants, suprasegmentals)
  - [x] Notation type classification
  - [x] Validation with issue reporting
- [x] `PhoneticSSMLGenerator` class:
  - [x] Azure SSML generation with `<phoneme>` tags
  - [x] ElevenLabs text with phonetic hints
  - [x] Conversion of simplified phonetics to speakable text
- [x] `PhoneticMarkupParser` class:
  - [x] Parse `[phonetic:...]`, `[ipa:...]`, `[ph:...]`, `[pron:...]` tags
  - [x] Convert to PhoneticSegment objects
- [x] Main `PhoneticProcessor` class:
  - [x] Orchestrate parsing, validation, and generation
  - [x] Backend-specific processing (Azure vs ElevenLabs)
  - [x] `preprocess_text()` method returning `(is_ssml, processed_text)`
  - [x] **FIXED:** Added proper SSML wrapper with `<speak>` and `<voice>` tags for Azure

**Validated Working Examples:**
```python
# Real working examples tested September 8, 2025
processor = PhoneticProcessor(backend="azure", voice_name="en-US-JennyNeural")
is_ssml, processed = processor.preprocess_text("Hello [ipa:təˈmeɪtoʊ]tomato[/ipa]!")
# Returns: (True, '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US"><voice name="en-US-JennyNeural">Hello <phoneme alphabet="ipa" ph="təˈmeɪtoʊ">tomato</phoneme>!</voice></speak>')

# Direct functions working
method, content = process_phonetic_for_tts("tomato", "təˈmeɪtoʊ", "azure")
notation_type, is_valid, issues = validate_phonetic_notation("/həˈloʊ/")
```

#### Step 1.2: Update Import Structure ✅ **DONE**
**Files:** `src/texttospeech/phonetics/__init__.py`

**Status: IMPLEMENTED**

Proper exports added and working.

### Phase 2: Enhanced LLM Coach ✅ **COMPLETED**

**Current Status: Step 2 FULLY IMPLEMENTED AND WORKING**

#### Step 2.1: Implement Enhanced LLM Coach with JSON ✅ **DONE**  
**File:** `src/texttospeech/phonetics/llm_phonetic_coach.py`

**Status: FULLY IMPLEMENTED AND WORKING**

Complete implementation including:

- [x] `PhoneticOption` dataclass with phonetic notation and description
- [x] `LLMResponse` class with JSON parsing (`from_json()` method)  
- [x] Context-aware coaching responses with numbered options (1, 2, 3...)
- [x] "Play all" functionality (a/all command)
- [x] **CRITICAL FIX**: Integrated with PhoneticProcessor for robust TTS
- [x] **FIXED**: Phonetic classification issue - syllabic notations now work correctly
- [x] Individual option testing and feedback collection
- [x] Save functionality for successful pronunciations
- [x] Enhanced interaction patterns (good/bad/different/save responses)

**Validated Working Examples:**
```python
# Real working session tested September 9, 2025
coach = LLMPhoneticCoach("worcestershire", phonetic_manager, "azure", "en-US-JennyNeural")
# All 5 phonetic options now work correctly:
# 1. /ˈwʊstəʃə/ (IPA) → <phoneme> tag → ✅ Success
# 2. /ˈwʊstərʃɪr/ (IPA) → <phoneme> tag → ✅ Success  
# 3. WUU-stuh-shuh (Syllabic) → <emphasis> tag → ✅ Success (FIXED!)
# 4. /ˈwɔrsɛstərʃaɪr/ (IPA) → <phoneme> tag → ✅ Success
# 5. WUSS-ter-shur (Syllabic) → <emphasis> tag → ✅ Success (FIXED!)
```

**Critical Integration Fixes Applied:**
- Fixed `PhoneticNotationValidator.classify_notation()` to prioritize syllabic pattern detection
- Raised IPA classification threshold from 60% to 80% with additional checks  
- All phonetic notation types now correctly processed through `process_phonetic_for_tts()`

#### Step 2.2: CLI Integration ✅ **DONE**
**File:** `src/texttospeech/cli/phonetics_cli.py`

**Status: FULLY WORKING**

- [x] Complete `--coach` command implementation
- [x] LLM Coach fully integrated with interactive CLI
- [x] All phonetic option types working correctly in production

### Phase 3: TTS Pipeline Integration ✅ **COMPLETED**

#### Step 3.1: Update ModalityToSpeech ✅ **DONE**
**File:** `src/texttospeech/processing/modality_to_speech.py`

**Status: FULLY INTEGRATED AND WORKING**

Phonetic processing successfully integrated into main TTS pipeline:

- [x] PhoneticProcessor initialized in constructor
- [x] Updated `process_markdown_document()` method with phonetic processing
- [x] Real TTS generation working with phonetic SSML
- [x] Proper error handling for phonetic processing failures

**Validated Working Code:**
```python
# Current working implementation
if self.phonetic_processor:
    is_ssml, text_to_speak = self.phonetic_processor.preprocess_text(segment.text)
    success = self.tts_client.text_to_speech(
        text=text_to_speak,
        voice_name=voice_name,
        output_path=temp_path,
        output_format=output_format,
        is_ssml=is_ssml
    )
```

#### Step 3.2: Update TTS Interface ✅ **DONE**
**File:** `src/texttospeech/tts/interface.py`

**Status: IMPLEMENTED AND WORKING**

- [x] Added `is_ssml` parameter to `text_to_speech()` method
- [x] All implementations updated

#### Step 3.3: Update Azure TTS Implementation ✅ **DONE**
**File:** `src/texttospeech/tts/azure.py`

**Status: FULLY WORKING WITH REAL TTS**

- [x] Handles `is_ssml` parameter in `text_to_speech()` method
- [x] Uses `speak_ssml_async()` when `is_ssml=True`
- [x] Uses `speak_text_async()` when `is_ssml=False`
- [x] **VALIDATED:** Real Azure TTS working with phonetic SSML

#### Step 3.4: Update ElevenLabs Implementation ✅ **DONE**
**File:** `src/texttospeech/tts/elevenlabs.py`

**Status: IMPLEMENTED**

- [x] Handles `is_ssml` parameter (ignores SSML formatting, uses text content)
- [x] Extracts plain text from phonetic hints for ElevenLabs API

### Phase 4: CLI Integration ⚠️ **PARTIAL - TTS DONE, PHONETICS TODO**

#### Step 4.1: Update TTS CLI ✅ **DONE**
**File:** `src/texttospeech/cli/tts_cli.py`

**Status: FULLY WORKING**

- [x] PhoneticProcessor initialized in main TTS workflow
- [x] PhoneticProcessor passed to ModalityToSpeech constructor
- [x] **VALIDATED:** Real TTS working with phonetic markup in production

**Tested and Working Examples:**
- `python -m texttospeech.cli.tts_cli --md examples\phonetic_demo.md --output-dir examples\output --overwrite-audio`
- `python -m texttospeech.cli.tts_cli --md examples\simple_phonetic_test.md --output-dir examples\output --overwrite-audio`

#### Step 4.2: Update Phonetics CLI ⚠️ **NEEDS IMPLEMENTATION**
**File:** `src/texttospeech/cli/phonetics_cli.py`

**Status: SKELETON EXISTS - NEEDS FULL IMPLEMENTATION**

Required implementation:

- [ ] Integrate enhanced LLM Coach (depends on Step 2.1)
- [ ] Use PhoneticProcessor for validation and testing
- [ ] Add `--coach` option for LLM phonetic coaching
- [ ] Complete interactive phonetic management
- [ ] Audio recording functionality
- [ ] Personal phonetic lookup management

### Phase 5: Documentation and Examples ⚠️ **PARTIALLY DONE**

### Phase 5: Documentation and Examples ⚠️ **PARTIALLY DONE**

#### Step 5.1: Update README.md ⚠️ **NEEDS PHONETIC SECTION**
**File:** `README.md`

**Status: BASIC STRUCTURE EXISTS - NEEDS PHONETIC DOCUMENTATION**

Required additions:

- [ ] Phonetic markup syntax examples
- [ ] Voice alias + phonetic combinations  
- [ ] Integration with Markdown and PowerPoint workflows

#### Step 5.2: Create Phonetic Usage Examples ✅ **DONE**
**File:** `examples/phonetic_demo.md`, `examples/simple_phonetic_test.md`

**Status: WORKING EXAMPLES EXIST**

- [x] Comprehensive examples created and tested
- [x] IPA notation usage validated
- [x] Mixed content documents working
- [x] Real TTS generation confirmed

#### Step 5.3: Update Architecture Documentation ⚠️ **NEEDS UPDATE**
**File:** `docs/architecture.md`

**Status: NEEDS PHONETIC INTEGRATION DOCUMENTATION**

Required updates:

- [ ] Document phonetic processing flow
- [ ] Add PhoneticProcessor to core flows section
- [ ] Document integration points between components

### Phase 6: Testing and Validation ✅ **CORE TESTS DONE**

#### Step 6.1: Unit Tests ✅ **WORKING**
**Directory:** `tests/`

**Status: COMPREHENSIVE TESTS IMPLEMENTED AND PASSING**

- [x] Test PhoneticProcessor functionality - **ALL PASSING**
- [x] Test markup parsing with various inputs - **WORKING**
- [x] Test SSML generation for different notation types - **WORKING**
- [x] Test integration with TTS pipeline - **WORKING**

#### Step 6.2: Integration Tests ✅ **VALIDATED**
**Status: REAL-WORLD TESTING COMPLETED**

- [x] Test complete Markdown → phonetic → TTS workflow - **WORKING**
- [x] Test cross-platform compatibility (Azure) - **WORKING**  
- [x] Test error handling and edge cases - **WORKING**

#### Step 6.3: Manual Testing ✅ **VALIDATED**
**Status: PRODUCTION READY**

- [x] Test phonetic markup in real documents - **WORKING**
- [x] Test CLI commands work correctly - **WORKING**
- [x] Test real Azure TTS generation - **WORKING**

**Successfully Generated Audio Files:**
- `examples\output\section_1_basic_phonetics.mp3` ✅
- `examples\output\section_2_mixed_markup.mp3` ✅  
- `examples\output\section_3_simple_phonetics.mp3` ✅

---

## 🎯 **CURRENT STATUS SUMMARY** (Updated September 8, 2025)

### ✅ **PHASE 1: COMPLETE** - Core Phonetic Processing
- **Status: PRODUCTION READY** 
- All phonetic processing functionality implemented and tested
- Real TTS generation working with Azure
- Cross-platform support implemented

### 🎯 **PHASE 2: CURRENT TARGET** - Enhanced LLM Coach  
- **Next Step: Implement JSON Response Structure** (Step 2.1)
- PhoneticProcessor integration ready for LLM Coach
- Foundation is solid, ready for interactive coaching

### ⏭️ **PHASE 3: COMPLETE** - TTS Pipeline Integration
- **Status: FULLY WORKING IN PRODUCTION**
- All TTS interfaces updated and working
- Real-world validation completed

### ⚠️ **REMAINING WORK:**
1. **Step 2.1-2.2**: Enhanced LLM Coach with JSON responses
2. **Step 4.2**: Complete Phonetics CLI implementation
3. **Step 5.1, 5.3**: Documentation updates
4. **Future**: Audio recording and personal phonetic lookup

### 🚀 **READY TO PROCEED:** 
**Next implementation target is Step 2.1: Enhanced LLM Coach JSON Response Structure**

---