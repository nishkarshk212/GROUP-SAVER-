# ⚡ Quick Reference - Animated Sticker Scanning

## 🎯 What's Supported

| Format | Detection | Speed | Accuracy |
|--------|-----------|-------|----------|
| **Static WebP** | Classifier | 0.5s | ⭐⭐⭐⭐⭐ |
| **Animated WebP** | Frame-by-frame | 2-8s | ⭐⭐⭐⭐⭐ |
| **TGS (Lottie)** | Convert→Frames | 5-8s | ⭐⭐⭐⭐ |
| **Video WebM** | OpenCV sampling | 2-4s | ⭐⭐⭐⭐ |

---

## 🔧 Quick Commands

### Install Dependencies
```bash
pip install opencv-python lottie
# Or
pip install -r requirements.txt
```

### Test Locally
```bash
python test_sticker_scan.py sticker.webp
```

### Enable on Bot
```
/settings → Click "Sticker NSFW Scan" → Toggle ON ✅
```

---

## ⚙️ Configuration

### Change Sensitivity

Edit `bot.py`:

**Stricter (block more):**
```python
threshold=0.6  # Line ~1230
sample_rate=2  # Line ~1070 - scan more frames
```

**Lenient (allow more):**
```python
threshold=0.8  # Line ~1230
sample_rate=8  # Line ~1070 - scan fewer frames
```

**Faster processing:**
```python
sample_rate=8   # Skip more frames
video_sample=60 # Sample every 2 seconds
```

**Better accuracy:**
```python
sample_rate=2    # Scan more frames
video_sample=15  # Sample every 0.5 seconds
```

---

## 📊 Expected Behavior

### Normal Operation

**Static sticker sent:**
```
User sends sticker → Bot scans (0.5s) → Allowed/Deleted
Warning: "NSFW Static classifier (score: 0.87)"
```

**Animated sticker sent:**
```
User sends animation → Bot extracts frames (2-8s) → Scan each frame
Warning: "NSFW Animated frame analysis (12 frames) (score: 0.92)"
```

**TGS sticker sent:**
```
User sends TGS → Convert to GIF (1-2s) → Extract frames → Scan
Warning: "NSFW TGS frame analysis (score: 0.85)"
```

**Video sticker sent:**
```
User sends video → Extract 1fps → Scan sampled frames
Warning: "NSFW Video frame analysis (5 frames) (score: 0.78)"
```

---

## 🐛 Troubleshooting

### "Lottie library not available"
```bash
pip install lottie
# Or ignore - bot will gracefully skip TGS scanning
```

### "OpenCV not available"
```bash
pip install opencv-python
# Or ignore - video stickers won't be scanned
```

### Bot crashes on animated stickers
```bash
# Increase sample rate (fewer frames)
sample_rate=8  # Instead of 4
```

### Too many false positives
```python
# Raise threshold
threshold=0.8  # Instead of 0.7
```

### Processing too slow
```python
# Increase sample rates
sample_rate=8     # Every 8th frame
video_sample=60   # Every 2 seconds
```

---

## 📈 Performance Tips

### Optimize for Speed
```python
sample_rate=8      # Fewer frames
threshold=0.75     # Slightly higher
video_sample=60    # Less frequent sampling
```

**Result:** 2-3x faster, slight accuracy loss

### Optimize for Accuracy
```python
sample_rate=2      # More frames
threshold=0.65     # Lower threshold
video_sample=15    # More frequent sampling
```

**Result:** Better detection, 2-3x slower

### Balanced (Default)
```python
sample_rate=4      # Every 4th frame
threshold=0.7      # Standard
video_sample=30    # Every second
```

**Result:** Good balance ✅

---

## 🔍 Monitoring

### Check What's Being Detected

Enable logging in `bot.py`:
```python
print(f"Processing {sticker.format} format...")
print(f"Extracted {len(frames)} frames")
print(f"NSFW detected with score {max_score:.2f}")
```

### View Bot Logs

**On server:**
```bash
journalctl -u nsfw-bot -f
```

**Look for:**
```
Processing animated sticker (24 frames)...
Extracted 6 frames from animated sticker
NSFW detected in frame_0.png with score 0.92
```

---

## 🎯 Common Scenarios

### Scenario 1: Anime Sticker Pack

**Problem:** Users sending borderline suggestive anime stickers

**Solution:**
```python
threshold=0.65  # Stricter
sample_rate=2   # More frames
```

### Scenario 2: Meme Stickers

**Problem:** Memes with occasional adult content

**Solution:**
```python
threshold=0.7   # Default works well
```

### Scenario 3: Gaming Stickers

**Problem:** Some gaming stickers have violence/weapons

**Solution:**
```python
# Already handled by YOLOv5 weapon detection
# Keep default settings
```

### Scenario 4: Holiday Sticker Packs

**Problem:** Large variety, need fast processing

**Solution:**
```python
sample_rate=8   # Faster processing
threshold=0.75  # Slightly stricter
```

---

## 📦 File Locations

### Temporary Files
```python
/tmp/frame_0.png          # Extracted frames
/tmp/sticker.gif          # Converted TGS
/tmp/video_frame_30.jpg   # Video frames
```

**Auto-deleted after scan!**

### Code Locations

**Frame extraction:** `bot.py` line ~970  
**TGS conversion:** `bot.py` line ~1010  
**Video extraction:** `bot.py` line ~1040  
**Scanning logic:** `bot.py` line ~1070  
**Main handler:** `bot.py` line ~1111  

---

## 🆘 Emergency Actions

### Disable Sticker Scanning Immediately

**Via bot:**
```
/settings → Sticker NSFW Scan → Toggle OFF ❌
```

**Via code (server):**
```bash
cd /opt/nsfw-bot
# Comment out the handler in bot.py
# systemctl restart nsfw-bot
```

### Rollback to Previous Version

```bash
ssh root@140.245.240.202 -p 22
cd /opt/nsfw-bot
git log --oneline -5
git reset --hard <previous-commit>
systemctl restart nsfw-bot
```

### Check Current Status

```bash
# Local
python -m py_compile bot.py

# Server
ssh root@140.245.240.202 -p 22 'systemctl status nsfw-bot'
```

---

## 📞 Quick Help

**Test command:**
```bash
python test_sticker_scan.py path/to/sticker.webp
```

**Deploy command:**
```bash
./deploy_auto.sh
```

**Status check:**
```bash
ssh root@140.245.240.202 -p 22 'journalctl -u nsfw-bot -f'
```

---

## ✅ Success Indicators

Your setup is working when:

✅ Static stickers scanned in <1s  
✅ Animated stickers processed without errors  
✅ No memory leaks (RAM stable)  
✅ Temp files cleaned up  
✅ Accurate NSFW detection  
✅ No false positives on safe stickers  

---

**Quick Reference v2.0** | **March 2026** | **Animated Sticker Support**
