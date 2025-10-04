#!/usr/bin/env python3
"""
Test the markdown parser with default voice functionality
"""

import sys
import os
sys.path.insert(0, 'src')

def test_markdown_parser_with_default_voice():
    """Test the updated markdown parser with default voice support"""
    print("🧪 Testing Markdown Parser with Default Voice")
    print("=" * 50)
    
    try:
        from texttospeech.processing.markdown_parser import process_markdown
        
        # Test markdown content without voice aliases
        markdown_content = """# Phonetic Test Document

## Section 1: Basic Phonetics

Hello world! The word [ipa:təˈmeɪtoʊ]tomato[/ipa] can be pronounced differently.

## Section 2: Mixed Markup

I love eating [phonetic:tuh-MAH-toh]tomatoes[/phonetic] and [ipa:ˈwʊstərʃər]Worcestershire[/ipa] sauce.

## Section 3: Simple Phonetics

Regular text mixed with [ph:fuh-NET-ik]phonetic[/ph] markup should work seamlessly.
"""
        
        print("📄 Testing without default voice...")
        aliases, sections = process_markdown(markdown_content)
        print(f"  Aliases found: {len(aliases)}")
        print(f"  Sections found: {len(sections)}")
        
        print("\n📄 Testing with default voice...")
        aliases, sections = process_markdown(markdown_content, default_voice="en-US-JennyNeural")
        print(f"  Aliases found: {len(aliases)}")
        print(f"  Sections found: {len(sections)}")
        
        if sections:
            print(f"\n📋 Section details:")
            for i, section in enumerate(sections, 1):
                print(f"  Section {i}: {section.title}")
                print(f"    File: {section.file_path}")
                print(f"    Segments: {len(section.segments)}")
                for j, segment in enumerate(section.segments, 1):
                    print(f"      Segment {j}: Voice='{segment.voice}', Text='{segment.text[:50]}...'")
        
        print("\n✅ Markdown parser test completed!")
        return len(sections) > 0
        
    except Exception as e:
        print(f"❌ Error in markdown parser test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phonetic_processing():
    """Test the phonetic processing separately"""
    print("\n🔧 Testing Phonetic Processing")
    print("=" * 35)
    
    try:
        from texttospeech.phonetics.processing import PhoneticProcessor
        
        processor = PhoneticProcessor(backend="azure")
        
        test_texts = [
            "Hello [ipa:təˈmeɪtoʊ]tomato[/ipa] world!",
            "Regular text without markup.",
            "Multiple [ipa:həˈloʊ]hello[/ipa] and [ph:wərld]world[/ph] phonetics."
        ]
        
        for text in test_texts:
            print(f"\nInput: {text}")
            is_ssml, processed = processor.preprocess_text(text)
            print(f"SSML: {is_ssml}")
            print(f"Output: {processed[:80]}{'...' if len(processed) > 80 else ''}")
        
        print("\n✅ Phonetic processing test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in phonetic processing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the focused tests"""
    print("🎯 Focused Markdown + Phonetic Tests")
    print("=" * 40)
    
    tests = [
        ("Markdown Parser with Default Voice", test_markdown_parser_with_default_voice),
        ("Phonetic Processing", test_phonetic_processing),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
            print(f"✅ PASSED: {test_name}")
        else:
            print(f"❌ FAILED: {test_name}")
    
    print(f"\n🏁 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All focused tests passed! The fix is working!")
    else:
        print("⚠️  Some tests failed.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
