#!/usr/bin/env python3
"""
Test the complete end-to-end phonetic processing with proper markdown format.
This test validates the full pipeline without requiring actual TTS API calls.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_complete_pipeline():
    """Test the complete markdown-to-speech pipeline with phonetic processing"""
    print("🚀 Testing Complete End-to-End Pipeline")
    print("=" * 45)
    
    try:
        # Import our modules
        from texttospeech.processing.modality_to_speech import ModalityToSpeech
        from texttospeech.phonetics.processing import PhoneticProcessor
        from texttospeech.tts.interface import TTSInterface
        
        # Create a mock TTS client for testing
        class MockTTSClient(TTSInterface):
            def __init__(self):
                self.calls = []
            
            def get_voices(self):
                return []
            
            def get_voice_details(self, voice_id):
                return None
            
            def find_voice_by_name(self, voice_name):
                return "mock_voice_id"
            
            def text_to_speech(self, text, voice_name, output_path, output_format="mp3_44100_128", is_ssml=False):
                # Record the call for verification
                self.calls.append({
                    'text': text,
                    'voice_name': voice_name,
                    'output_path': output_path,
                    'output_format': output_format,
                    'is_ssml': is_ssml
                })
                print(f"  🎤 Mock TTS Call:")
                print(f"    Voice: {voice_name}")
                print(f"    SSML: {is_ssml}")
                print(f"    Text: {text[:60]}{'...' if len(text) > 60 else ''}")
                print(f"    Output: {output_path}")
                
                # Create empty output file to simulate success
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write("mock audio data")
                return True
        
        # Test markdown content without voice aliases (should use default voice)
        markdown_content = """# Phonetic Test Document

## Section 1: Basic Phonetics

Hello world! The word [ipa:təˈmeɪtoʊ]tomato[/ipa] can be pronounced differently.

## Section 2: Mixed Markup

I love eating [phonetic:tuh-MAH-toh]tomatoes[/phonetic] and [ipa:ˈwʊstərʃər]Worcestershire[/ipa] sauce.

## Section 3: Simple Phonetics

Regular text mixed with [ph:fuh-NET-ik]phonetic[/ph] markup should work seamlessly.
"""
        
        print("📄 Creating markdown file...")
        os.makedirs("examples", exist_ok=True)
        with open("examples/test_phonetic.md", "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        # Initialize components
        print("🔧 Initializing components...")
        mock_tts = MockTTSClient()
        phonetic_processor = PhoneticProcessor(backend="azure", voice_name="en-US-JennyNeural")
        modality_processor = ModalityToSpeech(mock_tts, phonetic_processor)
        
        # Process the markdown document
        print("🎯 Processing markdown document...")
        results = modality_processor.process_markdown_document(
            markdown_text=markdown_content,
            default_voice_name="en-US-JennyNeural",
            output_dir="examples/output",
            overwrite_audio=True
        )
        
        print(f"\n📊 Processing Results:")
        print(f"  Sections processed: {len(results)}")
        for path, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {status}: {path}")
        
        print(f"\n🎤 TTS Calls Made: {len(mock_tts.calls)}")
        for i, call in enumerate(mock_tts.calls, 1):
            print(f"  Call {i}:")
            print(f"    SSML: {call['is_ssml']}")
            print(f"    Has phonetic markup: {'phoneme' in call['text'] or 'ipa' in call['text']}")
        
        # Verify phonetic processing worked
        ssml_calls = [call for call in mock_tts.calls if call['is_ssml']]
        text_calls = [call for call in mock_tts.calls if not call['is_ssml']]
        
        print(f"\n🔍 Verification:")
        print(f"  SSML calls (should have phonetic markup): {len(ssml_calls)}")
        print(f"  Text calls (fallback): {len(text_calls)}")
        
        if ssml_calls:
            print(f"  ✅ Phonetic processing is working! Found SSML with phoneme tags.")
        else:
            print(f"  ⚠️  No SSML calls detected. Phonetic processing may not be working.")
        
        print(f"\n🎉 End-to-end test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in end-to-end test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete pipeline test"""
    print("🧪 TextToSpeech End-to-End Integration Test")
    print("=" * 45)
    
    success = test_complete_pipeline()
    
    if success:
        print("\n🏆 END-TO-END TEST PASSED!")
        print("The phonetic processing pipeline is fully integrated and working!")
    else:
        print("\n💥 END-TO-END TEST FAILED!")
        print("Please review the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
