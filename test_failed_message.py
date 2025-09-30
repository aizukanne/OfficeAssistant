#!/usr/bin/env python3
"""
Test the exact message that failed to deliver
"""
import re
import json

# Simulate the convert_to_slack_blocks function without dependencies
def simulate_convert_to_slack_blocks(markdown_text):
    """Simulate the key logic of convert_to_slack_blocks"""
    lines = markdown_text.split('\n')
    blocks = []
    current_section = []
    in_code_block = False
    
    for line_num, line in enumerate(lines):
        print(f"Processing line {line_num}: {repr(line)}")
        
        if in_code_block:
            if line.startswith("```"):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "```\n" + "\n".join(current_section) + "\n```",
                    }
                })
                current_section = []
                in_code_block = False
            else:
                current_section.append(line)
            continue
        
        # Handle horizontal rules
        if line.strip() in ('***', '---', '___'):
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            blocks.append({"type": "divider"})
            continue
        
        # Handle the start of a code block
        if line.startswith("```"):
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            in_code_block = True
            current_section.append(line)
            continue
        
        # Handle markdown images
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        if re.match(image_pattern, line.strip()):
            print(f"  -> Found markdown image on line {line_num}")
            # Flush current section
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            
            # Extract alt text and URL
            match = re.match(image_pattern, line.strip())
            alt_text = match.group(1) or "Image"
            image_url = match.group(2)
            
            print(f"    Alt text: {alt_text}")
            print(f"    Image URL: {image_url}")
            
            # Add image block
            blocks.append({
                "type": "image",
                "image_url": image_url,
                "alt_text": alt_text
            })
            continue
        
        # Handle standalone image URLs
        standalone_url_pattern = r'^https?://[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?[^\s]*)?$'
        if re.match(standalone_url_pattern, line.strip(), re.IGNORECASE):
            print(f"  -> Found standalone image URL on line {line_num}")
            # Flush current section
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            
            # Add image block
            blocks.append({
                "type": "image",
                "image_url": line.strip(),
                "alt_text": "Image"
            })
            continue
        
        # Replace Markdown bold with Slack's bold syntax outside code blocks
        line = line.replace('**', '*')
        
        # Headers and regular text
        if line.lstrip().startswith('#'):
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            
            # Count the number of # symbols and remove them
            heading_level = 0
            line_stripped = line.lstrip()
            for char in line_stripped:
                if char == '#':
                    heading_level += 1
                else:
                    break
            
            # Extract the heading text
            heading_text = line_stripped[heading_level:].strip()
            
            # Use progressively smaller markers as the heading level increases
            size_markers = ['◆', '🔷', '🔹', '▪️', '▫️', '·']
            marker = size_markers[min(heading_level - 1, len(size_markers) - 1)]
            
            # All headings are now section blocks with bold text
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{marker} *{heading_text}*"
                }
            })
        elif line.strip():
            current_section.append(line)
        
        # Empty lines
        elif current_section:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(current_section)
                }
            })
            current_section = []

    # Add the last section if there is any text left
    if current_section:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(current_section)
            }
        })

    return blocks

def test_failed_message():
    """Test the exact message that failed to deliver"""
    
    # The exact message from the user's feedback
    failed_message = '''Below are three separate, high‑resolution images that display the key formulas for each distribution. These images render cleanly in Slack (no LaTeX rendering needed).

---

### 1. Hypergeometric Distribution  

**Formula**  
\\[
P(X = k)=\\frac{\\displaystyle \\binom{K}{k}\\,\\binom{N-K}{\\,n-k\\,}}{\\displaystyle \\binom{N}{n}}
\\]

**Image**  
![Hypergeometric PMF](https://mariaimagefolder-us.s3.amazonaws.com/Generated_Image_20250929070649.png)

---

### 2. Poisson Distribution  

**Formula**  
\\[
P(X = x)=\\frac{\\lambda^{x}\\,e^{-\\lambda}}{x!}, \\qquad x = 0,1,2,\\dots
\\]

**Image**  
![Poisson PMF](https://mariaimagefolder-us.s3.amazonaws.com/Generated_Image_20250929070712.png)

---

### 3. Negative Binomial Distribution  

**Formula**  
\\[
P(X = x)=\\binom{x+r-1}{r-1}\\,p^{\\,r}\\,(1-p)^{\\,x},
\\qquad x = 0,1,2,\\dots
\\]

**Image**  
![Negative Binomial PMF](https://mariaimagefolder-us.s3.amazonaws.com/Generated_Image_20250929070734.png)

---

Feel free to drop any of the images into a Slack channel or message – they'll appear as normal picture attachments, making the equations instantly readable. Let me know if you need any additional formulas or variations!'''
    
    print("=== Testing Failed Message ===")
    print(f"Message length: {len(failed_message)} characters")
    print(f"Message lines: {len(failed_message.split(chr(10)))} lines")
    
    # Test image detection
    markdown_image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    standalone_url_pattern = r'^https?://[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?[^\s]*)?$'
    
    markdown_images = re.findall(markdown_image_pattern, failed_message)
    standalone_images = [line.strip() for line in failed_message.split('\n') 
                        if re.match(standalone_url_pattern, line.strip(), re.IGNORECASE)]
    
    print(f"Markdown images found: {len(markdown_images)}")
    for i, (alt, url) in enumerate(markdown_images):
        print(f"  {i+1}. '{alt}' -> {url}")
    
    print(f"Standalone images found: {len(standalone_images)}")
    for i, url in enumerate(standalone_images):
        print(f"  {i+1}. {url}")
    
    # Test block conversion
    print("\n=== Converting to Blocks ===")
    blocks = simulate_convert_to_slack_blocks(failed_message)
    
    print(f"Total blocks generated: {len(blocks)}")
    
    # Analyze block types
    section_count = sum(1 for b in blocks if b.get('type') == 'section')
    image_count = sum(1 for b in blocks if b.get('type') == 'image')
    divider_count = sum(1 for b in blocks if b.get('type') == 'divider')
    
    print(f"Section blocks: {section_count}")
    print(f"Image blocks: {image_count}")
    print(f"Divider blocks: {divider_count}")
    
    # Check for potential issues
    print("\n=== Potential Issues Analysis ===")
    
    # Check for very long text sections
    long_sections = [b for b in blocks if b.get('type') == 'section' and 
                    len(b.get('text', {}).get('text', '')) > 3000]
    if long_sections:
        print(f"⚠️  Found {len(long_sections)} sections longer than 3000 characters (Slack limit)")
        for i, section in enumerate(long_sections):
            print(f"    Section {i+1}: {len(section['text']['text'])} characters")
    
    # Check total message size
    total_chars = sum(len(json.dumps(block)) for block in blocks)
    print(f"Total block JSON size: {total_chars} characters")
    if total_chars > 50000:
        print("⚠️  Message may be too large for Slack API")
    
    # Check image URLs
    image_blocks = [b for b in blocks if b.get('type') == 'image']
    print(f"\nImage blocks details:")
    for i, img in enumerate(image_blocks):
        print(f"  {i+1}. Alt: '{img.get('alt_text')}' URL: {img.get('image_url')}")
    
    # Output sample blocks for inspection
    print(f"\n=== Sample Blocks (first 3) ===")
    for i, block in enumerate(blocks[:3]):
        print(f"Block {i+1}: {json.dumps(block, indent=2)}")
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    test_failed_message()