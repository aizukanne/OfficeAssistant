import requests
import json
from typing import Dict, List, Optional, Union, Any

def search_amazon_products(
    query: str,
    country: str = "CA",
    page: int = 1,
    sort_by: str = "RELEVANCE",
    product_condition: str = "NEW",
    is_prime: bool = False,
    deals_and_discounts: str = "NONE"
) -> Dict[str, Any]:
    """
    Search for products on Amazon using the Real-Time Amazon Data API from RapidAPI.
    
    Parameters:
    ----------
    query : str
        The search term to query Amazon with
    country : str, optional
        The Amazon marketplace country code (default: "US")
    page : int, optional
        The page number of results (default: 1)
    sort_by : str, optional
        How to sort the results (default: "RELEVANCE")
        Options: "RELEVANCE", "PRICE_LOW_TO_HIGH", "PRICE_HIGH_TO_LOW", "RATING", "NEWEST"
    product_condition : str, optional
        Product condition filter (default: "NEW")
        Options: "NEW", "USED", "REFURBISHED"
    is_prime : bool, optional
        Filter for Amazon Prime eligible products (default: False)
    deals_and_discounts : str, optional
        Filter for deals and discounts (default: "NONE")
        Options: "NONE", "TODAY_DEALS", "ON_SALE"
        
    Returns:
    -------
    Dict[str, Any]
        The full API response as a dictionary
    """
    url = "https://real-time-amazon-data.p.rapidapi.com/search"
    
    # Convert boolean to string for the API
    is_prime_str = str(is_prime).lower()
    
    querystring = {
        "query": query,
        "country": country,
        "page": str(page),
        "sort_by": sort_by,
        "product_condition": product_condition,
        "is_prime": is_prime_str,
        "deals_and_discounts": deals_and_discounts
    }
    
    headers = {
        "X-RapidAPI-Key": "4c37223acemsh65b1a8b456b72c1p15a99ajsnd4a09ab346a4",
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "ERROR", "message": str(e)}


def format_product_results(response_data: Dict[str, Any], max_products: int = 5) -> str:
    """
    Format the API response data into a readable string format.
    
    Parameters:
    ----------
    response_data : Dict[str, Any]
        The API response data
    max_products : int, optional
        Maximum number of products to include in the formatted output (default: 5)
        
    Returns:
    -------
    str
        A formatted string containing the product information
    """
    if response_data.get("status") != "OK":
        return f"Error: {response_data.get('message', 'Unknown error')}"
    
    data = response_data.get("data", {})
    total_products = data.get("total_products", 0)
    products = data.get("products", [])
    
    if not products:
        return "No products found."
    
    result = f"Found {total_products} products. Showing top {min(max_products, len(products))}:\n\n"
    
    for i, product in enumerate(products[:max_products], 1):
        title = product.get("product_title", "No title")
        price = product.get("product_price", "Price not available")
        rating = product.get("product_star_rating", "No rating")
        num_ratings = product.get("product_num_ratings", 0)
        url = product.get("product_url", "URL not available")
        
        result += f"{i}. {title}\n"
        result += f"   Price: {price}\n"
        result += f"   URL: {url}\n"
        
        if rating and num_ratings:
            result += f"   Rating: {rating}/5 ({num_ratings} reviews)\n"
        
        # Add best seller or Amazon's choice badge if applicable
        if product.get("is_best_seller"):
            result += f"   🏆 Best Seller\n"
        if product.get("is_amazon_choice"):
            result += f"   ✅ Amazon's Choice\n"
        
        # Add delivery information if available
        delivery = product.get("delivery")
        if delivery:
            result += f"   Delivery: {delivery}\n"
        
        result += "\n"
    
    return result


def search_and_format_products(
    query: str,
    country: str = "US",
    max_products: int = 5,
    **kwargs
) -> str:
    """
    Search for products on Amazon and return formatted results.
    
    Parameters:
    ----------
    query : str
        The search term to query Amazon with
    country : str, optional
        The Amazon marketplace country code (default: "US")
    max_products : int, optional
        Maximum number of products to show in results (default: 5)
    **kwargs : 
        Additional parameters to pass to the search_amazon_products function
        
    Returns:
    -------
    str
        A formatted string containing the product information
    """
    response = search_amazon_products(query=query, country=country, **kwargs)
    return format_product_results(response, max_products)
