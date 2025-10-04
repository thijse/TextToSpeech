#!/usr/bin/env python3
"""
Test the Enhanced LLM Coach implementation
"""

import sys
import os
sys.path.insert(0, 'src')

def test_llm_coach_components():
    """Test the enhanced LLM Coach JSON components"""
    print("🧪 Testing Enhanced LLM Coach Implementation")
    print("=" * 50)
    
    try:
        from texttospeech.phonetics.llm_phonetic_coach import PhoneticOption, LLMResponse, LLMPhoneticCoach
        from texttospeech.phonetics.processing import PhoneticProcessor
        
        print("✅ Successfully imported LLM Coach modules")
        
        # Test 1: PhoneticOption
        print("\n📝 Test 1: PhoneticOption")
        print("-" * 30)
        
        option = PhoneticOption("American pronunciation", "/təˈmeɪtoʊ/")
        print(f"Option: {option}")
        print(f"Description: {option.description}")
        print(f"Phonetic: {option.phonetic}")
        
        # Test 2: LLMResponse JSON parsing
        print("\n📄 Test 2: LLMResponse JSON Parsing")
        print("-" * 30)
        
        test_json = {
            "general_text": "Here are some phonetic options for 'tomato':",
            "options": [
                {"description": "American pronunciation", "phonetic": "/təˈmeɪtoʊ/"},
                {"description": "British pronunciation", "phonetic": "/təˈmɑːtəʊ/"},
                {"description": "Simplified version", "phonetic": "tuh-MAY-toh"}
            ]
        }
        
        response = LLMResponse.from_json(test_json)
        print(f"General text: {response.general_text}")
        print(f"Number of options: {len(response.options)}")
        
        for i, opt in enumerate(response.options, 1):
            print(f"  {i}. {opt}")
        
        # Test 3: Mock TTS Manager for testing
        print("\n🔧 Test 3: Mock Integration Setup")
        print("-" * 30)
        
        class MockPhoneticManager:
            def __init__(self):
                self.current_word = None
                self.lookup_manager = MockLookupManager()
            
            def _play_phonetic_tts(self, word: str, phonetic: str) -> bool:
                print(f"  🎤 Mock TTS: Playing '{word}' with phonetic '{phonetic}'")
                return True
        
        class MockLookupManager:
            def add_pronunciation(self, word, phonetic, source):
                print(f"  💾 Mock Save: '{word}' -> '{phonetic}' (source: {source})")
        
        mock_manager = MockPhoneticManager()
        
        # Test 4: LLM Coach initialization
        print("\n🎓 Test 4: LLM Coach Initialization")
        print("-" * 30)
        
        coach = LLMPhoneticCoach(
            phonetic_manager=mock_manager,
            tts_backend="azure",
            voice_name="en-US-JennyNeural"
        )
        
        print(f"TTS Backend: {coach.tts_backend}")
        print(f"Voice Name: {coach.voice_name}")
        print(f"PhoneticProcessor initialized: {coach.phonetic_processor is not None}")
        
        # Test 5: Mock LLM responses for known words
        print("\n🧠 Test 5: Mock LLM Response Generation")
        print("-" * 30)
        
        test_words = ["hello", "tomato", "worcestershire"]
        
        for word in test_words:
            print(f"\nWord: {word}")
            response_json = coach._get_llm_response(word, "initial_suggestions")
            response = LLMResponse.from_json(response_json)
            print(f"  Response: {response.general_text[:60]}...")
            print(f"  Options: {len(response.options)}")
            
            for i, opt in enumerate(response.options[:2], 1):  # Show first 2
                print(f"    {i}. {opt.phonetic} - {opt.description}")
        
        print("\n✅ All LLM Coach component tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in LLM Coach tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the LLM Coach tests"""
    print("🧪 Enhanced LLM Coach Test Suite")
    print("=" * 40)
    
    success = test_llm_coach_components()
    
    if success:
        print("\n🎉 All tests passed! Enhanced LLM Coach is working!")
        print("\n💡 Next: The LLM Coach appears to be fully implemented!")
        print("   Ready for integration testing with real phonetic management.")
    else:
        print("\n⚠️  Some tests failed.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
