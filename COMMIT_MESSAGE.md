feat: implement unified messaging system with Telegram support

## Summary
Add comprehensive multi-platform messaging architecture that enables Telegram responses while maintaining full Slack compatibility. Introduces abstract messaging layer for easy future platform integration.

## Key Changes

### New Architecture Components
- `messaging/` package with abstract MessageSender interface
- MessageRouter for platform-agnostic message dispatching  
- SlackMessenger wrapper preserving existing functionality
- TelegramMessenger with full feature parity (text, audio, files, images)

### Enhanced Telegram Integration
- Extended `telegram_integration.py` with media processing capabilities
- Added `send_telegram_audio()`, `send_telegram_file()`, `send_telegram_photo()`
- Enhanced `process_telegram_event()` to handle images, audio, documents
- Implemented retry logic and comprehensive error handling

### Core System Updates
- Modified `conversation.py` to use MessageRouter with source-aware routing
- Updated `lambda_function.py` with dynamic tool loading based on platform
- Added platform-specific function availability (Slack tools for Slack, Telegram tools for Telegram)
- Source parameter now passed through entire message processing pipeline

### Bug Fixes
- Fixed Weaviate storage error when saving image_urls (converted list to JSON string)
- Added proper empty list handling in storage operations
- **Fixed missing imports in Slack integration**: Added `upload_image_to_s3` and `image_bucket_name` imports to resolve "name not defined" errors
- **Fixed OpenAI API deprecation warning**: Updated text-to-speech to use modern `with_streaming_response.create()` method
- **Fixed Telegram audio upload error**: Corrected bytes/string mismatch where `text_to_speech()` returns file path, not audio bytes

### Documentation
- Comprehensive unified messaging system documentation
- Step-by-step guide for adding new messaging platforms  
- Architecture diagrams and best practices
- Migration guide and troubleshooting section

## Impact
- ✅ Telegram users now receive AI responses directly in their chats
- ✅ Full feature parity: text, audio, files, images across platforms
- ✅ Zero breaking changes - all existing Slack functionality preserved
- ✅ Extensible architecture ready for Discord, WhatsApp, Teams, etc.
- ✅ Dynamic tool loading optimizes function availability per platform

## Files Modified
- New: `messaging/__init__.py`, `messaging/base.py`, `messaging/router.py`
- New: `messaging/slack_messenger.py`, `messaging/telegram_messenger.py`
- New: `docs/unified-messaging-system.md`
- Enhanced: `telegram_integration.py` (+120 lines)
- Modified: `conversation.py`, `lambda_function.py`, `storage.py`

## Testing Status
- [x] Slack functionality verified (no regression)
- [x] Telegram text messaging working
- [x] Weaviate storage bug fixed
- [x] Slack import errors resolved (upload_image_to_s3 now accessible)
- [x] OpenAI TTS deprecation warning eliminated
- [x] Telegram audio upload bytes error fixed
- [ ] Full audio/file feature testing pending
- [ ] Load testing pending

## Breaking Changes
None - fully backward compatible

Co-authored-by: AI Assistant