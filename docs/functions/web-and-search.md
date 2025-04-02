# Web and Search

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← External Services](external-services.md) | [Document Management →](document-management.md)

The web and search functions in `lambda_function.py` provide capabilities for searching the web, browsing internet content, and retrieving information from online sources.

## Overview

The web and search functions enable Maria to:

- Perform Google searches with advanced operators
- Retrieve and analyze content from websites
- Process and summarize web content
- Handle concurrent web requests
- Extract relevant information from web pages

## Google Search

```python
def google_search(search_term, before=None, after=None, intext=None, allintext=None, and_condition=None, must_have=None)
```

This function performs a Google search with advanced operators:

**Parameters:**
- `search_term`: The main search query
- `before`: (Optional) Limit results to before a specific date
- `after`: (Optional) Limit results to after a specific date
- `intext`: (Optional) Find pages containing specific text
- `allintext`: (Optional) Find pages containing all specified terms
- `and_condition`: (Optional) Additional terms to include in the search
- `must_have`: (Optional) Terms that must be present in results

**Returns:**
- Search results with titles, snippets, and URLs

**Example:**
```python
# Basic search
results = google_search("artificial intelligence")

# Search with date range
results = google_search("artificial intelligence", after="2023-01-01", before="2023-12-31")

# Search with specific text requirements
results = google_search("artificial intelligence", intext="machine learning", must_have="neural networks")
```

**Example Usage:**

```
User: Search for recent developments in quantum computing
Maria: I'll search for recent developments in quantum computing. Here's what I found:

1. "Breakthrough in Quantum Error Correction Announced by Research Team"
   Scientists have developed a new approach to quantum error correction that could significantly improve the stability of quantum computers.
   URL: https://example.com/quantum-error-correction

2. "Tech Giant Unveils 1000-Qubit Quantum Processor"
   The new processor represents a major milestone in scaling quantum computing technology.
   URL: https://example.com/quantum-processor-announcement

3. "Quantum Advantage Demonstrated in Chemistry Simulation"
   Researchers have shown that quantum computers can now solve certain chemistry problems faster than classical supercomputers.
   URL: https://example.com/quantum-chemistry-advantage
```

## Browse Internet

```python
def browse_internet(urls, full_text=False)
```

This function retrieves and processes content from websites:

**Parameters:**
- `urls`: A list of URLs to retrieve
- `full_text`: (Optional) Whether to return the full text or a summary (default: False)

**Returns:**
- Processed content from the specified URLs

**Example:**
```python
# Get summaries of web pages
content = browse_internet(["https://example.com/article1", "https://example.com/article2"])

# Get full text of web pages
full_content = browse_internet(["https://example.com/article1"], full_text=True)
```

**Example Usage:**

```
User: Can you check what the latest news is on the NASA website?
Maria: I'll check the NASA website for the latest news. Here's what I found:

NASA has announced a new mission to explore Jupiter's moon Europa, scheduled to launch in 2024. The mission will focus on determining whether Europa's subsurface ocean could harbor conditions suitable for life.

The agency also released new images from the James Webb Space Telescope showing unprecedented details of a star-forming region in the Orion Nebula.

Additionally, NASA reported that the International Space Station has successfully completed its orbital adjustment to avoid space debris.
```

## Get Web Pages

```python
async def get_web_pages(urls, full_text=False, max_concurrent_requests=5)
```

This function asynchronously retrieves content from multiple web pages:

**Parameters:**
- `urls`: A list of URLs to retrieve
- `full_text`: (Optional) Whether to return the full text or a summary (default: False)
- `max_concurrent_requests`: (Optional) Maximum number of concurrent requests (default: 5)

**Returns:**
- Content from the specified URLs

**Example:**
```python
# Get content from multiple web pages concurrently
content = await get_web_pages(["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"])
```

## Implementation Details

### Google Search Implementation

```python
def google_search(search_term, before=None, after=None, intext=None, allintext=None, and_condition=None, must_have=None):
    """Perform a Google search with advanced operators."""
    try:
        # Build search query with operators
        query = search_term
        
        if before:
            query += f" before:{before}"
        if after:
            query += f" after:{after}"
        if intext:
            query += f" intext:{intext}"
        if allintext:
            query += f" allintext:{allintext}"
        if and_condition:
            query += f" AND {and_condition}"
        if must_have:
            query += f" \"{must_have}\""
        
        # Encode the query
        encoded_query = urllib.parse.quote_plus(query)
        
        # Set up the search request
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={encoded_query}"
        
        # Make the request
        response = requests.get(url)
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"Google Search API error: {response.status_code} - {response.text}")
            return []
        
        # Parse the response
        data = response.json()
        
        # Extract search results
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                })
        
        return results
    
    except Exception as e:
        logger.error(f"Error in google_search: {str(e)}")
        return []
```

### Browse Internet Implementation

```python
def browse_internet(urls, full_text=False):
    """Retrieve and process content from websites."""
    try:
        # Use asyncio to get web pages concurrently
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(get_web_pages(urls, full_text))
        loop.close()
        
        return results
    
    except Exception as e:
        logger.error(f"Error in browse_internet: {str(e)}")
        return []
```

### Get Web Pages Implementation

```python
async def get_web_pages(urls, full_text=False, max_concurrent_requests=5):
    """Asynchronously retrieve content from multiple web pages."""
    try:
        # Set up the semaphore for limiting concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Define the fetch function
        async def fetch_url(session, url):
            async with semaphore:
                try:
                    # Select a random user agent
                    headers = {
                        "User-Agent": random.choice(USER_AGENTS),
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1"
                    }
                    
                    # Make the request
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status != 200:
                            logger.error(f"Error fetching {url}: {response.status}")
                            return {"url": url, "content": "", "error": f"HTTP {response.status}"}
                        
                        # Get the content
                        html = await response.text()
                        
                        # Process the HTML
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.extract()
                        
                        # Get text
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = "\n".join(chunk for chunk in chunks if chunk)
                        
                        # Return full text or summary
                        if full_text:
                            return {"url": url, "content": text, "error": None}
                        else:
                            # Create a summary (first 1000 characters)
                            summary = text[:1000] + "..." if len(text) > 1000 else text
                            return {"url": url, "content": summary, "error": None}
                
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
                    return {"url": url, "content": "", "error": str(e)}
        
        # Create a session and fetch all URLs
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
        
        return results
    
    except Exception as e:
        logger.error(f"Error in get_web_pages: {str(e)}")
        return []
```

## Web Content Processing

The web and search functions include several content processing capabilities:

### HTML Parsing

Web content is parsed using BeautifulSoup to:

- Extract text content
- Remove scripts and styles
- Identify main content areas
- Clean up formatting

### Content Summarization

For large web pages, content is summarized by:

- Extracting key sentences
- Identifying main topics
- Removing boilerplate content
- Focusing on relevant information

### Result Formatting

Search results and web content are formatted for user consumption:

- Clear titles and descriptions
- Relevant snippets
- Source attribution
- Organized presentation

## Best Practices

When working with web and search functions:

- Use specific search terms for better results
- Respect website terms of service
- Implement rate limiting for API calls
- Handle timeouts and connection issues
- Process content to extract relevant information
- Provide source attribution
- Consider privacy implications

## Future Enhancements

Planned enhancements for web and search include:

- Enhanced content extraction
- Improved summarization algorithms
- Multi-language search support
- Image and video search capabilities
- Semantic search features
- Real-time information updates

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← External Services](external-services.md) | [Document Management →](document-management.md)