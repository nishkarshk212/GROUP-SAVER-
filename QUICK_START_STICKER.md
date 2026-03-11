# 🚀 Quick Start: Sticker NSFW Scan

## Enable in 30 Seconds

### Step 1: Open Settings
```
Send to bot: /settings
```

### Step 2: Toggle Sticker Scan
Click the button:
```
[❌ Sticker NSFW Scan] → Click once → [✅ Sticker NSFW Scan]
```

### Step 3: Done! ✅
The bot now automatically scans all stickers for NSFW content.

---

## What Happens Next?

**When user sends inappropriate sticker:**

1. ⏱️ **Bot scans** (0.5-2 seconds)
2. 🗑️ **Auto-deletes** message
3. ⚠️ **Sends warning**: "NSFW sticker detected! (score: 0.87)"
4. 🧹 **Warning auto-deletes** after 10 seconds

---

## Test It

### Send a test sticker to your group:
```
Normal sticker → ✅ Allowed
NSFW sticker → ❌ Deleted + Warning
```

### Check detection locally:
```bash
source .venv/bin/activate
python test_sticker_scan.py path/to/sticker.webp
```

---

## Default Settings

| Feature | Default | Recommended |
|---------|---------|-------------|
| Sticker Scan | ❌ OFF | ✅ ON (in active groups) |
| Detection Threshold | 0.70 (70%) | 0.70 (balanced) |
| Auto-delete | ✅ YES | ✅ YES |
| Warning duration | 10 sec | 10 sec |

---

## Adjust Sensitivity (Optional)

### Make Stricter (block more):
Edit `bot.py` line ~985:
```python
if unsafe_score > 0.6:  # Changed from 0.7 to 0.6
```

### Make Lenient (allow more):
```python
if unsafe_score > 0.8:  # Changed from 0.7 to 0.8
```

---

## Troubleshooting

### Bot not scanning stickers?
- ✅ Check `/settings` → Is "Sticker NSFW Scan" enabled?
- ✅ Verify bot has admin permissions
- ✅ Ensure bot can delete messages

### Too many false positives?
- Temporarily disable feature
- Increase threshold to 0.8
- Review specific stickers with test script

### Bot slow?
- Normal delay: 0.5-2 seconds per sticker
- Consider GPU server for faster processing
- Enable only during peak hours

---

## Supported Content

✅ **Detects:**
- Static WebP stickers
- Photo-based stickers
- Custom emoji stickers
- Sexually explicit imagery
- Adult-themed content

❌ **Not yet supported:**
- Animated TGS stickers (future)
- Video stickers (future)
- GIF frame analysis (future)

---

## Privacy Notes

🔒 **Secure by design:**
- ✅ Processed locally (no cloud API)
- ✅ No permanent storage
- ✅ Temporary files auto-deleted
- ✅ Only moderation events logged

---

## Performance

**Resource usage per scan:**
- RAM: +200-500MB (temporary)
- CPU: Moderate spike
- Time: 0.5-2 seconds
- Storage: None (auto-cleaned)

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `/settings` | Open settings menu |
| `/start` | Welcome message |
| Click "Sticker NSFW Scan" | Toggle on/off |

---

## Example Moderation

**User sends NSFW sticker:**

```
[User sends inappropriate sticker]
        ↓
⚠️ Moderation: User ID `123456789` - NSFW sticker detected! (score: 0.87)
        ↓
[Message deleted after 2 seconds]
        ↓
[Warning deleted after 10 seconds]
```

---

## Need Help?

**Contact:**
- Developer: @Jayden_212
- Updates: @Tele_212_bots

**Documentation:**
- Full guide: `STICKER_SCAN_FEATURE.md`
- Implementation: `STICKER_SCAN_SUMMARY.md`

---

## ✅ Success Checklist

- [ ] Virtual environment activated
- [ ] Bot code updated
- [ ] Dependencies installed
- [ ] `/settings` accessed
- [ ] Sticker scan enabled
- [ ] Test sticker sent
- [ ] Moderation working

---

**Ready to go!** Your group is now protected from inappropriate stickers. 🛡️

**Version**: 1.0.0 | **Updated**: March 2026
