# AssemblyAI ASR Handler

This handler provides automatic speech recognition (ASR) capabilities using AssemblyAI's cloud-based API.

## Features

- High-accuracy speech recognition using AssemblyAI's "best" model
- Fast processing option with "nano" model
- Multi-language support including Polish
- Real-time audio processing
- Automatic audio format conversion
- Error handling and recovery

## Configuration

The handler can be configured with the following parameters:

- `api_key`: Your AssemblyAI API key (required)
- `speech_model`: Model to use ("best" for highest accuracy, "nano" for fastest processing)
- `language`: Language code (e.g., "pl" for Polish, "en" for English)

## Requirements

- Python 3.8+
- assemblyai>=0.17.0
- Valid AssemblyAI API key

## Installation

The AssemblyAI package will be automatically installed when using this handler.

```bash
pip install assemblyai
```

## Usage

Add the AssemblyAI handler to your configuration:

```yaml
AssemblyAI:
  enabled: True
  module: asr/assemblyai/asr_handler_assemblyai
  api_key: "your_api_key_here"
  speech_model: "best"
  language: "pl"
```

## Performance Notes

- The "best" model provides highest accuracy but takes longer to process
- The "nano" model is faster but may have lower accuracy
- Processing time depends on audio length and internet connection
- Audio is automatically converted to 16kHz mono WAV format for optimal compatibility
