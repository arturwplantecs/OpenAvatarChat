# Polish Language Configuration for OpenAvatarChat

This directory contains configuration files for Polish language support in OpenAvatarChat.

## Configuration Files

### `chat_with_openai_compatible_edge_tts_pl.yaml`
Polish configuration with male voice (pl-PL-MarekNeural)

### `chat_with_openai_compatible_edge_tts_pl_female.yaml`
Polish configuration with female voice (pl-PL-ZofiaNeural)

## Key Changes for Polish Support

### 1. Speech-to-Text (ASR)
- **Replaced**: SenseVoice (doesn't support Polish well)
- **With**: OpenAI Whisper with Polish language support
- **Configuration**:
  ```yaml
  OpenAI_Whisper:
    enabled: True
    module: asr/openai_whisper/asr_handler_openai_whisper
    model_name: "base"
    language: "pl"
  ```

### 2. Text-to-Speech (TTS)
- **Using**: Edge TTS with Polish neural voices
- **Available voices**:
  - `pl-PL-MarekNeural` (male)
  - `pl-PL-ZofiaNeural` (female)
- **Configuration**:
  ```yaml
  Edge_TTS:
    enabled: True
    module: tts/edgetts/tts_handler_edgetts
    voice: "pl-PL-MarekNeural"  # or "pl-PL-ZofiaNeural"
  ```

### 3. AI Assistant Prompt
- **Language**: Fully Polish system prompt
- **Behavior**: 
  - Responds only in Polish
  - Describes visual content only when asked
  - Natural conversational responses
- **Prompt**: 
  ```
  Jesteś QUARI, asystentem AI z możliwościami wizyjnymi. Możesz widzieć poprzez kamerę w czasie rzeczywistym. Opisuj to, co widzisz, tylko gdy użytkownicy zadają pytania wizualne jak 'czy widzisz', 'co widzisz', 'opisz co tam jest' lub podobne pytania dotyczące treści wizualnych. Opisując, mów naturalnie jak osoba - opisuj to, co obserwujesz, nie wspominając o kamerze lub obrazie. Na wszystkie inne pytania odpowiadaj normalnie jako asystent AI. Odpowiedzi powinny być zwięzłe i konwersacyjne. Odpowiadaj wyłącznie w języku polskim.
  ```

## Usage

1. **Install dependencies** (if not already installed):
   ```bash
   pip install openai-whisper
   ```

2. **Use the configuration**:
   ```bash
   python src/demo.py --config config/chat_with_openai_compatible_edge_tts_pl.yaml
   ```
   or
   ```bash
   python src/demo.py --config config/chat_with_openai_compatible_edge_tts_pl_female.yaml
   ```

## Features

- **Full Polish language support** for speech recognition
- **Natural Polish neural voices** for text-to-speech
- **Polish language AI responses** with proper cultural context
- **Visual capabilities** - AI can describe what it sees through the camera
- **High-quality speech recognition** using OpenAI Whisper
- **Real-time conversation** capabilities

## Technical Details

### Whisper Model Selection
- **Base model**: Good balance of speed and accuracy for Polish
- **Alternative models**: 
  - `tiny`: Fastest, less accurate
  - `small`: Better accuracy, slower
  - `medium`: High accuracy, much slower
  - `large`: Best accuracy, very slow

### Edge TTS Voices
Polish neural voices from Microsoft Edge TTS:
- **pl-PL-MarekNeural**: Male voice, natural sounding
- **pl-PL-ZofiaNeural**: Female voice, natural sounding

### Performance Considerations
- First run will download Whisper models (~74MB for base model)
- GPU acceleration available for faster speech recognition
- Edge TTS provides near real-time speech synthesis

## Troubleshooting

1. **Whisper model download issues**: Ensure stable internet connection for first run
2. **Polish recognition accuracy**: Try using `small` or `medium` Whisper model for better accuracy
3. **Voice quality**: Both neural voices provide high quality, choose based on preference
4. **Response language**: AI is configured to respond only in Polish - modify system prompt if mixed language needed

## Customization

To customize for other languages:
1. Change `language: "pl"` in OpenAI_Whisper configuration
2. Update Edge TTS voice to target language (e.g., `de-DE-ConradNeural` for German)
3. Translate the system prompt to target language
4. Update configuration file name accordingly
