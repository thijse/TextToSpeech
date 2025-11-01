"""
Phonetic Lookup Manager with overlay support (general + personal).

Loads a tracked general JSON and a gitignored personal JSON, overlays them at runtime,
with personal entries overriding general ones. Saves only to the personal file.
"""

from typing import Dict, Optional, List, Tuple
import os
import json
import re
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PhoneticEntry:
    """Represents a custom phonetic pronunciation entry."""
    word: str
    phonetic: str
    source: str = "custom"
    confidence: float = 1.0
    created_date: str = ""
 
    def __post_init__(self):
        self.word = self.word.lower()
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "word": self.word,
            "phonetic": self.phonetic,
            "source": self.source,
            "confidence": self.confidence,
            "created_date": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PhoneticEntry":
        return cls(
            word=data.get("word", ""),
            phonetic=data.get("phonetic", ""),
            source=data.get("source", "custom"),
            confidence=float(data.get("confidence", 1.0)),
            created_date=data.get("created_date", ""),
        )


class PhoneticLookupManager:
    """
    Manages phonetic pronunciations with overlay semantics:
    - Loads general and personal JSON files
    - Personal overrides general
    - Saves only to personal
    """

    def __init__(
        self,
        general_path: str = "data/phonetic_lookup.json",
        personal_path: str = "data/phonetic_lookup.personal.json",
        auto_create: bool = True,
        verbose: bool = True,
    ):
        self.general_path = general_path
        self.personal_path = personal_path
        self.auto_create = auto_create
        self.verbose = verbose
        self._general: Dict[str, PhoneticEntry] = {}
        self._personal: Dict[str, PhoneticEntry] = {}
        self.load()

    @property
    def combined(self) -> Dict[str, PhoneticEntry]:
        """Overlay personal over general and return a new mapping."""
        result = dict(self._general)
        result.update(self._personal)
        return result

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _ensure_dir(self, path: str):
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def load(self):
        """Load both general and personal files."""
        self._general = self._load_file(self.general_path, label="general")
        self._personal = self._load_file(self.personal_path, label="personal")
        # After load, normalize stored phonetics for consistency
        for bucket in (self._general, self._personal):
            for w, entry in bucket.items():
                entry.phonetic = self._normalize_and_wrap(entry.phonetic)

    def _load_file(self, path: str, label: str) -> Dict[str, PhoneticEntry]:
        entries: Dict[str, PhoneticEntry] = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for word, entry_data in data.items():
                    entries[word.lower()] = PhoneticEntry.from_dict(entry_data)
                self._log(f"📚 Loaded {len(entries)} {label} pronunciation(s) from {path}")
            except Exception as e:
                self._log(f"❌ Error loading {label} pronunciations from {path}: {e}")
        else:
            if label == "personal" and self.auto_create:
                # Create an empty personal file on first save; not now.
                self._log(f"ℹ️ Personal file not found at {path}. It will be created on first save.")
            else:
                self._log(f"ℹ️ {label.capitalize()} file not found at {path}.")
        return entries

    def save(self):
        """Persist only personal pronunciations."""
        try:
            self._ensure_dir(self.personal_path)
            data = {w: e.to_dict() for w, e in sorted(self._personal.items())}
            with open(self.personal_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._log(f"💾 Saved {len(self._personal)} personal pronunciation(s) to {self.personal_path}")
        except Exception as e:
            self._log(f"❌ Error saving personal pronunciations: {e}")

    # CRUD operations (operate on overlay but write to personal)
    def add_pronunciation(self, word: str, phonetic: str, source: str = "custom", confidence: float = 1.0):
        """Add/update a pronunciation in personal overlay."""
        entry = PhoneticEntry(word=word, phonetic=self._normalize_and_wrap(phonetic), source=source, confidence=confidence)
        self._personal[entry.word] = entry
        self.save()

    def remove_pronunciation(self, word: str):
        """Remove a pronunciation from personal overlay only."""
        key = word.lower()
        if key in self._personal:
            del self._personal[key]
            self.save()
            self._log(f"🗑️  Removed personal pronunciation for '{word}'")
        else:
            self._log(f"❌ No personal pronunciation found for '{word}'")

    def has_pronunciation(self, word: str) -> bool:
        return word.lower() in self.combined

    def get_pronunciation(self, word: str) -> Optional[PhoneticEntry]:
        return self.combined.get(word.lower())

    def list_pronunciations(self):
        """List combined pronunciations with origin labels."""
        combined = self.combined
        if not combined:
            print("📭 No custom pronunciations found.")
            return
        print(f"\n📚 Custom Pronunciations ({len(combined)}):")
        print("=" * 60)
        for word in sorted(combined.keys()):
            entry = combined[word]
            origin = "personal" if word in self._personal else "general"
            print(f"{word:20} -> {entry.phonetic:25} ({origin}:{entry.source})")
        print()

    # Text application helpers
    def apply_to_text_azure(self, text: str) -> str:
        """
        Apply custom pronunciations to text for Azure TTS using SSML <phoneme>.
        Wraps the provided text in a minimal <speak> container if needed.
        """
        entries = self.combined
        if not entries:
            return text
        # Ensure wrapped in speak
        if not text.strip().startswith("<speak"):
            ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">{text}</speak>'
        else:
            ssml_text = text
        for word, entry in entries.items():
            core = self._extract_core(entry.phonetic)
            pattern = r"\b" + re.escape(word) + r"\b"
            replacement = f'<phoneme alphabet="ipa" ph="{core}">{word}</phoneme>'
            ssml_text = re.sub(pattern, replacement, ssml_text, flags=re.IGNORECASE)
        return ssml_text

    def apply_to_text_elevenlabs(self, text: str) -> str:
        """
        Apply custom pronunciations to plain text for ElevenLabs by inserting hints.
        """
        entries = self.combined
        if not entries:
            return text
        result_text = text
        for word, entry in entries.items():
            core = self._extract_core(entry.phonetic)
            pattern = r"\b" + re.escape(word) + r"\b"
            replacement = f"{word} ({core})"
            result_text = re.sub(pattern, replacement, result_text, flags=re.IGNORECASE)
        return result_text

    # ----------------- Sanity / Normalization Utilities -----------------
    _IPA_TAG_RE = re.compile(r"^\[ipa:.*?]$", re.IGNORECASE)
    _PRON_TAG_RE = re.compile(r"^\[(pron|phon|ph):.*?]$", re.IGNORECASE)

    def _extract_core(self, phonetic: str) -> str:
        """Return the inner phonetic content without our wrapper or surrounding slashes."""
        if phonetic.startswith('[') and phonetic.endswith(']') and ':' in phonetic:
            phonetic = phonetic.split(':', 1)[1][:-1]  # drop leading tag + trailing ]
        # Strip surrounding slashes if user saved /ipa/
        if phonetic.startswith('/') and phonetic.endswith('/') and len(phonetic) > 2:
            phonetic = phonetic[1:-1]
        return phonetic.strip()

    def _detect_notation_kind(self, core: str) -> str:
        """Lightweight heuristic: decide if looks like IPA vs mnemonic pron guide."""
        # IPA core: presence of typical IPA chars
        if re.search(r"[ˈˌɪʊəɜʒʃθðɑæɔɹŋː]", core):
            return 'ipa'
        # If only letters, dashes, caps → pron guide
        if re.fullmatch(r"[A-Za-z\-\s']+", core):
            return 'pron'
        return 'unknown'

    def _normalize_and_wrap(self, raw: str) -> str:
        """Normalize any incoming phonetic notation and ensure single appropriate wrapper.

        Rules:
        - If already [ipa:...] or [pron:...] (case-insensitive), canonicalize tag to lowercase
        - If bare IPA → wrap as [ipa:...]
        - If looks like pron guide (EYE-vuss) → wrap as [pron:...]
        - Remove redundant surrounding slashes /.../
        - Collapse internal whitespace
        """
        if not raw:
            return raw
        s = raw.strip()
        # Remove accidental double wrapping like [ipa:[ipa:...]]
        for _ in range(2):  # at most two unravel passes
            if self._IPA_TAG_RE.match(s) and s.lower().count('[ipa:') > 1:
                inner = self._extract_core(s)
                s = f"[ipa:{inner}]"
        # If already wrapped once correctly, just normalize case
        if s.startswith('[ipa:') and s.endswith(']'):
            inner = self._extract_core(s)
            return f"[ipa:{inner}]"
        if re.match(r"^\[pron:.*?]$", s, re.IGNORECASE):
            inner = self._extract_core(s)
            return f"[pron:{inner}]"
        # Strip outer slashes
        if s.startswith('[') and ':' in s and s.endswith(']'):
            # Unknown tag, unwrap and proceed
            s = self._extract_core(s)
        if s.startswith('/') and s.endswith('/') and len(s) > 2:
            s = s[1:-1]
        s = re.sub(r"\s+", " ", s)
        kind = self._detect_notation_kind(s)
        if kind == 'ipa':
            return f"[ipa:{s}]"
        if kind == 'pron':
            return f"[pron:{s}]"
        # Fallback: assume ipa to keep pipeline working, flag could be added later
        return f"[ipa:{s}]"

    def sanitize_llm_options(self, options: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Given raw LLM options (each with 'phonetic'), return sanitized list with canonical wrappers.

        Also deduplicates based on (phonetic core, tag type).
        """
        seen: set[Tuple[str, str]] = set()
        sanitized = []
        for opt in options:
            ph = opt.get('phonetic', '')
            wrapped = self._normalize_and_wrap(ph)
            core = self._extract_core(wrapped)
            tag = 'ipa' if wrapped.startswith('[ipa:') else 'pron'
            key = (core, tag)
            if key in seen:
                continue
            seen.add(key)
            sanitized.append({
                **opt,
                'phonetic': wrapped
            })
        return sanitized

    # ----------------- Coach support helpers -----------------
    def get_existing_for_coach(self, word: str) -> List[Dict[str, str]]:
        """Return existing pronunciations for coach consumption.

        Always returns canonical wrapped phonetics.
        Multiple distinct variants (ipa vs pron) will be returned if present.
        """
        variants = []
        w = word.lower()
        if w in self._general:
            variants.append({
                'source': 'general',
                'phonetic': self._normalize_and_wrap(self._general[w].phonetic),
                'description': 'Previously saved (general)'
            })
        if w in self._personal:
            variants.append({
                'source': 'personal',
                'phonetic': self._normalize_and_wrap(self._personal[w].phonetic),
                'description': 'Previously saved (personal)'
            })
        # Deduplicate by core value
        dedup = {}
        for v in variants:
            core = self._extract_core(v['phonetic'])
            if core not in dedup:
                dedup[core] = v
        return list(dedup.values())


__all__ = [
    "PhoneticEntry",
    "PhoneticLookupManager",
]