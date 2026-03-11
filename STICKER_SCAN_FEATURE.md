# 🛡️ Sticker NSFW Scan Feature

## Overview
The bot now includes **AI-powered sticker scanning** to detect and block NSFW/inappropriate stickers in your Telegram groups.

## Features

### ✅ What the Bot Detects
- **NSFW/Pornographic content** in static stickers (WebP format)
- **Sexually explicit imagery** using NudeNet's NudeClassifier
- **Adult-themed stickers** with confidence scoring

### 🔧 How It Works
1. User sends a sticker
2. Bot downloads the sticker temporarily
3. NudeClassifier analyzes the image
4. If `unsafe_score > 0.7`:
   - Message is deleted automatically
   - Warning message sent to chat
   - User ID logged in moderation message

### 📊 Detection Threshold
- **Safe**: unsafe_score ≤ 0.5
- **Warning**: 0.5 < unsafe_score ≤ 0.7
- **Blocked**: unsafe_score > 0.7 ⚠️

## Setup & Configuration

### Enable/Disable Sticker Scan

**Via Settings Menu:**
1. Send `/settings` to the bot
2. Click on **"Sticker NSFW Scan"** toggle
3. ✅ = Enabled, ❌ = Disabled

**Default Setting:** DISABLED (must be manually enabled by group owner)

### Settings Location
```
/settings → Image Scanning Section → Sticker NSFW Scan
```

## Technical Implementation

### Handler Registration
```python
app.add_handler(MessageHandler(filters.Sticker.ALL, scan_sticker))
```

### Key Components
- **NudeClassifier** from NudeNet library
- **Threshold**: 0.7 (70% confidence)
- **Format Support**: WebP (Telegram sticker format)
- **Auto-delete**: Removes violating stickers within seconds

### Code Flow
```
User sends sticker
    ↓
Check if sticker_scan enabled
    ↓
Download sticker to temp file
    ↓
Run NudeClassifier
    ↓
Get unsafe_score
    ↓
Score > 0.7?
    ├─ YES → Delete message + Send warning
    └─ NO → Allow sticker
```

## Usage Examples

### As Group Owner
```bash
# Enable sticker scanning
/settings → Toggle "Sticker NSFW Scan" ON

# Bot will now auto-moderate all stickers
```

### Test Sticker Scanner
```bash
# Test a sticker file locally
python test_sticker_scan.py path/to/sticker.webp

# Example output:
# 📊 Classification Results for: sticker.webp
# ============================================================
# Safe Score:   12.34%
# Unsafe Score: 87.66%
# ------------------------------------------------------------
# ❌ NSFW DETECTED (Score > 0.7)
```

## Moderation Messages

When NSFW sticker detected:
```
⚠️ Moderation: User ID `123456789` - NSFW sticker detected! (score: 0.87)
```

Message auto-deletes after 10 seconds.

## Performance Considerations

### Processing Time
- **Average scan time**: 0.5-2 seconds per sticker
- **Depends on**: Image size, server CPU/GPU

### Resource Usage
- **RAM**: ~200-500MB during scan
- **CPU**: Moderate usage
- **Storage**: Temporary files auto-cleaned

### Optimization Tips
1. Enable only in active groups
2. Monitor log channel for false positives
3. Adjust threshold if needed (advanced users)

## Limitations

### Currently Supported
- ✅ Static stickers (WebP)
- ✅ Regular photo stickers
- ✅ Custom emoji stickers

### Not Yet Supported
- ❌ Animated stickers (TGS/Lottie) - *Future update*
- ❌ Video stickers - *Future update*
- ❌ GIF frame-by-frame analysis - *Future update*

## Advanced: Custom Threshold

To modify the NSFW threshold (default: 0.7):

Edit `bot.py`, line ~985:
```python
if unsafe_score > 0.7:  # Change 0.7 to your preferred threshold
```

**Recommended thresholds:**
- **Strict**: 0.6 (blocks more content)
- **Balanced**: 0.7 (default)
- **Lenient**: 0.8 (allows more content)

## Troubleshooting

### Sticker not being scanned
1. Check if `sticker_scan` is enabled: `/settings`
2. Verify bot has admin permissions
3. Check bot logs for errors

### False positives
1. Review log channel for details
2. Temporarily disable sticker_scan
3. Report to bot developer for model improvement

### Bot slow to respond
- Sticker scanning adds processing delay
- Consider enabling only during high-activity periods
- Use dedicated server with GPU for faster inference

## Dependencies

Required packages (already in `requirements.txt`):
```
nudenet>=3.0
Pillow>=9.0
```

## Privacy & Security

- ✅ Stickers processed locally (no external API calls)
- ✅ Temporary files deleted immediately after scan
- ✅ No images stored permanently
- ✅ No user data logged beyond moderation events

## Future Enhancements

Planned features:
- [ ] Animated sticker (TGS) support
- [ ] Video sticker frame extraction
- [ ] Custom blacklist/whitelist
- [ ] Per-user exemption settings
- [ ] Age-restricted sticker detection (CSAM prevention)
- [ ] Multi-model ensemble for better accuracy

## Support

For issues or questions:
- GitHub Issues: [Your Repo]
- Telegram: @Jayden_212
- Updates Channel: @Tele_212_bots

---

**Last Updated**: March 2026  
**Version**: 1.0.0
