"""
CFI Lab TTS Implementation Module

TTSInterface implementation that reaches the Azure neural voices through the CFI Lab LiteLLM proxy
(`POST /speech/tts`) instead of connecting to Azure Speech directly.
"""

import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .interface import TTSInterface

DEFAULT_BASE_URL = "https://litellm.cfilab.philips.com"
DEFAULT_VOICE = "en-US-JennyNeural"
DEFAULT_VOICE_LIST = "data/azure_voices.txt"

# The proxy builds <speak><voice> itself and rejects those, bare node lists and mstts:* as the JsonML root.
JSONML_ROOT = "p"

_OUTPUT_FORMATS = {
    "mp3": "audio-24khz-160kbitrate-mono-mp3",
    "wav": "riff-24khz-16bit-mono-pcm",
    "ogg": "ogg-24khz-16bit-mono-opus",
    "webm": "webm-24khz-16bit-mono-opus",
}

_NAMESPACE_PREFIXES = {
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/2001/mstts": "mstts",
}


def _to_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def load_cfi_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve CFI settings: `cfi` config section, then environment variables, then `cfi.env_file`."""
    cfg = dict(config.get("cfi") or {})
    file_env: Dict[str, Optional[str]] = {}
    if cfg.get("env_file"):
        from dotenv import dotenv_values
        file_env = dotenv_values(os.path.expanduser(str(cfg["env_file"])))

    def pick(key: str, env_name: str) -> Any:
        value = cfg.get(key)
        if value is not None and value != "" and not (isinstance(value, str) and value.startswith("<")):
            return value
        return os.environ.get(env_name) or file_env.get(env_name)

    return {
        "base_url": str(pick("base_url", "PROXY_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"),
        "api_key": pick("api_key", "LITELLM_API_KEY"),
        "ssl_verify": _to_bool(pick("ssl_verify", "SSL_VERIFY"), True),
        "voice_name": cfg.get("voice_name") or (config.get("azure") or {}).get("voice_name") or DEFAULT_VOICE,
        "voice_list": cfg.get("voice_list") or DEFAULT_VOICE_LIST,
        "chat_model": cfg.get("chat_model") or "gpt-5",
        "transcribe_model": cfg.get("transcribe_model") or "gpt-4o-mini-transcribe",
        # gpt-5 spends most of this on reasoning; 4000 often left nothing for the coach's JSON answer.
        "max_completion_tokens": int(cfg.get("max_completion_tokens") or 16000),
    }


def make_openai_client(settings: Dict[str, Any], timeout: float = 300.0):
    """OpenAI SDK client pointed at the CFI Lab proxy (chat completions, transcriptions)."""
    from openai import OpenAI

    return OpenAI(
        base_url=f"{settings['base_url']}/v1",
        api_key=settings["api_key"],
        http_client=httpx.Client(verify=settings["ssl_verify"], timeout=timeout),
    )


def _qualified_name(name: str) -> str:
    if name.startswith("{"):
        uri, local = name[1:].split("}", 1)
        prefix = _NAMESPACE_PREFIXES.get(uri)
        return f"{prefix}:{local}" if prefix else local
    return name


def _jsonml_children(element: ET.Element) -> List[Any]:
    children: List[Any] = []
    if element.text:
        children.append(element.text)
    for child in element:
        children.append(_jsonml_element(child))
        if child.tail:
            children.append(child.tail)
    return children


def _jsonml_element(element: ET.Element) -> List[Any]:
    attributes = {_qualified_name(k): v for k, v in element.attrib.items()}
    return [_qualified_name(element.tag), attributes, *_jsonml_children(element)]


def ssml_to_jsonml(ssml: str) -> Tuple[Optional[str], List[Any]]:
    """Convert an SSML document or fragment to the proxy's JsonML; returns (voice from <voice>, jsonml)."""
    source = ssml.strip()
    if not source.startswith("<speak"):
        source = ('<speak xmlns="http://www.w3.org/2001/10/synthesis" '
                  f'xmlns:mstts="http://www.w3.org/2001/mstts">{source}</speak>')
    root = ET.fromstring(source)
    body, voice = root, None
    elements = list(root)
    if (len(elements) == 1 and _qualified_name(elements[0].tag) == "voice"
            and not (root.text or "").strip() and not (elements[0].tail or "").strip()):
        body, voice = elements[0], elements[0].get("name")
    return voice, [JSONML_ROOT, {}, *_jsonml_children(body)]


