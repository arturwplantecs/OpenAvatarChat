# OpenAI Whisper ASR Handler

This handler provides Automatic Speech Recognition (ASR) using OpenAI's Whisper model with support for Polish language.

## Features

- Uses OpenAI Whisper for high-quality speech recognition
- Supports Polish language (and other languages by changing configuration)
- Works with GPU acceleration when available
- Configurable model size (tiny, base, small, medium, large)

## Configuration

```yaml
OpenAI_Whisper:
  enabled: True
  module: asr/openai_whisper/asr_handler_openai_whisper
  model_name: "base"  # Options: tiny, base, small, medium, large
  language: "pl"      # Polish language code
```

## Dependencies

- openai-whisper
- torch
- torchaudio
- transformers

## Installation

The dependencies will be installed automatically when setting up the project. Whisper models will be downloaded on first use.

## Supported Languages

Whisper supports many languages including:
- Polish (pl)
- English (en)
- German (de)
- French (fr)
- Spanish (es)
- Italian (it)
- And many more...

## Model Sizes

- `tiny`: Fastest, least accurate (~39 MB)
- `base`: Good balance of speed and accuracy (~74 MB)
- `small`: Better accuracy (~244 MB)
- `medium`: High accuracy (~769 MB)
- `large`: Best accuracy (~1550 MB)

For Polish language recognition, `base` or `small` models provide good results.
