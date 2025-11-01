#!/usr/bin/env python3

import azure.cognitiveservices.speech as speechsdk
import yaml
import os
import tempfile
import soundfile as sf
import sounddevice as sd

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

azure_config = config.get('azure', {})
api_key = azure_config.get('api_key')
region = azure_config.get('region')
voice_name = azure_config.get('voice_name', 'en-US-JennyNeural')

print(f'🧪 Testing Azure TTS with voice: {voice_name}')
print(f'🔑 API Key: {api_key[:10]}...')
print(f'🌍 Region: {region}')

# Create speech config (following official example)
speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)

# Set voice name
speech_config.speech_synthesis_voice_name = voice_name

# Create temp file
with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
    temp_path = temp_file.name

print(f'📁 Output file: {temp_path}')

# Create audio config for file output (following official example)
file_config = speechsdk.audio.AudioOutputConfig(filename=temp_path)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)

# Test 1: Basic text synthesis
print('\n🔄 Test 1: Basic text synthesis...')
result = speech_synthesizer.speak_text_async('hello').get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print('✅ Basic TTS working!')
    
    # Play the basic result
    print('🔊 Playing basic TTS...')
    try:
        data, sample_rate = sf.read(temp_path)
        sd.play(data, sample_rate)
        sd.wait()
        print('✅ Basic playback complete!')
    except Exception as e:
        print(f'❌ Playback error: {e}')
    
    # Test 2: Simple SSML
    print('\n🔄 Test 2: Simple SSML...')
    simple_ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<voice name="en-US-JennyNeural">Hello world</voice>
</speak>'''
    
    ssml_result = speech_synthesizer.speak_ssml_async(simple_ssml).get()
    
    if ssml_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print('✅ Simple SSML working!')
        
        # Test 3: Phonetic SSML
        print('\n🔄 Test 3: Phonetic SSML...')
        phonetic_ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<voice name="en-US-JennyNeural">
<phoneme alphabet="ipa" ph="hɛloʊ">hello</phoneme>
</voice>
</speak>'''
        
        print(f'📝 Phonetic SSML: {phonetic_ssml.strip()}')
        
        phonetic_result = speech_synthesizer.speak_ssml_async(phonetic_ssml).get()
        
        if phonetic_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print('✅ Phonetic SSML working!')
            
            # Play the phonetic result
            print('🔊 Playing phonetic TTS...')
            try:
                data, sample_rate = sf.read(temp_path)
                sd.play(data, sample_rate)
                sd.wait()
                print('✅ Phonetic playback complete!')
            except Exception as e:
                print(f'❌ Phonetic playback error: {e}')
                
        elif phonetic_result.reason == speechsdk.ResultReason.Canceled:
            print('❌ Phonetic SSML failed')
            cancellation_details = phonetic_result.cancellation_details
            print(f'   Reason: {cancellation_details.reason}')
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f'   Error: {cancellation_details.error_details}')
        else:
            print(f'❌ Phonetic SSML failed: {phonetic_result.reason}')
    
    elif ssml_result.reason == speechsdk.ResultReason.Canceled:
        print('❌ Simple SSML failed')
        cancellation_details = ssml_result.cancellation_details
        print(f'   Reason: {cancellation_details.reason}')
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f'   Error: {cancellation_details.error_details}')
    else:
        print(f'❌ Simple SSML failed: {ssml_result.reason}')

elif result.reason == speechsdk.ResultReason.Canceled:
    print('❌ Basic TTS failed')
    cancellation_details = result.cancellation_details
    print(f'   Reason: {cancellation_details.reason}')
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print(f'   Error: {cancellation_details.error_details}')
else:
    print(f'❌ Basic TTS failed: {result.reason}')

# Clean up
try:
    os.remove(temp_path)
except:
    pass

print('\n🏁 Test complete!')
