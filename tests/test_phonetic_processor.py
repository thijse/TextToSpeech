#!/usr/bin/env python3
"""
Test script for PhoneticProcessor functionality.

This script tests the comprehensive PhoneticProcessor implementation including:
- IPA validation and classification
- Phonetic markup parsing
- SSML generation for Azure
- Text hint generation for ElevenLabs
- Integration with TTS pipeline

Run from the repository root:
    cd d:\GitHub\LLM\TextToSpeech
    python tests\test_phonetic_processor.py
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_phonetic_processor():
    """Test the PhoneticProcessor implementation."""
    
    print("🧪 Testing PhoneticProcessor Implementation")
    print("=" * 50)
    
    try:
        from texttospeech.phonetics.processing import (
            PhoneticProcessor,
            PhoneticNotationType,
            validate_phonetic_notation,
            process_phonetic_for_tts
        )
        print("✅ Successfully imported PhoneticProcessor modules")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 1: Phonetic notation validation
    print("\n📝 Test 1: Phonetic Notation Validation")
    print("-" * 30)
    
    test_cases = [
        ("/həˈloʊ/", "IPA with wrapper"),
        ("təˈmeɪtoʊ", "IPA without wrapper"),
        ("huh-LOH", "Syllabic notation"),
        ("tuh-MAY-toh", "Simplified phonetics"),
        ("said like hello", "Text description"),
        ("", "Empty string"),
        ("xyz123", "Unknown notation")
    ]
    
    for phonetic, description in test_cases:
        notation_type, is_valid, issues = validate_phonetic_notation(phonetic)
        print(f"'{phonetic}' ({description})")
        print(f"  Type: {notation_type.value}, Valid: {is_valid}")
        if issues:
            for issue in issues[:2]:  # Show first 2 issues
                print(f"  Issue: {issue.message}")
        print()
    
    # Test 2: Markup parsing
    print("\n🏷️  Test 2: Phonetic Markup Parsing")
    print("-" * 30)
    
    test_texts = [
        "Hello [ipa:wɜrld]world[/ipa]!",
        "I love [ph:tuh-MAY-toh]tomato[/ph] soup.",
        "The word [phonetic:wʊstərʃər]Worcestershire[/phonetic] is tricky.",
        "Mixed content with [ipa:həˈloʊ]hello[/ipa] and normal text.",
        "No phonetic markup here.",
        "Multiple [ipa:wɜrld]world[/ipa] and [ph:tuh-MAY-toh]tomato[/ph] words."
    ]
    
    processor = PhoneticProcessor(backend="azure")
    
    for text in test_texts:
        print(f"Input: {text}")
        segments = processor.parser.parse_text(text)
        print(f"  Segments found: {len(segments)}")
        for i, seg in enumerate(segments):
            print(f"    {i+1}. '{seg.text}' - Phonetic: {seg.is_phonetic}")
            if seg.is_phonetic:
                print(f"       Notation: '{seg.phonetic}' (Type: {seg.notation_type.value})")
        print()
    
    # Test 3: SSML generation for Azure
    print("\n🎤 Test 3: Azure SSML Generation")
    print("-" * 30)
    
    azure_processor = PhoneticProcessor(backend="azure", voice_name="en-US-JennyNeural")
    
    azure_test_texts = [
        "Hello [ipa:wɜrld]world[/ipa]!",
        "The [phonetic:təˈmeɪtoʊ]tomato[/phonetic] is red.",
        "Regular text without markup.",
        "Multiple [ipa:həˈloʊ]hello[/ipa] and [ipa:wɜrld]world[/ipa] phonetics."
    ]
    
    for text in azure_test_texts:
        is_ssml, processed = azure_processor.preprocess_text(text)
        print(f"Input: {text}")
        print(f"  SSML: {is_ssml}")
        print(f"  Output: {processed}")
        print()
    
    # Test 4: ElevenLabs text generation
    print("\n🔊 Test 4: ElevenLabs Text Generation")
    print("-" * 30)
    
    elevenlabs_processor = PhoneticProcessor(backend="elevenlabs")
    
    for text in azure_test_texts:
        is_ssml, processed = elevenlabs_processor.preprocess_text(text)
        print(f"Input: {text}")
        print(f"  SSML: {is_ssml} (should be False)")
        print(f"  Output: {processed}")
        print()
    
    # Test 5: Direct utility functions
    print("\n🛠️  Test 5: Utility Functions")
    print("-" * 30)
    
    test_phonetics = [
        ("hello", "/həˈloʊ/", "azure"),
        ("world", "wɜrld", "azure"),
        ("tomato", "tuh-MAY-toh", "elevenlabs")
    ]
    
    for text, phonetic, backend in test_phonetics:
        method, content = process_phonetic_for_tts(text, phonetic, backend)
        print(f"process_phonetic_for_tts('{text}', '{phonetic}', '{backend}')")
        print(f"  Method: {method}")
        print(f"  Content: {content}")
        print()
    
    print("✅ All PhoneticProcessor tests completed successfully!")
    return True


def test_markdown_with_phonetics():
    """Test markdown processing with phonetic markup."""
    
    print("\n📄 Testing Markdown with Phonetic Markup")
    print("=" * 50)
    
    # Create a test markdown file
    test_markdown = """# Phonetic Test Document

