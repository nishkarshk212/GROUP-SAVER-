"""
Sticker Pack Analyzer
Analyzes stickers from a Telegram sticker pack URL
Tests: https://t.me/addstickers/Shiva1234422_by_fStikBot
"""

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import asyncio


async def analyze_sticker_pack(pack_url: str):
    """
    Analyze a Telegram sticker pack
    
    Args:
        pack_url: URL like https://t.me/addstickers/Shiva1234422_by_fStikBot
    """
    # Extract pack name from URL
    pack_name = pack_url.split('/')[-1]
    
    print(f"🔍 Analyzing sticker pack: {pack_name}")
    print("=" * 60)
    
    app = Client(
        "sticker_analyzer",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    await app.start()
    
    try:
        # Get sticker set info
        sticker_set = await app.get_sticker_set(pack_name)
        
        print(f"\n📦 **Sticker Pack Info:**")
        print(f"   Name: {sticker_set.name}")
        print(f"   Title: {sticker_set.title}")
        print(f"   Total Stickers: {len(sticker_set.stickers)}")
        print(f"   Is Animated: {sticker_set.is_animated}")
        print(f"   Is Video: {sticker_set.is_video}")
        print()
        
        # Analyze each sticker
        print("📊 **Analyzing Individual Stickers:**")
        print("-" * 60)
        
        for i, sticker in enumerate(sticker_set.stickers[:10], 1):  # Analyze first 10
            print(f"\n{i}. Sticker #{i}")
            print(f"   File ID: `{sticker.file_id}`")
            print(f"   Width: {sticker.width}")
            print(f"   Height: {sticker.height}")
            print(f"   File Size: {sticker.file_size} bytes")
            
            if sticker.emoji:
                print(f"   Emoji: {sticker.emoji}")
            
            if sticker.set_name:
                print(f"   Set: {sticker.set_name}")
            
            # Check format
            if sticker.file_size > 1024 * 1024:  # > 1MB
                print(f"   ⚠️  Large file ({sticker.file_size / 1024:.1f} KB)")
            else:
                print(f"   ✅ Normal size ({sticker.file_size / 1024:.1f} KB)")
        
        if len(sticker_set.stickers) > 10:
            print(f"\n... and {len(sticker_set.stickers) - 10} more stickers")
        
        print("\n" + "=" * 60)
        print("✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error analyzing pack: {e}")
    
    finally:
        await app.stop()


async def test_specific_sticker(file_id: str):
    """
    Test a specific sticker by file ID
    
    Args:
        file_id: Telegram file ID of sticker
    """
    print(f"🔍 Testing sticker: {file_id}")
    print("=" * 60)
    
    app = Client(
        "sticker_tester",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    await app.start()
    
    try:
        # Get file info
        file = await app.get_file(file_id)
        
        print(f"\n📊 **Sticker Details:**")
        print(f"   File ID: `{file_id}`")
        print(f"   File Size: {file.file_size} bytes")
        print(f"   Can Download: {bool(file.file_id)}")
        
        # Download and analyze
        print("\n⬇️  Downloading sticker...")
        downloaded = await file.download()
        print(f"✅ Downloaded to: {downloaded}")
        
        # Run NSFW detection
        print("\n🔍 Running NSFW detection...")
        from optimized_detector import detector
        
        is_nsfw, score, detections = detector.detect_sticker(downloaded)
        
        print(f"\n🎯 **Detection Result:**")
        print(f"   NSFW: {'✅ YES' if is_nsfw else '❌ NO'}")
        print(f"   Confidence: {score:.2%}")
        print(f"   Detections: {len(detections)} objects found")
        
        if detections:
            print(f"\n📋 **Detected Objects:**")
            for det in detections[:5]:  # Show first 5
                print(f"   • {det.get('class', 'unknown')}: {det.get('score', 0):.2%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await app.stop()


if __name__ == "__main__":
    # Test the Shiva sticker pack
    PACK_URL = "https://t.me/addstickers/Shiva1234422_by_fStikBot"
    
    print("🚀 Sticker Pack Analyzer")
    print("=" * 60)
    print(f"Target: {PACK_URL}")
    print()
    
    # Run analysis
    asyncio.run(analyze_sticker_pack(PACK_URL))
