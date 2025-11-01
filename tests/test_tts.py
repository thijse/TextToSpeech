#!/usr/bin/env python3

import azure.cognitiveservices.speech as speechsdk
import yaml

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

azure_config = config.get('azure', {})
api_key = azure_config.get('api_key')
region = azure_config.get('region')
voice_name = azure_config.get('voice_name', 'en-US-JennyNeural')

print(f'Testing basic TTS with voice: {voice_name}')

# Create speech config
speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
speech_config.speech_synthesis_voice_name = voice_name
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)

# Create audio config for file output
audio_config = speechsdk.audio.AudioOutputConfig(filename='tts_test.wav')
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Test basic text
print('Testing basic text synthesis...')
result = synthesizer.speak_text_async('hello').get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print('✅ Basic TTS working!')
    
    # Test phonetic SSML
    print('Testing phonetic SSML...')
    ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<phoneme alphabet="ipa" ph="hɛllɔ">hello</phoneme>
</speak>'''
    
    phonetic_result = synthesizer.speak_ssml_async(ssml).get()
    
    if phonetic_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print('✅ Phonetic TTS working!')
    else:
        print(f'❌ Phonetic TTS failed: {phonetic_result.reason}')
        if phonetic_result.reason == speechsdk.ResultReason.Canceled:
            details = speechsdk.CancellationDetails(phonetic_result)
            print(f'   Details: {details.reason}, {details.error_details}')
else:
    print(f'❌ Basic TTS failed: {result.reason}')
    if result.reason == speechsdk.ResultReason.Canceled:
        details = speechsdk.CancellationDetails(result)
        print(f'   Details: {details.reason}, {details.error_details}')