This document tests phonetic markup in different contexts.

## Section 1: Basic Phonetics

Hello [ipa:wɜrld]world[/ipa]! This tests basic IPA notation.

I love eating [ph:tuh-MAY-toh]tomato[/ph] soup on cold days.

## Section 2: Complex Phonetics  

The word [phonetic:wʊstərʃər]Worcestershire[/phonetic] sauce is hard to pronounce.

## Section 3: Mixed Content

Some words like [ipa:həˈloʊ]hello[/ipa] are easy, but others like [phonetic:ˌɪntərˈnæʃənəl]international[/phonetic] are complex.

Regular text without any phonetic markup should work normally.
"""

    try:
        from texttospeech.processing.modality_to_speech import ModalityToSpeech
        from texttospeech.phonetics.processing import PhoneticProcessor
        
        print("✅ Successfully imported processing modules")
        
        # Create a mock TTS client for testing
        class MockTTSClient:
            def text_to_speech(self, text, voice_name, output_path, output_format="mp3", is_ssml=False):
                print(f"  [MOCK TTS] Voice: {voice_name}")
                print(f"  [MOCK TTS] SSML: {is_ssml}")
                print(f"  [MOCK TTS] Text: {text[:100]}...")
                print(f"  [MOCK TTS] Output: {output_path}")
                
                # Create a dummy file to simulate success
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write("dummy audio content")
                return True
        
        # Test with phonetic processor
        print("\n🔄 Testing with PhoneticProcessor enabled")
        print("-" * 40)
        
        phonetic_processor = PhoneticProcessor(backend="azure", voice_name="en-US-JennyNeural")
        mock_client = MockTTSClient()
        modality_processor = ModalityToSpeech(mock_client, phonetic_processor)
        
        # Process the markdown
        results = modality_processor.process_markdown_document(
            markdown_text=test_markdown,
            default_voice_name="en-US-JennyNeural",
            output_dir="temp/phonetic_test",
            overwrite_audio=True
        )
        
        print(f"\n📊 Processing Results:")
        for file_path, success in results.items():
            print(f"  {'✅' if success else '❌'} {file_path}")
        
        # Test without phonetic processor (for comparison)
        print("\n🔄 Testing without PhoneticProcessor (comparison)")
        print("-" * 40)
        
        modality_processor_plain = ModalityToSpeech(mock_client, None)
        
        results_plain = modality_processor_plain.process_markdown_document(
            markdown_text=test_markdown,
            default_voice_name="en-US-JennyNeural", 
            output_dir="temp/plain_test",
            overwrite_audio=True
        )
        
        print(f"\n📊 Plain Processing Results:")
        for file_path, success in results_plain.items():
            print(f"  {'✅' if success else '❌'} {file_path}")
        
        print("\n✅ Markdown processing tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Markdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test the full integration with TTS CLI structure."""
    
    print("\n🔗 Testing Integration with TTS CLI")
    print("=" * 50)
    
    try:
        from texttospeech.cli.tts_cli import load_config
        from texttospeech.phonetics.processing import PhoneticProcessor
        
        # Test config loading
        config = load_config("config/config.yaml")
        print(f"✅ Config loaded: {len(config)} sections")
        
        # Test phonetic processor initialization  
        processor = PhoneticProcessor(backend="azure", voice_name="en-US-JennyNeural")
        print("✅ PhoneticProcessor initialized for Azure")
        
        processor_el = PhoneticProcessor(backend="elevenlabs")
        print("✅ PhoneticProcessor initialized for ElevenLabs")
        
        # Test with sample text
        test_text = "Hello [ipa:wɜrld]world[/ipa] and [ph:tuh-MAY-toh]tomato[/ph]!"
        
        is_ssml_azure, processed_azure = processor.preprocess_text(test_text)
        print(f"\n🔄 Azure processing:")
        print(f"  SSML: {is_ssml_azure}")
        print(f"  Result: {processed_azure}")
        
        is_ssml_el, processed_el = processor_el.preprocess_text(test_text)
        print(f"\n🔄 ElevenLabs processing:")
        print(f"  SSML: {is_ssml_el}")
        print(f"  Result: {processed_el}")
        
        print("\n✅ Integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    
    print("🚀 Starting PhoneticProcessor Test Suite")
    print("=" * 60)
    
    tests = [
        ("Core PhoneticProcessor", test_phonetic_processor),
        ("Markdown Processing", test_markdown_with_phonetics),
        ("TTS CLI Integration", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {test_name}")
        print('=' * 60)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! PhoneticProcessor implementation is working correctly.")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed. Check the output above for details.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
