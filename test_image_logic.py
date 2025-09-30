#!/usr/bin/env python3
"""
Simple test of the image detection logic
"""
import re
import json

def test_image_detection_logic():
    """Test the core image detection patterns"""
    
    # Test markdown image pattern
    markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    test_cases = [
        "![Test Image](https://example.com/test.jpg)",
        "![](https://example.com/no-alt.png)", 
        "![Alt text with spaces](https://domain.com/image.gif)",
        "Not an image: https://example.com/test.jpg",
        "![Broken markdown](no-url-here)"
    ]
    
    print("=== Markdown Image Pattern Test ===")
    for case in test_cases:
        match = re.match(markdown_pattern, case.strip())
        if match:
            alt_text = match.group(1) or "Image"
            image_url = match.group(2)
            print(f"✓ MATCH: '{case}' -> Alt: '{alt_text}', URL: '{image_url}'")
        else:
            print(f"✗ NO MATCH: '{case}'")
    print()
    
    # Test standalone URL pattern
    standalone_pattern = r'^https?://[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?[^\s]*)?$'
    
    url_test_cases = [
        "https://mariaimagefolder-us.s3.amazonaws.com/Generated_Image_20250929064405.png",
        "http://example.com/image.jpg",
        "https://domain.com/path/to/image.gif?v=123",
        "https://example.com/not-an-image.txt",
        "ftp://example.com/image.jpg",  # Should not match
        "https://example.com/image.jpg with spaces"  # Should not match
    ]
    
    print("=== Standalone URL Pattern Test ===")
    for case in url_test_cases:
        match = re.match(standalone_pattern, case.strip(), re.IGNORECASE)
        if match:
            print(f"✓ MATCH: '{case}'")
        else:
            print(f"✗ NO MATCH: '{case}'")
    print()

def test_message_parsing_logic():
    """Test the message parsing logic similar to what we implemented"""
    
    # Simulate the message from the screenshot
    message = """Landscape image (16:9):
https://mariaimagefolder-us.s3.amazonaws.com/Generated_Image_20250929064405.png

Quick check:
- Cake on right third, pastel balloons to the right"""
    
    lines = message.split('\n')
    
    # Test our detection patterns
    markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    standalone_pattern = r'^https?://[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?[^\s]*)?$'
    
    print("=== Message Parsing Test ===")
    print(f"Input message: {repr(message)}")
    print(f"Split into {len(lines)} lines")
    
    detected_images = []
    
    for i, line in enumerate(lines):
        print(f"Line {i}: {repr(line)}")
        
        # Check for markdown images
        if re.match(markdown_pattern, line.strip()):
            match = re.match(markdown_pattern, line.strip())
            alt_text = match.group(1) or "Image"
            image_url = match.group(2)
            detected_images.append(("markdown", alt_text, image_url))
            print(f"  -> Found markdown image: {image_url}")
            
        # Check for standalone URLs
        elif re.match(standalone_pattern, line.strip(), re.IGNORECASE):
            # Check if previous line could be alt text
            alt_text = "Image"
            if i > 0 and lines[i-1].strip() and not lines[i-1].strip().startswith('http'):
                potential_alt = lines[i-1].strip()
                if len(potential_alt) < 100:
                    alt_text = potential_alt
            
            detected_images.append(("standalone", alt_text, line.strip()))
            print(f"  -> Found standalone image: {line.strip()}")
            print(f"  -> Using alt text: {alt_text}")
    
    print(f"\nTotal images detected: {len(detected_images)}")
    for img_type, alt, url in detected_images:
        print(f"  {img_type.upper()}: '{alt}' -> {url}")
    
    print()

def test_unfurling_detection():
    """Test the unfurling detection logic"""
    
    messages = [
        "Just text with no images",
        "![Markdown image](https://example.com/test.jpg)",
        "Standalone image:\nhttps://example.com/image.png",
        "Mixed content:\n![Markdown](https://example.com/md.jpg)\nAnd standalone:\nhttps://example.com/standalone.png"
    ]
    
    markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    standalone_pattern = r'^https?://[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?[^\s]*)?$'
    
    print("=== Unfurling Detection Test ===")
    
    for message in messages:
        has_markdown = bool(re.search(markdown_pattern, message))
        has_standalone = any(re.match(standalone_pattern, line.strip(), re.IGNORECASE) 
                           for line in message.split('\n'))
        
        has_images = has_markdown or has_standalone
        
        print(f"Message: {repr(message)}")
        print(f"  Markdown images: {has_markdown}")
        print(f"  Standalone images: {has_standalone}")
        print(f"  Should disable unfurling: {has_images}")
        print()

if __name__ == "__main__":
    print("Testing Image Detection Logic")
    print("=" * 40)
    
    test_image_detection_logic()
    test_message_parsing_logic()
    test_unfurling_detection()
    
    print("Tests completed!")