"""
LLM Phonetic Coach Module

This module provides an LLM-powered conversational phonetic coaching system
for helping users refine word pronunciations through interactive dialogue.

Canonical location: src/texttospeech/phonetics/llm_phonetic_coach.py
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Guidance block for LLM output (tags enforced)
IPA_TAG_GUIDANCE = (
    "You MUST output phonetic options using explicit tags: [ipa:...] and optional [pron:...]. "
    "Never output bare IPA without a tag. Normalize malformed user inputs like /ˈaɪvʌs/ to [ipa:ˈaɪ.vʌs]."
)

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    AzureOpenAI = None
    OPENAI_AVAILABLE = False
from .processing import PhoneticProcessor, validate_phonetic_notation, process_phonetic_for_tts


@dataclass
class PhoneticOption:
    """Represents a single phonetic pronunciation option."""
    description: str
    phonetic: str

    def __str__(self):
        return f"{self.phonetic} - {self.description}"
 

class LLMResponse:
    """Represents a structured LLM response with general text and phonetic options."""
    def __init__(self, general_text: str, options: List[PhoneticOption]):
        self.general_text = general_text
        self.options = options

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'LLMResponse':
        options = []
        for opt in json_data.get("options", []):
            raw_phonetic = opt.get("phonetic", "").strip()
            # Expect already tagged; fallback-wrap as ipa if missing
            if not (raw_phonetic.startswith('[') and raw_phonetic.endswith(']') and ':' in raw_phonetic):
                raw_phonetic = f"[ipa:{raw_phonetic}]" if raw_phonetic else "[ipa:UNKNOWN]"
            options.append(PhoneticOption(opt.get("description", "(no description)"), raw_phonetic))
        
        return cls(json_data.get("general_text", ""), options)

    def display(self, word: str) -> None:
        """Display the response in a user-friendly format."""
        print(f"\n🎓 Coach: {self.general_text}")

        if self.options:
            print(f"\nHere are some phonetic options for '{word}':")
            for i, option in enumerate(self.options, 1):
                print(f"  {i}. {option.phonetic} - {option.description}")

            print(f"\nPress 1-{len(self.options)} to hear a specific pronunciation")
            print("Press 'a' to have them all pronounced")
            print("Or describe what you're looking for...")


class LLMPhoneticCoach:
    """
    LLM-powered conversational phonetic coaching system.

    This class integrates with PhoneticProcessor for enhanced validation and TTS testing.
    It expects an object 'phonetic_manager' that:
      - has attribute 'lookup_manager' with method add_pronunciation(word, phonetic, source)
      - implements a method _play_phonetic_tts(word: str, phonetic: str) -> bool
      - exposes the current word under coaching through self.current_word when session is active
    """

    def __init__(self, phonetic_manager, tts_backend: str = "azure", voice_name: str = "en-US-JennyNeural"):
        """
        Initialize with an existing phonetic manager and TTS configuration.
        
        Args:
            phonetic_manager: Manager for TTS playback and pronunciation storage
            tts_backend: Backend for TTS ("azure" or "elevenlabs")
            voice_name: Voice name for TTS generation
        """
        self.phonetic_manager = phonetic_manager
        self.current_word = None
        self.conversation_history: List[str] = []
        self.current_options: List[PhoneticOption] = []
        
        # Initialize phonetic processor for enhanced validation and TTS
        self.phonetic_processor = PhoneticProcessor(
            backend=tts_backend,
            voice_name=voice_name,
            accepts_ssml=(tts_backend == "azure")
        )
        self.tts_backend = tts_backend
        self.voice_name = voice_name
        
        # Initialize Azure OpenAI client
        self.azure_client = None
        self.config = getattr(phonetic_manager, 'config', {})
        self._setup_azure_openai()

    def _setup_azure_openai(self):
        """Setup Azure OpenAI client if configuration is available."""
        try:
            if not OPENAI_AVAILABLE:
                logging.warning("OpenAI library not available.")
                return
                
            azure_config = self.config.get('azure_openai', {})
            
            # Check for placeholder or missing credentials
            api_key = azure_config.get('api_key', '')
            endpoint = azure_config.get('endpoint', '')
            
            if not api_key or api_key == 'your-azure-openai-api-key-here':
                logging.info("Azure OpenAI API key not configured.")
                return
                
            if not endpoint or 'your-resource-name' in endpoint:
                logging.info("Azure OpenAI endpoint not configured.")
                return
                
            self.api_version = azure_config.get('api_version', '2025-04-01-preview')

            self.azure_client = AzureOpenAI(
                api_key=api_key,
                api_version=self.api_version,
                azure_endpoint=endpoint
            )
            
            # Store config for easy access
            self.deployment_name = azure_config.get('deployment_name', 'gpt-5')
            self.model = azure_config.get('model', 'gpt-5')
            self.max_completion_tokens = azure_config.get('max_completion_tokens', 4000)  # GPT-5 needs more tokens
            self.temperature = 1.0  # GPT-5 only supports temperature=1.0
            self.enable_fallback = azure_config.get('enable_fallback', True)
            
            logging.info("Azure OpenAI client initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to setup Azure OpenAI: {e}")
            self.azure_client = None

    def start_coaching_session(self, word: str, baseline: Optional[str] = None) -> None:
        """Start an interactive coaching session for a specific word.
    
        baseline: Optional single-tag phonetic (e.g., [ipa:...]/[pron:...]) to prepend as the recorded baseline option.
        """
        self.current_word = word.lower()
        self.conversation_history = []
        self.current_options = []
    
        print(f"\n🎓 LLM Phonetic Coach - Working on '{word}'")
        print("=" * 50)
        print("I'm your pronunciation coach! Let's work together to find the perfect")
        print("phonetic representation for this word.")
        print("\nAvailable commands:")
        print("  'quit' - Exit coaching session")
        print("  '1', '2', '3'... - Play specific phonetic option")
        print("  'a' or 'all' - Play all options in sequence")
        print("  'save' - Save the last played option")
        print("  'save 3' - Save option number 3")
        print("  'save [ipa:phonetic]' - Save specific phonetic notation")
        print("  'play <phonetics>' - Test custom pronunciation")
        print("  Or describe what you want...")
        print("-" * 50)
    
        # Get initial phonetic suggestions
        self._generate_initial_suggestions(word)
    
        # Inject recorded baseline option at the top if provided and not a duplicate
        if baseline:
            try:
                norm = baseline.strip()
                # Normalize wrapper via lookup manager when available
                if hasattr(self.phonetic_manager, 'lookup_manager') and hasattr(self.phonetic_manager.lookup_manager, '_normalize_and_wrap'):
                    norm = self.phonetic_manager.lookup_manager._normalize_and_wrap(norm)
    
                # Extract core value for deduplication
                core = norm
                if core.startswith('[') and core.endswith(']') and ':' in core:
                    core = core.split(':', 1)[1][:-1]
    
                existing_cores = set()
                for opt in self.current_options:
                    s = opt.phonetic.strip()
                    c = s.split(':', 1)[1][:-1] if s.startswith('[') and s.endswith(']') and ':' in s else s
                    existing_cores.add(c)
    
                if core not in existing_cores:
                    self.current_options.insert(0, PhoneticOption(description="Recorded baseline", phonetic=norm))
                    print("🎼 Added recorded baseline option at the top.")
            except Exception as e:
                try:
                    if hasattr(self, 'logger'):
                        self.logger.debug(f"Baseline injection warning: {e}")
                except Exception:
                    pass
    
        # Start conversation loop
        self._conversation_loop()

    def _generate_initial_suggestions(self, word: str) -> None:
        """Generate initial phonetic suggestions for the word."""
        # First check if we have existing entries in phonetic dictionaries
        existing_options = self._get_existing_phonetic_entries(word)
        
        print(f"\n🤖 Generating pronunciation options for '{word}'... Please wait a moment.")
        
        json_response = self._get_llm_response(word, "initial_suggestions", existing_entries=existing_options)
        llm_response = LLMResponse.from_json(json_response)
        
        # Ensure dictionary entries are always included at the top
        self.current_options = self._ensure_dictionary_entries_included(llm_response.options, existing_options)
        
        self._last_played_option = None  # Track which option user last heard
        self._feedback_count = 0  # Track feedback interactions for shorter prompts
        
        # Display with updated options
        self._display_options_with_dictionary_note(word, existing_options, llm_response.general_text)

    def _get_existing_phonetic_entries(self, word: str) -> List[Dict[str, str]]:
        """Retrieve and normalize existing phonetics using lookup_manager (which wraps PhoneticLookupManager)."""
        existing_entries: List[Dict[str,str]] = []
        w = word.lower()
        try:
            if hasattr(self.phonetic_manager, 'lookup_manager'):
                lm = self.phonetic_manager.lookup_manager
                # Preferred helper if available
                if hasattr(lm, 'get_existing_for_coach'):
                    existing_entries = lm.get_existing_for_coach(w)
                else:
                    # Fallback legacy access
                    if hasattr(lm, 'phonetic_data') and w in lm.phonetic_data:
                        existing_entries.append({
                            'source': 'main dictionary',
                            'phonetic': lm.phonetic_data[w],
                            'description': 'From main phonetic dictionary'
                        })
                    if hasattr(lm, 'personal_data') and w in lm.personal_data:
                        existing_entries.append({
                            'source': 'personal dictionary',
                            'phonetic': lm.personal_data[w],
                            'description': 'From your personal phonetic dictionary'
                        })
                # Normalize via manager utility if present
                if hasattr(lm, '_normalize_and_wrap'):
                    for e in existing_entries:
                        e['phonetic'] = lm._normalize_and_wrap(e['phonetic'])
        except Exception as e:
            logging.debug(f"Could not check existing phonetic entries: {e}")
        return existing_entries

    def _ensure_dictionary_entries_included(self, llm_options: List[PhoneticOption], existing_entries: List[Dict[str, str]]) -> List[PhoneticOption]:
        """Prepend normalized existing dictionary entries (deduplicated by core)."""
        if not existing_entries:
            return llm_options
        core_seen = set()
        def core(p: str):
            s=p
            if s.startswith('[') and s.endswith(']') and ':' in s:
                s = s.split(':',1)[1][:-1]
            if s.startswith('/') and s.endswith('/') and len(s)>2:
                s=s[1:-1]
            return s
        dict_opts: List[PhoneticOption] = []
        for e in existing_entries:
            c = core(e['phonetic'])
            if c in core_seen: continue
            core_seen.add(c)
            dict_opts.append(PhoneticOption(description=f"From {e['source']} (previously saved)", phonetic=e['phonetic']))
        # Filter out duplicates from llm options
        filtered_llm = []
        for opt in llm_options:
            if core(opt.phonetic) in core_seen:
                continue
            core_seen.add(core(opt.phonetic))
            filtered_llm.append(opt)
        if dict_opts:
            print(f"📚 Ensuring {len(dict_opts)} dictionary entries are included at the top")
        return dict_opts + filtered_llm

    def _display_options_with_dictionary_note(self, word: str, existing_entries: List[Dict[str, str]], general_text: str) -> None:
        """Display options with special note about dictionary entries."""
        print(f"\n🎓 Coach: {general_text}")
        
        if existing_entries:
            dict_count = len(existing_entries)
            print(f"\n📚 Note: Found {dict_count} existing pronunciation(s) in your dictionary - included at the top")

        if self.current_options:
            print(f"\nHere are some phonetic options for '{word}':")
            for i, option in enumerate(self.current_options, 1):
                # Add special marker for dictionary entries
                marker = "📚 " if any(entry['phonetic'] == option.phonetic for entry in existing_entries) else "   "
                print(f"  {i}. {marker}{option.phonetic} - {option.description}")

            print(f"\nPress 1-{len(self.current_options)} to hear a specific pronunciation")
            print("Press 'a' to have them all pronounced")
            print("Or describe what you're looking for...")

    def _get_llm_response(self, word: str, context: str = "general", existing_entries: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get LLM response for a word and context using Azure OpenAI.
        """
        # Check if Azure OpenAI is properly configured
        if not self.azure_client:
            return self._get_configuration_error_response()
        
        # Try Azure OpenAI
        try:
            response = self._call_azure_openai(word, context, existing_entries)
            if response:
                return response
            else:
                return self._get_api_error_response("Failed to get valid response from Azure OpenAI")
        except Exception as e:
            logging.error(f"Azure OpenAI call failed: {e}")
            return self._get_api_error_response(f"Azure OpenAI API error: {str(e)}")

    def _get_configuration_error_response(self) -> Dict[str, Any]:
        """Return error message when Azure OpenAI is not configured."""
        azure_config = self.config.get('azure_openai', {})
        
        if not OPENAI_AVAILABLE:
            error_msg = "❌ LLM Coach not available: OpenAI library not installed. Run 'pip install openai' to enable."
        elif not azure_config:
            error_msg = "❌ LLM Coach not configured: No 'azure_openai' section found in config.yaml"
        elif not azure_config.get('api_key') or azure_config.get('api_key') == 'your-azure-openai-api-key-here':
            error_msg = "❌ LLM Coach not configured: Please set your Azure OpenAI API key in config.yaml"
        elif not azure_config.get('endpoint') or 'your-resource-name' in azure_config.get('endpoint', ''):
            error_msg = "❌ LLM Coach not configured: Please set your Azure OpenAI endpoint in config.yaml"
        else:
            error_msg = "❌ LLM Coach not configured: Azure OpenAI configuration is incomplete"
        
        return {
            "general_text": error_msg + "\n\nTo enable the LLM Phonetic Coach:\n1. Set up an Azure OpenAI resource\n2. Update config.yaml with your endpoint and API key\n3. Set your GPT-5 deployment name",
            "options": [
                {"description": "Configuration needed", "phonetic": "[pron:Please configure Azure OpenAI]"}
            ]
        }

    def _get_api_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error message when Azure OpenAI API fails."""
        return {
            "general_text": f"❌ LLM Coach temporarily unavailable: {error_message}\n\nPlease check:\n1. Your Azure OpenAI endpoint is correct\n2. Your API key is valid\n3. Your deployment name matches your GPT-5 deployment\n4. Your Azure OpenAI resource has quota available",
            "options": [
                {"description": "API error occurred", "phonetic": "[pron:Please check configuration]"}
            ]
        }

    def _call_azure_openai(self, word: str, context: str, existing_entries: List[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Call Azure OpenAI with conversation history for context-aware responses."""
        
        # Build conversation context
        conversation_context = ""
        if self.conversation_history:
            conversation_context = f"\nConversation so far:\n" + "\n".join(self.conversation_history[-6:])  # Last 6 exchanges
        
        # Reference last played option if available
        last_option_context = ""
        if hasattr(self, '_last_played_option') and self._last_played_option:
            last_option_context = f"\nLast option user heard: Option {self._last_played_option['number']} - {self._last_played_option['phonetic']} ({self._last_played_option['description']})"
        
        # Add existing entries context
        existing_context = ""
        if existing_entries:
            existing_context = f"\nExisting phonetic entries for '{word}':\n"
            for entry in existing_entries:
                existing_context += f"- {entry['phonetic']} ({entry['source']})\n"
            existing_context += "ALWAYS include existing dictionary entries and comment that previous entries were found. If you feel these are imperfect, add variations. If they sound correct, show dictionary items only."
        
        # Check if this is a save intent context
        is_save_intent = context.startswith('save_intent:')
        
        if is_save_intent:
            save_guidance_prompt = f"""
The user wants to save a pronunciation but needs guidance on the proper command format.

IMPORTANT: Instead of saying you'll save something, GUIDE THE USER to use the save command properly:

Available save commands:
- "save" - saves the last option they heard
- "save 3" - saves option number 3  
- "save [ipa:phonetic]" - saves specific phonetic notation

If they refer to "second to last", "the one before", "previous one", etc., translate this to the specific option number and tell them to use "save X" where X is the number.

Your response should guide them to type the correct save command, not perform the save yourself.
"""
            system_prompt = f"""You are a helpful pronunciation coach guiding the user to save phonetic pronunciations properly.

{save_guidance_prompt}

Current word: "{word}"
Context: {context}
{conversation_context}
{last_option_context}

Always respond in this JSON format:
{{
    "general_text": "guide the user to use the proper save command - don't perform the save yourself",
    "options": [],
    "feedback_prompt": "Ask them to type the save command you suggested"
}}"""
        
        else:
            # Enhanced system prompt for conversational coaching
            system_prompt = f"""You are a friendly, expert pronunciation coach helping iteratively find the BEST phonetic representation for a word.

MISSION: We are working together to find the most accurate phonetic notation that will produce perfect pronunciation via text-to-speech using Microsoft Azure TTS.

CRITICAL PHONETIC FORMAT REQUIREMENTS:
You MUST follow these exact Microsoft Azure TTS SSML phoneme format rules:

1. USE ONLY IPA (International Phonetic Alphabet) notation
2. Format: [ipa:phonetic_string] (e.g., [ipa:təˈmeɪtoʊ])
3. REQUIRED IPA stress and boundary symbols:
   - ˈ = Primary stress (NOT single quote ' or ')
   - ˌ = Secondary stress (NOT comma ,)
   - . = Syllable boundary
   - ː = Long vowel (NOT colon : or ：)
   - ‿ = Linking

4. STRESS PLACEMENT: Place ˈ or ˌ BEFORE the stressed syllable vowel
   - Correct: [ipa:təˈmeɪtoʊ] (stress before "meɪ")
   - Wrong: [ipa:təmeɪˈtoʊ] (stress after vowel)

5. COMMON MISTAKES TO AVOID:
   - Don't use ASCII approximations: use ˈ not ', use ˌ not ,, use ː not :
   - Don't place stress after vowels - it goes BEFORE the stressed vowel
   - Don't mix phonetic systems - use pure IPA only
   - Don't use /slashes/ or [brackets] inside the ipa: tag

6. EXAMPLES OF PROPER IPA FORMAT (what you should generate):
   - həˈloʊ (hello)
   - ˌɪntərˈnæʃənəl (international - secondary + primary stress)  
   - kəmˈpjuːtər (computer - long vowel ː)
   - ðə.ˈkæt (the cat - syllable boundary)

7. COMMON ENGLISH IPA VOWELS FOR REFERENCE:
   - i (beat, see), ɪ (bit, sit), eɪ (bait, say), ɛ (bet, set)
   - æ (bat, cat), ɑ (bot, father), ɔ (bought, saw), oʊ (boat, so)
   - ʊ (book, put), u (boot, do), ʌ (but, cut), ə (about, sofa)
   - aɪ (bite, my), aʊ (bout, how), ɔɪ (boy, coin)

8. COMMON ENGLISH IPA CONSONANTS FOR REFERENCE:
   - p b t d k g (stops), f v θ ð s z ʃ ʒ h (fricatives)
   - m n ŋ (nasals), l ɹ (approximants), w j (semivowels)
   - tʃ dʒ (affricates)

Key behaviors:
- Be conversational and reference what the user just heard or said
- When user asks for modifications, acknowledge their feedback and explain your new suggestions  
- Reference previous options by number when relevant ("Option 2 that you just heard...")
- We are ITERATING towards the perfect pronunciation - acknowledge this process
- Be encouraging and educational about why certain phonetic choices work better
- ALWAYS include existing dictionary entries and mention that previous entries were found
- If dictionary entries seem imperfect, add variations; if they sound correct, show dictionary items only
- Provide exactly what the user is asking for
- NEVER say you're saving something - guide users to use save commands instead
- ALL phonetic notations must follow the Microsoft Azure TTS IPA format rules above

Always respond in this JSON format:
{{
    "general_text": "conversational response that acknowledges user's feedback and explains your suggestions",
    "options": [
        {{"description": "helpful description explaining the phonetic choice", "phonetic": "pure_ipa_notation_only"}},
        {{"description": "helpful description explaining the phonetic choice", "phonetic": "pure_ipa_notation_only"}}
    ],
    "feedback_prompt": "natural question about how it sounded (keep short after first time)"
}}

IMPORTANT OUTPUT FORMAT CHANGE:
Each option's phonetic field MUST already be wrapped in [ipa:...] OR [pron:...] tags.
NEVER output bare IPA without a tag. Provide IPA primary; optionally include one mnemonic [pron:...] if helpful.
If user input or dictionary shows malformed entries like [ipa:/ˈaɪvʌs/] or /ˈaɪvʌs/, normalize to [ipa:ˈaɪ.vʌs].

Current word: "{word}"
Context: {context}
{conversation_context}
{last_option_context}
{existing_context}"""

        user_prompt = f"Help with pronunciation coaching for '{word}' in context '{context}'. We're iterating to find the perfect phonetic representation." 

        try:
            # Use Chat Completions API with GPT-5 optimized parameters
            print("🤖 Thinking...")  # Show thinking indicator
            
            if hasattr(self, 'logger'):
                try:
                    self.logger.debug(f"Calling Azure OpenAI for word: {word}")
                except Exception:
                    pass
            
            # Primary attempt using max_completion_tokens (GPT-5 preview)
            try:
                resp = self.azure_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=self.max_completion_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
            except Exception as primary_err:
                # Retry with legacy param name if server rejects unknown field
                retry_needed = any(token in str(primary_err).lower() for token in ["max_completion_tokens", "unexpected", "unknown", "invalid" ])
                if hasattr(self, 'logger'):
                    try:
                        self.logger.debug(f"Primary GPT-5 call failed ({primary_err}); retrying with max_tokens param: {retry_needed}")
                    except Exception:
                        pass
                if retry_needed:
                    try:
                        resp = self.azure_client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            max_tokens=self.max_completion_tokens,
                            temperature=self.temperature,
                            response_format={"type": "json_object"}
                        )
                    except Exception as secondary_err:
                        if hasattr(self, 'logger'):
                            try:
                                self.logger.error(f"Retry with max_tokens also failed: {secondary_err}")
                            except Exception:
                                pass
                        return None
                else:
                    return None
            
            content = resp.choices[0].message.content

            if not content:
                if hasattr(self, 'logger'):
                    try:
                        self.logger.warning("Empty content returned from Azure OpenAI")
                    except Exception:
                        pass
                return None

            # Parse JSON safely
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as je:
                if hasattr(self, 'logger'):
                    try:
                        self.logger.error(f"Failed to parse JSON content: {je}. Raw content: {content[:200]}")
                    except Exception:
                        pass
                return None

            if "general_text" in parsed and "options" in parsed:
                if hasattr(self, 'logger'):
                    try:
                        self.logger.debug(f"Successfully generated {len(parsed.get('options', []))} phonetic options")
                    except Exception:
                        pass
                # Sanitize options to ensure tagging & normalization via lookup_manager if available
                try:
                    if hasattr(self.phonetic_manager, 'lookup_manager') and hasattr(self.phonetic_manager.lookup_manager, 'sanitize_llm_options'):
                        parsed['options'] = self.phonetic_manager.lookup_manager.sanitize_llm_options(parsed.get('options', []))
                except Exception as san_e:
                    logging.debug(f"Sanitization warning: {san_e}")
                return parsed
            
            if hasattr(self, 'logger'):
                try:
                    self.logger.warning("Azure OpenAI response missing required fields: keys= %s", list(parsed.keys()))
                except Exception:
                    pass
            return None
            
        except Exception as e:
            if hasattr(self, 'logger'):
                try:
                    self.logger.error(f"Azure OpenAI API call failed: {e}")
                except Exception:
                    pass
            return None

    # DISABLED FALLBACK MOCK RESPONSES
    # The following mock response method is disabled to ensure Azure OpenAI configuration is required
    # 
    # def _get_mock_response(self, word: str, context: str = "general") -> Dict[str, Any]:
    #     """
    #     Get mock response for a word and context.
    #     Fallback implementation when Azure OpenAI is not available.
    #     NOTE: This fallback is disabled. Azure OpenAI configuration is required.
    #     """
    #     word_lower = word.lower()
    #
    #     if context == "initial_suggestions":
    #         if word_lower == "hello":
    #             return {
    #                 "general_text": "Here are some phonetic options for 'hello'. The word has different stress patterns and vowel realizations depending on the context and regional accent.",
    #                 "options": [
    #                     {"description": "Standard American (IPA)", "phonetic": "[ipa:həˈloʊ]"},
    #                     {"description": "Clear/emphatic (IPA)", "phonetic": "[ipa:hɛˈloʊ]"},
    #                     {"description": "Casual reduced (IPA)", "phonetic": "[ipa:həˈlo]"},
    #                     {"description": "British variant (IPA)", "phonetic": "[ipa:həˈləʊ]"},
    #                     {"description": "Simplified phonetic", "phonetic": "[pron:heh-LOH]"}
    #                 ]
    #             }
    #         elif word_lower == "tomato":
    #             return {
    #                 "general_text": "The word 'tomato' is famous for having different pronunciations! Here are the main variants you'll encounter.",
    #                 "options": [
    #                     {"description": "American (IPA)", "phonetic": "[ipa:təˈmeɪtoʊ]"},
    #                     {"description": "British (IPA)", "phonetic": "[ipa:təˈmɑːtəʊ]"},
    #                     {"description": "Emphatic American (IPA)", "phonetic": "[ipa:toʊˈmeɪtoʊ]"},
    #                     {"description": "Casual version", "phonetic": "[pron:tuh-MAY-toh]"},
    #                     {"description": "Syllable breakdown", "phonetic": "[pron:to-ma-to]"}
    #                 ]
    #             }
    #         elif word_lower == "worcestershire":
    #             return {
    #                 "general_text": "Ah, 'Worcestershire' - the sauce that trips up everyone! It's much simpler than it looks when you know the trick.",
    #                 "options": [
    #                     {"description": "Correct British (IPA)", "phonetic": "[ipa:ˈwʊstəʃə]"},
    #                     {"description": "American approximation (IPA)", "phonetic": "[ipa:ˈwʊstərʃɪr]"},
    #                     {"description": "Broken down slowly", "phonetic": "[pron:WUU-stuh-shuh]"},
    #                     {"description": "Common mispronunciation (avoid!)", "phonetic": "[ipa:ˈwɔrsɛstərʃaɪr]"},
    #                     {"description": "Very casual", "phonetic": "[pron:WUSS-ter-shur]"}
    #                 ]
    #             }
    #         else:
    #             return {
    #                 "general_text": f"Let me help you with '{word}'. I'll provide several phonetic options based on common pronunciation patterns.",
    #                 "options": [
    #                     {"description": "Basic IPA transcription", "phonetic": f"[ipa:{word_lower}]"},
    #                     {"description": "Simplified uppercase", "phonetic": f"[pron:{word_lower.upper()}]"},
    #                     {"description": "Syllable-separated", "phonetic": f"[pron:{'-'.join(list(word_lower))}]"},
    #                     {"description": "Common vowel pattern", "phonetic": f"[phonetic:{word_lower.replace('a', 'æ').replace('e', 'ɛ')}]"}
    #                 ]
    #             }
    #
    #     elif context == "softer":
    #         return {
    #             "general_text": f"Here are some softer, gentler ways to pronounce '{word}':",
    #             "options": [
    #                 {"description": "Reduced stress version", "phonetic": f"[ipa:{word_lower}]"},
    #                 {"description": "Whispered quality", "phonetic": f"[pron:{word_lower} (soft)]"},
    #                 {"description": "Relaxed articulation", "phonetic": f"[phonetic:{word_lower.replace('t', 'ɾ')}]"}
    #             ]
    #         }
    #
    #     elif context == "clearer":
    #         return {
    #             "general_text": f"Here are some crisper, clearer ways to pronounce '{word}':",
    #             "options": [
    #                 {"description": "Over-articulated", "phonetic": f"[pron:{word_lower.upper()}]"},
    #                 {"description": "Clear consonants", "phonetic": f"[pron:{word_lower} (crisp)]"},
    #                 {"description": "Broadcast quality", "phonetic": f"[pron:{word_lower} (precise)]"}
    #             ]
    #         }
    #
    #     else:
    #         return {
    #             "general_text": f"I understand you want to work on '{word}'. Could you be more specific about what you'd like to change?",
    #             "options": [
    #                 {"description": "Current best guess", "phonetic": f"[ipa:{word_lower}]"},
    #                 {"description": "Alternative stress", "phonetic": f"[pron:{word_lower} (alt)]"}
    #             ]
    #         }

    def _conversation_loop(self) -> None:
        """Main conversation loop for coaching."""
        while True:
            try:
                user_input = input(f"\n🗣️  You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Great session! Hope that helped with your pronunciation.")
                    break

                # Handle numbered options - direct play without LLM processing
                if user_input.isdigit():
                    option_num = int(user_input)
                    if 1 <= option_num <= len(self.current_options):
                        option = self.current_options[option_num - 1]
                        self._test_pronunciation(option.phonetic, show_header=True, option_number=option_num)
                    else:
                        print(f"❌ Please choose a number between 1 and {len(self.current_options)}")
                    continue

                # Handle enhanced save command
                if user_input.lower().startswith('save'):
                    self._handle_save_command(user_input)
                    continue

                # Handle "play all" command
                if user_input.lower() in ['a', 'all']:
                    self._play_all_options()
                    continue

                # Handle "play <phonetic>" command
                if user_input.lower().startswith('play '):
                    phonetic = user_input[5:].strip()
                    self._test_pronunciation(phonetic)
                    continue

                # Handle legacy "try option X" command for backwards compatibility
                if user_input.lower().startswith('try option '):
                    try:
                        option_num = int(user_input[11:].strip())
                        if 1 <= option_num <= len(self.current_options):
                            option = self.current_options[option_num - 1]
                            print(f"🔊 Playing option {option_num}: {option.phonetic}")
                            self._test_pronunciation(option.phonetic)
                        else:
                            print(f"❌ Option {option_num} not available. Please choose 1-{len(self.current_options)}")
                    except ValueError:
                        print("❌ Please specify a valid option number (e.g., 'try option 2')")
                    continue

                # Add user input to conversation history
                self.conversation_history.append(f"User: {user_input}")

                # Check if user is expressing save intent - let LLM guide them to proper command
                if any(word in user_input.lower() for word in ['save', 'keep', 'store', 'remember']):
                    response = self._process_save_intent(user_input)
                else:
                    # Process natural language input through LLM
                    print(f"\n🤖 Let me think about that...")
                    response = self._process_user_request(user_input)

                if response:
                    # Store feedback prompt for next interaction
                    self._current_feedback_prompt = response.get('feedback_prompt', 
                        "How did that sound?")
                    
                    llm_response = LLMResponse.from_json(response)
                    self.current_options = llm_response.options
                    llm_response.display(self.current_word)
                else:
                    print("🤔 I didn't quite understand that. Try describing what you want or use a number to test an option.")

            except KeyboardInterrupt:
                print("\n\n👋 Session ended. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _process_save_intent(self, user_input: str) -> Dict[str, Any]:
        """Process user input that expresses save intent and guide them to proper save command."""
        
        # Add to conversation history
        self.conversation_history.append(f"User expressed save intent: {user_input}")
        
        # Enhanced context for LLM to understand save intent
        context = f"save_intent: {user_input}"
        
        # Get LLM response that should guide user to proper save command
        return self._get_llm_response(self.current_word, context)

    def _handle_save_command(self, command: str) -> None:
        """Handle enhanced save command with various formats."""
        command_parts = command.strip().split(None, 1)
        
        if len(command_parts) == 1:
            # Simple "save" - use last played option
            if hasattr(self, '_last_played_option') and self._last_played_option:
                phonetic = self._last_played_option['phonetic']
                option_desc = self._last_played_option['description']
                self._confirm_and_save(phonetic, f"last played option ({option_desc})")
            else:
                print("❌ No option has been played yet. Play an option first, then use 'save'.")
                print("💡 Or use 'save 3' to save a specific option by number.")
        
        elif len(command_parts) == 2:
            argument = command_parts[1].strip()
            
            # Check if argument is a number (option number)
            if argument.isdigit():
                option_num = int(argument)
                if 1 <= option_num <= len(self.current_options):
                    option = self.current_options[option_num - 1]
                    self._confirm_and_save(option.phonetic, f"option {option_num} ({option.description})")
                else:
                    print(f"❌ Option {option_num} not available. Please choose 1-{len(self.current_options)}")
            
            # Check if argument looks like phonetic notation
            elif any(argument.startswith(f'[{tag}:') for tag in ['ipa', 'pron', 'ph', 'phonetic']):
                self._confirm_and_save(argument, "specified phonetic notation")
            
            else:
                print(f"❌ Invalid save argument: '{argument}'")
                print("💡 Use 'save' (last played), 'save 3' (option number), or 'save [ipa:phonetic]' (specific notation)")

    def _confirm_and_save(self, phonetic: str, description: str) -> None:
        """Confirm save operation and allow choice of dictionary."""
        print(f"\n💾 Ready to save: {phonetic}")
        print(f"📝 Description: {description}")
        print(f"🎯 Word: '{self.current_word}'")
        
        # Play the pronunciation for confirmation
        print(f"\n🔊 Let me play this pronunciation for confirmation...")
        success = self.phonetic_manager._play_phonetic_unified(self.current_word, phonetic)
        
        if not success:
            print("❌ Could not play pronunciation for confirmation. Save anyway? (y/n): ", end="")
            confirm = input().strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Save cancelled.")
                return
        
        print(f"\n❓ Save this pronunciation for '{self.current_word}'?")
        print("   1. Personal dictionary (just for you)")
        print("   2. Global dictionary (for everyone)")  
        print("   3. Cancel")
        
        choice = input("Choose (1/2/3): ").strip()
        
        if choice == '1':
            self._save_to_dictionary(phonetic, 'personal')
        elif choice == '2':
            self._save_to_dictionary(phonetic, 'global')
        elif choice == '3':
            print("❌ Save cancelled.")
        else:
            print("❌ Invalid choice. Save cancelled.")
            
    def _save_to_dictionary(self, phonetic: str, dictionary_type: str) -> None:
        """Save pronunciation to specified dictionary."""
        try:
            if dictionary_type == 'personal':
                self.phonetic_manager.lookup_manager.add_pronunciation(
                    self.current_word,
                    phonetic,
                    "llm_coached_personal"
                )
                print(f"✅ Saved '{self.current_word}' → '{phonetic}' to your personal dictionary!")
                
            elif dictionary_type == 'global':
                # For global dictionary, we might need admin approval or special handling
                # For now, save to personal with global flag
                self.phonetic_manager.lookup_manager.add_pronunciation(
                    self.current_word,
                    phonetic,
                    "llm_coached_global_candidate"
                )
                print(f"✅ Saved '{self.current_word}' → '{phonetic}' as global dictionary candidate!")
                print("📋 Note: Global submissions may require review before activation.")
                
        except Exception as e:
            print(f"❌ Error saving pronunciation: {e}")

    def _process_user_feedback(self, feedback: str) -> None:
        """Process user feedback and generate contextual response."""
        print(f"\n🤖 Let me adjust based on your feedback...")
        
        # Add feedback to conversation history
        self.conversation_history.append(f"User feedback: {feedback}")
        
        # Generate response based on feedback
        response = self._get_llm_response(self.current_word, f"user_feedback: {feedback}")
        
        if response:
            # Store feedback prompt for next interaction
            self._current_feedback_prompt = response.get('feedback_prompt', 
                "How did that sound?")
            
            llm_response = LLMResponse.from_json(response)
            self.current_options = llm_response.options
            llm_response.display(self.current_word)
        else:
            print("🤔 I'd like to help adjust that. Could you be more specific about what you'd like to change?")

    def _process_user_request(self, user_input: str) -> Dict[str, Any]:
        """Process user input and generate appropriate LLM response."""
        user_lower = user_input.lower()

        # Determine context based on user input
        if any(word in user_lower for word in ['soft', 'gentle', 'quiet', 'whisper']):
            context = "softer"
        elif any(word in user_lower for word in ['clear', 'crisp', 'sharp', 'precise', 'broadcast']):
            context = "clearer"
        elif any(word in user_lower for word in ['different', 'other', 'alternative', 'another']):
            context = "alternatives"
        elif any(word in user_lower for word in ['help', 'how', 'what', 'explain']):
            context = "help"
        else:
            context = "general"

        return self._get_llm_response(self.current_word, context)

    def _play_all_options(self) -> None:
        """Play all current phonetic options in sequence."""
        if not self.current_options:
            print("❌ No options available to play")
            return

        print(f"🎵 Playing all {len(self.current_options)} options in sequence...")

        for i, option in enumerate(self.current_options, 1):
            print(f"\n   Option {i}: {option.phonetic} - {option.description}")
            success = self._test_pronunciation(option.phonetic, show_header=False)

            if not success:
                print(f"   ❌ Could not play option {i}")

            if i < len(self.current_options):
                input("   Press Enter for next option...")

        print("\n✅ Finished playing all options!")
        print("Which one sounded best? Or would you like me to suggest variations?")

    def _test_pronunciation(self, phonetic: str, show_header: bool = True, option_number: int = None) -> bool:
        """Test a phonetic pronunciation using the unified processing pipeline."""
        try:
            if show_header:
                print(f"🔊 Playing: {phonetic}")

            # Track which option was played for context
            if option_number:
                self._last_played_option = {
                    'number': option_number,
                    'phonetic': phonetic,
                    'description': self.current_options[option_number-1].description if option_number <= len(self.current_options) else "Custom"
                }

            # Use the unified processing pipeline
            success = self.phonetic_manager._play_phonetic_unified(
                self.current_word, 
                phonetic
            )

            if success and show_header:
                # Get LLM-generated feedback prompt or use smart default
                feedback_prompt = getattr(self, '_current_feedback_prompt', 
                    "How did that sound? You can say 'good', 'save', or tell me what to adjust:")
                
                # Make shorter prompts after first interaction
                if hasattr(self, '_feedback_count'):
                    self._feedback_count += 1
                    if self._feedback_count > 1:
                        feedback_prompt = "How was that one? (or 'save' to keep it)"
                else:
                    self._feedback_count = 1
                
                print(f"\n💡 Tip: Just type a number to play that option, or 'save' to keep the last one played!")
                feedback = input(f"🎙️  {feedback_prompt} ").strip()
                
                # Handle empty input - just continue
                if not feedback:
                    return success
                
                # Handle numbered input - play that option directly (like main loop)
                if feedback.isdigit():
                    option_num = int(feedback)
                    if 1 <= option_num <= len(self.current_options):
                        option = self.current_options[option_num - 1]
                        print(f"🔊 Playing option {option_num}: {option.phonetic}")
                        self._test_pronunciation(option.phonetic, show_header=True, option_number=option_num)
                    else:
                        print(f"❌ Please choose a number between 1 and {len(self.current_options)}")
                    return success
                
                # Add to conversation history
                self.conversation_history.append(f"User played option and said: {feedback}")

                if feedback.lower() in ['good', 'great', 'perfect', 'yes', 'save', 's']:
                    if feedback.lower() in ['save', 's']:
                        self._confirm_and_save(phonetic, f"last played option")
                    else:
                        print("🎉 Great! Would you like to save this one?")
                        save = input("Type 'save' to save it: ").strip().lower()
                        if save in ['save', 's']:
                            self._confirm_and_save(phonetic, f"approved option")
                else:
                    # Process feedback through LLM for natural response
                    if feedback and feedback.lower() not in ['bad', 'no', 'terrible']:
                        self._process_user_feedback(feedback)

            return success

        except Exception as e:
            print(f"❌ Error testing pronunciation: {e}")
            return False



    def _suggest_variations(self, base_phonetic: str) -> None:
        """Suggest variations on a phonetic pronunciation."""
        variations_response = {
            "general_text": f"Here are some variations on '{base_phonetic}' to try:",
            "options": [
                {"description": "With more emphasis", "phonetic": base_phonetic.upper()},
                {"description": "With less emphasis", "phonetic": base_phonetic.lower()},
                {"description": "Slower/clearer", "phonetic": f"{base_phonetic} (slow)"},
                {"description": "Faster/casual", "phonetic": f"{base_phonetic} (fast)"}
            ]
        }

        # Filter out identical options
        unique_options = []
        seen_phonetics = set()
        for opt in variations_response["options"]:
            if opt["phonetic"] not in seen_phonetics and opt["phonetic"] != base_phonetic:
                unique_options.append(opt)
                seen_phonetics.add(opt["phonetic"])

        if unique_options:
            variations_response["options"] = unique_options
            llm_response = LLMResponse.from_json(variations_response)
            self.current_options = llm_response.options
            llm_response.display(self.current_word)
        else:
            print("🤔 Let me think of some other approaches for this word...")


__all__ = [
    "PhoneticOption",
    "LLMResponse",
    "LLMPhoneticCoach",
]