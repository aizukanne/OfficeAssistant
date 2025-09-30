#!/usr/bin/env python3
"""
Test script to verify Slack image block functionality
"""
import json
from slack_integration import convert_to_slack_blocks

def test_markdown_image():
    """Test markdown image syntax"""
    message = """Here's a test image:
![Test Image](https://example.com/test.jpg)
Some text after the image."""
    
    result = convert_to_slack_blocks(message)
    blocks = json.loads(result)
    
    print("=== Markdown Image Test ===")
    print(f"Input: {repr(message)}")
    print(f"Blocks generated: {len(blocks)}")
    
    # Find image block
    image_blocks = [b for b in blocks if b.get('type') == 'image']
    print(f"Image blocks found: {len(image_blocks)}")
    
    if image_blocks:
        img_block = image_blocks[0]
        print(f"Image URL: {img_block.get('image_url')}")
        print(f"Alt text: {img_block.get('alt_text')}")
    
    print(f"Full result: {json.dumps(blocks, indent=2)}")
    print()

def test_standalone_url():
    """Test standalone image URL"""
    message = """Landscape image (16:9):
https://mariaimagefolder-us.s3.amazonaws.com/Generated_Image_20250929064405.png

Quick check:
- Some bullet point"""
    
    result = convert_to_slack_blocks(message)
    blocks = json.loads(result)
    
    print("=== Standalone URL Test ===")
    print(f"Input: {repr(message)}")
    print(f"Blocks generated: {len(blocks)}")
    
    # Find image block
    image_blocks = [b for b in blocks if b.get('type') == 'image']
    print(f"Image blocks found: {len(image_blocks)}")
    
    if image_blocks:
        img_block = image_blocks[0]
        print(f"Image URL: {img_block.get('image_url')}")
        print(f"Alt text: {img_block.get('alt_text')}")
    
    print(f"Full result: {json.dumps(blocks, indent=2)}")
    print()

def test_mixed_content():
    """Test mixed markdown and standalone URLs"""
    message = """# Header
Some text content.

![Markdown Image](https://example.com/markdown.jpg)

More text here.

Standalone image:
https://example.com/standalone.png

Final text section."""
    
    result = convert_to_slack_blocks(message)
    blocks = json.loads(result)
    
    print("=== Mixed Content Test ===")
    print(f"Input: {repr(message)}")
    print(f"Blocks generated: {len(blocks)}")
    
    # Count different block types
    section_blocks = [b for b in blocks if b.get('type') == 'section']
    image_blocks = [b for b in blocks if b.get('type') == 'image']
    
    print(f"Section blocks: {len(section_blocks)}")
    print(f"Image blocks: {len(image_blocks)}")
    
    if image_blocks:
        for i, img_block in enumerate(image_blocks):
            print(f"Image {i+1} URL: {img_block.get('image_url')}")
            print(f"Image {i+1} Alt text: {img_block.get('alt_text')}")
    
    print(f"Full result: {json.dumps(blocks, indent=2)}")
    print()

if __name__ == "__main__":
    print("Testing Slack Image Block Functionality")
    print("=" * 50)
    
    test_markdown_image()
    test_standalone_url()
    test_mixed_content()
    
    print("Tests completed!")