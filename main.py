#Main Usage <- While I polish and write README
#--translate from [] --translate-to []

#Based on KoljiBs RealtimeSTT implementation of Whisper.

EXTENDED_LOGGING = False
WRITE_TO_KEYBOARD_INTERVAL = 0.002  

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Real-time STT with optional translation.')

    parser.add_argument('-m', '--model', type=str, help='Main Whisper model (e.g. large-v2, medium, small).')
    parser.add_argument('-r', '--rt-model', '--realtime_model_type', type=str,
                        help='Realtime model (e.g. tiny, base, small — avoid .en variants for non-English).')
    parser.add_argument('-l', '--lang', '--language', type=str, help='Input language code (e.g. es, en, fr).')
    parser.add_argument('--translate-from', type=str, help='Alias for --lang.')
    parser.add_argument('--translate-to', type=str, default=None, help='Target language code for translation.')
    parser.add_argument('-d', '--root', type=str, help='Whisper model cache/download directory.')

    if EXTENDED_LOGGING:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    from rich.console import Console
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    from RealtimeSTT import AudioToTextRecorder
    from deep_translator import GoogleTranslator
    import pyautogui
    import os
    import sys
    import colorama

    if os.name == "nt" and (3, 8) <= sys.version_info < (3, 99):
        from torchaudio._extension.utils import _init_dll_path
        _init_dll_path()

    colorama.init()
    console = Console()
    console.print("System initializing, please wait...")

    live = Live(console=console, refresh_per_second=10, screen=False)
    live.start()

    full_sentences = []
    displayed_text = ""
    rich_text_stored = ""
    recorder = None
    prev_text = ""

    end_of_sentence_detection_pause = 0.45
    unknown_sentence_detection_pause = 0.7
    mid_sentence_detection_pause = 2.0

    def preprocess_text(text):
        text = text.lstrip()
        if text.startswith("..."):
            text = text[3:].lstrip()
        if text:
            text = text[0].upper() + text[1:]
        return text

    def text_detected(text):
        global prev_text, displayed_text, rich_text_stored

        text = preprocess_text(text)

        sentence_end_marks = ['.', '!', '?', '。']
        if text.endswith("..."):
            recorder.post_speech_silence_duration = mid_sentence_detection_pause
        elif text and text[-1] in sentence_end_marks and prev_text and prev_text[-1] in sentence_end_marks:
            recorder.post_speech_silence_duration = end_of_sentence_detection_pause
        else:
            recorder.post_speech_silence_duration = unknown_sentence_detection_pause

        prev_text = text

        rich_text = Text()
        for i, sentence in enumerate(full_sentences):
            style = "yellow" if i % 2 == 0 else "cyan"
            rich_text += Text(sentence, style=style) + Text(" ")

        if text:
            rich_text += Text(text, style="bold yellow")

        new_displayed_text = rich_text.plain
        if new_displayed_text != displayed_text:
            displayed_text = new_displayed_text
            panel = Panel(rich_text, title="[bold green]Live Transcription[/bold green]", border_style="bold green")
            live.update(panel)
            rich_text_stored = rich_text

    def process_text(text):
        global recorder, full_sentences, prev_text
        recorder.post_speech_silence_duration = unknown_sentence_detection_pause

        text = preprocess_text(text).rstrip()
        if text.endswith("..."):
            text = text[:-2]

        if not text:
            return

        prev_text = ""
        print(f"[✓] Final sentence: {text}")

        if args.translate_to:
            try:
                translated = GoogleTranslator(source='auto', target=args.translate_to).translate(text)
                print(f"[→] Translated to '{args.translate_to}': {translated}")
            except Exception as e:
                translated = "[Translation failed]"
                print(f"[✗] Translation failed: {e}")
        else:
            translated = text

        full_sentences.append(translated)
        text_detected("")

        if WRITE_TO_KEYBOARD_INTERVAL:
            pyautogui.write(f"{translated} ", interval=WRITE_TO_KEYBOARD_INTERVAL)

    args = parser.parse_args()

    #  --translate-from = --lang
    if args.translate_from:
        args.lang = args.translate_from

    #Config 
    recorder_config = {
        'spinner': False,
        'model': 'large-v2',
        'download_root': None,
        'realtime_model_type': 'tiny', 
        'language': 'en',
        'silero_sensitivity': 0.05,
        'webrtc_sensitivity': 3,
        'post_speech_silence_duration': unknown_sentence_detection_pause,
        'min_length_of_recording': 1.1,
        'min_gap_between_recordings': 0,
        'enable_realtime_transcription': True,
        'realtime_processing_pause': 0.02,
        'on_realtime_transcription_update': text_detected,
        'silero_deactivity_detection': True,
        'early_transcription_on_silence': 0,
        'beam_size': 5,
        'beam_size_realtime': 3,
        'no_log_file': True,
        'initial_prompt': (
            "End incomplete sentences with ellipses.\n"
            "Examples:\n"
            "Complete: The sky is blue.\n"
            "Incomplete: When the sky...\n"
            "Complete: She walked home.\n"
            "Incomplete: Because he...\n"
        )
    }

    #CLI overrides
    if args.model:
        recorder_config['model'] = args.model
    if args.rt_model:
        recorder_config['realtime_model_type'] = args.rt_model
    if args.lang:
        recorder_config['language'] = args.lang
    if args.root:
        recorder_config['download_root'] = args.root
    if EXTENDED_LOGGING:
        recorder_config['level'] = logging.DEBUG

    recorder = AudioToTextRecorder(**recorder_config)

    initial_text = Panel(Text("Say something...", style="cyan bold"),
                         title="[bold yellow]Waiting for Input[/bold yellow]", border_style="bold yellow")
    live.update(initial_text)

    try:
        while True:
            recorder.text(process_text)
    except KeyboardInterrupt:
        live.stop()
        console.print("[bold red]Transcription stopped by user. Exiting...[/bold red]")
        exit(0)
