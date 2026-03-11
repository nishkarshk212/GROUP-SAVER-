#!/usr/bin/env python3
"""Test sticker NSFW detection using NudeClassifier"""

from nudenet import NudeClassifier
import sys

def test_sticker_classifier(image_path):
    """Test NSFW classification on an image"""
    try:
        classifier = NudeClassifier()
        result = classifier.classify(image_path)
        
        print(f"\n📊 Classification Results for: {image_path}")
        print("=" * 60)
        
        for img_path, scores in result.items():
            safe_score = scores.get('safe', 0.0)
            unsafe_score = scores.get('unsafe', 0.0)
            
            print(f"Safe Score:   {safe_score:.2%}")
            print(f"Unsafe Score: {unsafe_score:.2%}")
            print("-" * 60)
            
            if unsafe_score > 0.7:
                print("❌ NSFW DETECTED (Score > 0.7)")
            elif unsafe_score > 0.5:
                print("⚠️  Potentially Unsafe (Score > 0.5)")
            else:
                print("✅ Safe Content")
                
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_sticker_scan.py <image_path>")
        print("Example: python test_sticker_scan.py sticker.webp")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_sticker_classifier(image_path)
