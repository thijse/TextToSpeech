#!/usr/bin/env python3
"""
Test script to verify our phonetic classification fix.
"""

import sys
sys.path.append('src')

from texttospeech.phonetics.processing import process_phonetic_for_tts, validate_phonetic_notation

def test_phonetic_processing():
    """Test the fixed phonetic processing with problematic cases."""
    
    test_cases = [
        ("WUSS-ter-shur", "Should be syllabic"),
        ("WUU-stuh-shuh", "Should be syllabic"),
        ("/ˈwʊstəʃə/", "Should be IPA"),
        ("təˈmeɪtoʊ", "Should be IPA"),
        ("tuh-MAY-toh", "Should be syllabic"),
    ]
    
    print("🔍 Testing Phonetic Classification and Processing")
    print("=" * 60)
    
    for phonetic, expected in test_cases:
        print(f"\nTesting: '{phonetic}' ({expected})")
        
        # Test classification
        notation_type, is_valid, issues = validate_phonetic_notation(phonetic)
        print(f"  Classification: {notation_type.value} (valid: {is_valid})")
        
        if issues:
            print(f"  Issues: {[issue.message for issue in issues[:3]]}")
        
        # Test processing for TTS
        try:
            method, content = process_phonetic_for_tts("worcestershire", phonetic, "azure")
            print(f"  TTS Method: {method}")
            print(f"  Generated SSML/Text: {content[:100]}...")
            
            # Check if it contains proper tags
            if method == "ssml":
                if "<phoneme" in content:
                    print("  ✅ Uses <phoneme> tag (correct for IPA)")
                elif "<emphasis" in content:
                    print("  ✅ Uses <emphasis> tag (correct for syllabic)")
                else:
                    print("  ⚠️  Unknown SSML structure")
            else:
                print("  ✅ Uses plain text (fallback)")
                
        except Exception as e:
            print(f"  ❌ Error processing: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_phonetic_processing()
