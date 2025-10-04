#!/usr/bin/env python3
"""
Test the complete phonetic processing pipeline with markdown parsing.
This test validates the integration without requiring TTS API keys.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_markdown_phonetic_processing():
    """Test the full markdown + phonetic processing workflow"""
    print("🚀 Testing Complete Markdown + Phonetic Processing Pipeline")
    print("=" * 65)
    
    try:
        # Import our modules
        from texttospeech.processing.markdown_parser import process_markdown
        from texttospeech.phonetics.processing import PhoneticProcessor
        
        # Test markdown content with phonetic markup (no voice aliases needed)
        markdown_content = """# Phonetic Test Document

## Section 1: Basic Phonetics

Hello world! The word [ipa:təˈmeɪtoʊ]tomato[/ipa] can be pronounced differently.

## Section 2: Mixed Markup

I love eating [phonetic:tuh-MAH-toh]tomatoes[/phonetic] and [ipa:ˈwʊstərʃər]Worcestershire[/ipa] sauce.

## Section 3: Simple Phonetics

Regular text mixed with [ph:fuh-NET-ik]phonetic[/ph] markup should work seamlessly.
"""
        
        print("📄 Processing markdown content...")
        aliases, sections = process_markdown(markdown_content, default_voice="en-US-JennyNeural")
        
        print(f"✅ Found {len(sections)} sections")
        
        # Initialize phonetic processor
        processor = PhoneticProcessor(backend="azure", voice_name="en-US-JennyNeural")
        
        # Process each section
        for i, section in enumerate(sections, 1):
            print(f"\n📝 Section {i}: {section.title}")
            print(f"   File path: {section.file_path}")
            print(f"   Segments: {len(section.segments)}")
            
            for j, segment in enumerate(section.segments, 1):
                if segment.text.strip():
                    print(f"\n   Segment {j}: '{segment.text[:50]}{'...' if len(segment.text) > 50 else ''}'")
                    print(f"   Voice: {segment.voice or 'default'}")
                    
                    # Apply phonetic processing
                    is_ssml, processed_text = processor.preprocess_text(segment.text)
                    
                    if is_ssml:
                        print(f"   🎤 SSML Generated: {processed_text[:100]}{'...' if len(processed_text) > 100 else ''}")
                    else:
                        print(f"   📝 Plain text: {processed_text[:100]}{'...' if len(processed_text) > 100 else ''}")
        
        print(f"\n🎉 Successfully processed all {len(sections)} sections with phonetic markup!")
        return True
        
    except Exception as e:
        print(f"❌ Error in markdown phonetic processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_cli_integration():
    """Test direct CLI integration with phonetic processor"""
    print("\n🔗 Testing Direct CLI Integration")
    print("=" * 40)
    
    try:
        from texttospeech.phonetics.processing import PhoneticProcessor
        
        # Test various phonetic markups
        test_cases = [
            "Hello [ipa:wɜrld]world[/ipa]!",
            "I love [phonetic:tuh-MAY-toh]tomatoes[/phonetic].",
            "The [ph:WOR-ses-ter]Worcester[/ph] sauce is good.",
            "Regular text without any phonetic markup.",
            "Multiple [ipa:həˈloʊ]hello[/ipa] and [ipa:wɜrld]world[/ipa] phonetics."
        ]
        
        for backend in ["azure", "elevenlabs"]:
            print(f"\n🏭 Testing {backend.upper()} backend:")
            processor = PhoneticProcessor(backend=backend)
            
            for text in test_cases:
                is_ssml, processed = processor.preprocess_text(text)
                print(f"  Input:  {text}")
                print(f"  Output: {processed[:80]}{'...' if len(processed) > 80 else ''}")
                print(f"  Type:   {'SSML' if is_ssml else 'Text'}")
                print()
        
        print("✅ CLI integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in CLI integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("🧪 TextToSpeech Phonetic Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Markdown + Phonetic Processing", test_markdown_phonetic_processing),
        ("CLI Integration", test_direct_cli_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ PASSED: {test_name}")
        else:
            print(f"❌ FAILED: {test_name}")
    
    print(f"\n🏁 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Phonetic integration is working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