def to_azure_output_format(output_format: Optional[str]) -> str:
    """Map the app's format names (mp3, wav, mp3_44100_128, ...) to Azure output format names."""
    if not output_format:
        return _OUTPUT_FORMATS["mp3"]
    fmt = output_format.lower()
    if fmt in _OUTPUT_FORMATS:
        return _OUTPUT_FORMATS[fmt]
    if fmt.startswith("mp3"):
        return _OUTPUT_FORMATS["mp3"]
    return output_format


class CfiVoice:
    """A voice from the static voice catalog, shaped like AzureVoice."""

    def __init__(self, voice_id: str, locale: str, gender: str):
        self.voice_id = voice_id
        self.name = voice_id
        self.locale = locale
        self.gender = gender
        self.style_list: List[str] = []
        self.category = "azure"
        self.description = f"{locale} {gender} voice"
        self.labels = {"locale": locale, "gender": gender}


class CfiVoicesResponse:
    def __init__(self, voices: List[CfiVoice]):
        self.voices = voices


class CfiSpeechTTS(TTSInterface):
    """Azure neural voices through the CFI Lab proxy."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, voice_name: str = DEFAULT_VOICE,
                 ssl_verify: bool = True, voice_list_path: str = DEFAULT_VOICE_LIST, timeout: float = 120.0,
                 http_client: Optional[httpx.Client] = None):
        self.voice_name = voice_name
        self.default_voice_name = voice_name
        self.voice_list_path = voice_list_path
        self._http = http_client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            verify=ssl_verify,
        )
        self._voices_cache: Optional[CfiVoicesResponse] = None

    @classmethod
    def from_settings(cls, settings: Dict[str, Any]) -> "CfiSpeechTTS":
        return cls(
            api_key=settings["api_key"],
            base_url=settings["base_url"],
            voice_name=settings["voice_name"],
            ssl_verify=settings["ssl_verify"],
            voice_list_path=settings["voice_list"],
        )

    def get_voices(self):
        """The proxy has no voice-list endpoint, so voices come from a static catalog file."""
        if self._voices_cache:
            return self._voices_cache
        try:
            voices = []
            with open(self.voice_list_path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    voice_id, _, comment = line.partition("#")
                    voice_id = voice_id.strip()
                    if not voice_id:
                        continue
                    fields = [part.strip() for part in comment.split(",")]
                    locale = fields[1] if len(fields) > 1 else "Unknown"
                    gender = fields[2] if len(fields) > 2 else "Unknown"
                    voices.append(CfiVoice(voice_id, locale, gender))
            self._voices_cache = CfiVoicesResponse(voices)
            return self._voices_cache
        except Exception as e:
            print(f"Error reading voice list '{self.voice_list_path}': {e}")
            return None

    def get_voice_details(self, voice_id):
        response = self.get_voices()
        if not response:
            return None
        for voice in response.voices:
            if voice.voice_id == voice_id:
                return voice
        return None

    def find_voice_by_name(self, voice_name):
        response = self.get_voices()
        if not response:
            return None
        for voice in response.voices:
            if voice.name.lower() == voice_name.lower():
                return voice.voice_id
        return None

    def text_to_speech(self, text, voice_name, output_path, output_format="mp3", is_ssml=False):
        voice = voice_name or self.voice_name
        payload: Dict[str, Any] = {"voice": voice, "output_format": to_azure_output_format(output_format)}
        try:
            if is_ssml:
                ssml_voice, payload["ssml"] = ssml_to_jsonml(text)
                payload["voice"] = voice_name or ssml_voice or self.voice_name
            else:
                payload["text"] = text
        except ET.ParseError as e:
            print(f"Error generating speech: invalid SSML ({e})")
            return False

        print(f"Generating speech using voice '{payload['voice']}' ({'SSML' if is_ssml else 'text'}) via CFI Lab...")
        try:
            response = self._http.post("/speech/tts", json=payload)
        except httpx.HTTPError as e:
            print(f"Error generating speech: {e}")
            return False
        if response.status_code >= 400:
            print(f"Error generating speech: HTTP {response.status_code}: {response.text[:300]}")
            return False
        try:
            with open(output_path, "wb") as f:
                f.write(response.content)
        except OSError as e:
            print(f"Error writing audio to '{output_path}': {e}")
            return False
        print(f"Speech generated and saved to '{output_path}'.")
        return True
