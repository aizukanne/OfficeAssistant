# Information Retrieval

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← ERP Integration](erp-integration.md) | [Document Processing →](document-processing.md)

Maria can fetch information from various sources, providing users with up-to-date and relevant data through several information retrieval mechanisms.

## Web Search

Maria can perform web searches to find information on the internet:

### Google Search

```python
def google_search(search_term, before=None, after=None, intext=None, allintext=None, and_condition=None, must_have=None)
```

This function performs a Google search with advanced operators:

- `search_term`: The main search query
- `before`: Limit results to before a specific date
- `after`: Limit results to after a specific date
- `intext`: Find pages containing specific text
- `allintext`: Find pages containing all specified terms
- `and_condition`: Additional terms to include in the search
- `must_have`: Terms that must be present in results

**Example Usage:**

```
User: Search for information about artificial intelligence developments in 2023
Maria: I'll search for that information. Here are the latest AI developments in 2023:
[Search results with summaries]
```

### Web Browsing

```python
def browse_internet(urls, full_text=False)
async def get_web_pages(urls, full_text=False, max_concurrent_requests=5)
```

These functions allow Maria to:

- Retrieve content from specific websites
- Process and analyze web content
- Extract relevant information
- Summarize web pages

**Example Usage:**

```
User: Can you check what's on the NASA website about the latest Mars mission?
Maria: I'll check the NASA website for information about the latest Mars mission.
[Summary of relevant information from NASA's website]
```

## Weather Data

Maria can retrieve weather information for locations:

### Location Coordinates

```python
def get_coordinates(location_name)
```

This function retrieves the latitude and longitude coordinates for a specified location.

**Parameters:**
- `location_name`: The name of the location to get coordinates for

**Example:**
```python
coordinates = get_coordinates("New York")
# Returns: {"lat": 40.7128, "lon": -74.0060}
```

### Weather Information

```python
def get_weather_data(location_name='Whitehorse')
```

This function retrieves current weather data for a location:

**Parameters:**
- `location_name`: The name of the location to get weather data for (defaults to Whitehorse)

**Example Usage:**

```
User: What's the weather like in Tokyo today?
Maria: Let me check the weather in Tokyo for you.
Currently in Tokyo, it's 22°C (72°F) and partly cloudy. 
The humidity is 65% with a light breeze of 8 km/h from the southeast.
There's a 20% chance of precipitation today.
```

## Product Search

Maria can search for products on e-commerce platforms:

### Amazon Product Search

```python
def search_and_format_products(search_term, num_results=5)
```

This function searches for products on Amazon and formats the results:

**Parameters:**
- `search_term`: The product to search for
- `num_results`: The number of results to return (default: 5)

**Example Usage:**

```
User: Find me some wireless headphones on Amazon
Maria: I've found some wireless headphones on Amazon for you:

1. Sony WH-1000XM4 Wireless Noise Canceling Headphones
   Price: $348.00
   Rating: 4.7/5 (34,251 reviews)
   Features: Industry-leading noise cancellation, 30-hour battery life, touch controls

2. Bose QuietComfort 45 Bluetooth Wireless Headphones
   Price: $329.00
   Rating: 4.6/5 (12,789 reviews)
   Features: World-class noise cancellation, 24-hour battery life, comfortable fit

[Additional results...]
```

## Implementation Details

### Web Search Implementation

The web search functionality uses:

- Custom HTTP requests to search engines
- HTML parsing to extract search results
- Content filtering to remove irrelevant information
- Rate limiting to respect service terms

```python
def google_search(search_term, before=None, after=None, intext=None, allintext=None, and_condition=None, must_have=None):
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
    
    # Perform search and parse results
    # ...
    
    return formatted_results
```

### Weather Data Implementation

The weather data functionality uses:

- Geocoding services to convert location names to coordinates
- Weather API integration to retrieve current conditions
- Data formatting for user-friendly presentation

```python
def get_weather_data(location_name='Whitehorse'):
    # Get coordinates for the location
    coordinates = get_coordinates(location_name)
    
    # Build API request
    url = f"{WEATHER_API_URL}?lat={coordinates['lat']}&lon={coordinates['lon']}&units=metric&appid={WEATHER_API_KEY}"
    
    # Make request and parse response
    # ...
    
    return formatted_weather_data
```

### Product Search Implementation

The product search functionality uses:

- Amazon product API or web scraping
- Result filtering and ranking
- Data formatting for clear presentation

```python
def search_and_format_products(search_term, num_results=5):
    # Perform product search
    # ...
    
    # Format results
    formatted_results = []
    for product in results[:num_results]:
        formatted_results.append({
            "title": product["title"],
            "price": product["price"],
            "rating": product["rating"],
            "reviews": product["review_count"],
            "features": product["features"],
            "url": product["url"]
        })
    
    return formatted_results
```

## Best Practices

When using information retrieval functionality:

- Be specific in search queries to get more relevant results
- Provide location context for weather queries
- Use product-specific terms for better product search results
- Consider privacy implications when searching for sensitive information
- Be aware of potential rate limits on external services

## Future Enhancements

Planned enhancements for information retrieval include:

- Enhanced search filtering options
- Integration with additional data sources
- Improved result summarization
- Personalized search based on user preferences
- Multi-source information synthesis

---

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← ERP Integration](erp-integration.md) | [Document Processing →](document-processing.md)