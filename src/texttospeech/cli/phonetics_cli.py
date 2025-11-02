"""
Phonetics CLI (package entrypoint)

Usage via module:
  python -m texttospeech.cli.phonetics_cli [options]

This CLI wraps the InteractivePhoneticManager living under:
  texttospeech.phonetics.phonetic_word_manager

Notes:
- This is a streamlined CLI focussed on the core flows (interactive, record, list, remove, test).
- Advanced audio device configuration and diagnostic flows remain available in the legacy
  root-level CLI (cli_phonetic_word_manager.py) during the migration phases.
"""

import sys
import argparse
import os

from texttospeech.phonetics.phonetic_word_manager import InteractivePhoneticManager
from texttospeech.phonetics.llm_phonetic_coach import LLMPhoneticCoach
from texttospeech.phonetics.processing import PhoneticNotationValidator


def display_usage():
    """Print usage and examples for the package CLI."""
    print("🎙️  Phonetic Word Manager (Package CLI)")
    print("========================================\n")
    print("This tool helps you record custom pronunciations and manage")
    print("phonetic lookup tables for Text-to-Speech applications.\n")

    print("Usage:")
    print("  python -m texttospeech.cli.phonetics_cli [options]\n")

    print("Options:")
    print("  --interactive, -i          Launch interactive mode")
    print("  --record, -r WORD          Record pronunciation for a specific word")
    print("  --list, -l                 List all saved pronunciations (overlayed: general+personal)")
    print("  --remove WORD              Remove PERSONAL pronunciation for a specific word")
    print("  --test, -t WORD            Test pronunciation playback for a specific word")
    print("  --coach WORD               Start an LLM coaching session for a specific word")
    print("  --coach-record             Record a baseline before starting LLM coach")
    print("  --config, -c CONFIG_FILE   Path to configuration file (default: config/config.yaml)")
    print("  --help, -h                 Show this help message\n")

    print("Examples:")
    print("  python -m texttospeech.cli.phonetics_cli --interactive")
    print("  python -m texttospeech.cli.phonetics_cli --record tomato")
    print("  python -m texttospeech.cli.phonetics_cli --list")
    print("  python -m texttospeech.cli.phonetics_cli --test tomato")
    print("  python -m texttospeech.cli.phonetics_cli --remove tomato")
    print("  python -m texttospeech.cli.phonetics_cli --coach worcestershire\n")

    print("Notes:")
    print("  - Overlay semantics for pronunciations:")
    print("      general:  data/phonetic_lookup.json        (tracked in VCS)")
    print("      personal: data/phonetic_lookup.personal.json (gitignored; overrides general)")
    print("  - Advanced audio device setup and diagnostics remain available in the legacy CLI")
    print("    at repository root (cli_phonetic_word_manager.py) during migration.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Phonetic Word Manager (package CLI) - Record and manage custom pronunciations",
        add_help=False,
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Launch interactive mode",
    )
    parser.add_argument(
        "--record",
        "-r",
        metavar="WORD",
        help="Record pronunciation for a specific word",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all saved pronunciations",
    )
    parser.add_argument(
        "--remove",
        metavar="WORD",
        help="Remove PERSONAL pronunciation for a specific word",
    )
    parser.add_argument(
        "--test",
        "-t",
        metavar="WORD",
        help="Test pronunciation playback for a specific word",
    )
    parser.add_argument(
        "--coach",
        metavar="WORD",
        help="Start an LLM coaching session for a specific word",
    )
    parser.add_argument(
        "--coach-record",
        action="store_true",
        help="Record a baseline before starting LLM coach",
    )
    parser.add_argument(
        "--config",
        "-c",
        metavar="CONFIG_FILE",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )
    parser.add_argument(
        "--help",
        "-h",
        action="store_true",
        help="Show this help message",
    )

    args = parser.parse_args()

    if args.help or len(sys.argv) == 1:
        display_usage()
        return

    try:
        manager = InteractivePhoneticManager(config_path=args.config)

        if args.interactive:
            manager.interactive_menu()
            return

        if args.record:
            manager.record_word_workflow(args.record)
            return

        if args.list:
            manager.lookup_manager.list_pronunciations()
            return

        if args.remove:
            # Removes ONLY personal override; general entries remain intact.
            manager.lookup_manager.remove_pronunciation(args.remove)
            return

        if args.test:
            entry = manager.lookup_manager.get_pronunciation(args.test)
            if entry:
                print(f"Testing pronunciation for '{args.test}': {entry.phonetic}")
                # Use unified processing pipeline like LLM Coach
                manager._play_phonetic_unified(args.test, entry.phonetic)
            else:
                print(f"❌ No pronunciation found for '{args.test}'")
            return

        if args.coach:
            baseline = None
            if getattr(args, "coach_record", False):
                # Record a baseline and extract phonetics before coaching
                audio_file = manager.recorder.record_word(duration=3.0)
                if audio_file:
                    try:
                        result = manager.extractor.extract_phonetics_from_audio(audio_file, expected_word=args.coach)
                        if result:
                            recognized_text, phonetic = result
                            # Normalize wrapper via lookup manager when available
                            try:
                                baseline = manager.lookup_manager._normalize_and_wrap(phonetic)
                            except Exception:
                                # Fallback: classify and wrap
                                nt = PhoneticNotationValidator.classify_notation(phonetic or recognized_text)
                                if nt.value == "ipa":
                                    baseline = f"[ipa:{phonetic}]"
                                else:
                                    baseline = f"[pron:{phonetic}]"
                    finally:
                        try:
                            os.remove(audio_file)
                        except Exception:
                            pass
            coach = LLMPhoneticCoach(manager)
            coach.start_coaching_session(args.coach, baseline=baseline)
            return

        # If no recognized action was provided, show usage
        display_usage()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
 