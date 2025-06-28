# Changelog

## [1.1.1] - 2025-06-28 - by <https://github.com/adryserage>

### Fixed

- Fixed async streaming issues with different LLM providers:
  - Corrected async generator handling in OpenAI streaming
  - Fixed provider-specific stream response formats
  - Improved error handling for different chunk formats
- Updated main chat loop to properly handle provider-specific responses

## [1.1.0] - 2025-06-28 - by <https://github.com/adryserage>

### Added

- Multi-provider LLM support:
  - OpenAI (GPT-3.5, GPT-4)
  - Anthropic (Claude-2, Claude-3)
  - Google (Gemini Pro)
- Unified streaming interface for all providers
- Environment variables support for model configuration
- Automatic provider detection based on model name

### Changed

- Refactored `llm_api.py` with improved architecture:
  - Added object-oriented design with `LLMClient` class
  - Centralized configuration management
  - Unified response format for all providers
  - Better message format handling for each provider
- Updated environment variables structure:
  - Provider-specific API keys
  - Common model settings
  - Optional organization settings

### Dependencies Added

- `anthropic` package for Claude models
- `google-generativeai` package for Gemini models

### Documentation

- Added detailed environment variables documentation
- Created `.env.example` with configuration examples
- Updated README.md with provider-specific setup instructions

## Migration Guide

1. Update your `.env` file with the new environment variables
2. Install new dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. No changes needed in existing code using `openai_chatbot_chain`

## Configuration Examples

### OpenAI Setup

```env
LLM_MODEL=gpt-4
OPENAI_API_KEY=your_key
OPENAI_ORGANIZATION=optional_org_id
```

### Anthropic Setup

```env
LLM_MODEL=claude-3-opus
ANTHROPIC_API_KEY=your_key
```

### Gemini Setup

```env
LLM_MODEL=gemini-pro
GOOGLE_API_KEY=your_key
```

### Common Settings

```env
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```
