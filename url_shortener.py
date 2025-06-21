import json
import os
import random
import string
import time
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError


class URLShortener:
    """URL Shortener class that can be used as a module in existing Lambda functions"""
    
    def __init__(self, table_name=None, base_url=None):
        """
        Initialize the URL shortener
        
        Args:
            table_name (str): DynamoDB table name. If None, uses TABLE_NAME env var
            base_url (str): Base URL for shortened links. If None, uses BASE_URL env var
        """
        self.table_name = table_name or os.environ.get('URL_TABLE', 'short_urls')
        self.base_url = base_url or os.environ.get('BASE_URL', 'https://short.cerenyi.info')
        
        if not self.table_name:
            raise ValueError("TABLE_NAME must be provided either as parameter or environment variable")
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)
    
    def generate_short_code(self, length=6):
        """Generate a random short code using base62 encoding"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def is_valid_url(self, url):
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def shorten_url(self, url, custom_code=None, max_attempts=10):
            """
            Shorten a URL and return the result
            
            Args:
                url (str): The URL to shorten
                custom_code (str, optional): Custom short code to use
                max_attempts (int): Maximum attempts to generate unique code
                
            Returns:
                dict: Result dictionary with success/error information
            """
            try:
                # Validation
                if not url or not isinstance(url, str):
                    return {
                        'success': False,
                        'error': 'URL is required',
                        'message': 'Please provide a valid URL to shorten'
                    }
                
                url = url.strip()
                
                if not self.is_valid_url(url):
                    return {
                        'success': False,
                        'error': 'Invalid URL format',
                        'message': 'Please provide a valid HTTP or HTTPS URL'
                    }
                
                if len(url) > 2048:
                    return {
                        'success': False,
                        'error': 'URL too long',
                        'message': 'URL must be less than 2048 characters'
                    }
                
                # Handle custom code path
                if custom_code:
                    # Validate custom code
                    if not custom_code.isalnum() or len(custom_code) > 20:
                        return {
                            'success': False,
                            'error': 'Invalid custom code',
                            'message': 'Custom code must be alphanumeric and less than 20 characters'
                        }
                    
                    # Try to create with custom code using conditional put
                    current_time = int(time.time())
                    item = {
                        'shortCode': custom_code,
                        'originalUrl': url,
                        'createdAt': current_time,
                        'clickCount': 0
                    }
                    
                    try:
                        self.table.put_item(
                            Item=item,
                            ConditionExpression='attribute_not_exists(shortCode)'
                        )
                        
                        # Success!
                        return {
                            'success': True,
                            'shortUrl': f"{self.base_url}/{custom_code}",
                            'shortCode': custom_code,
                            'originalUrl': url,
                            'createdAt': current_time
                        }
                        
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                            return {
                                'success': False,
                                'error': 'Custom code already exists',
                                'message': 'Please choose a different custom code'
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'Database error',
                                'message': f'Unable to check custom code: {str(e)}'
                            }
                
                # Generate random short code with race-condition safety
                for attempt in range(max_attempts):
                    candidate_code = self.generate_short_code()
                    current_time = int(time.time())
                    
                    item = {
                        'shortCode': candidate_code,
                        'originalUrl': url,
                        'createdAt': current_time,
                        'clickCount': 0
                    }
                    
                    try:
                        # Atomic operation: only insert if shortCode doesn't exist
                        self.table.put_item(
                            Item=item,
                            ConditionExpression='attribute_not_exists(shortCode)'
                        )
                        
                        # Success! No race condition possible
                        return {
                            'success': True,
                            'shortUrl': f"{self.base_url}/{candidate_code}",
                            'shortCode': candidate_code,
                            'originalUrl': url,
                            'createdAt': current_time
                        }
                        
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                            # Code already exists, try next candidate
                            print(f"Short code collision on attempt {attempt + 1}: {candidate_code}")
                            continue
                        else:
                            # Some other database error
                            print(f"Error storing item in DynamoDB: {e}")
                            return {
                                'success': False,
                                'error': 'Database error',
                                'message': 'Unable to store shortened URL'
                            }
                
                # If we get here, all attempts failed
                return {
                    'success': False,
                    'error': 'Unable to generate unique short code',
                    'message': f'Failed to generate unique code after {max_attempts} attempts'
                }
                
            except Exception as e:
                print(f"Unexpected error in shorten_url: {e}")
                return {
                    'success': False,
                    'error': 'Internal server error',
                    'message': 'Unable to shorten URL at this time'
                }
    
    def get_url(self, short_code):
        """
        Retrieve original URL by short code
        
        Args:
            short_code (str): The short code to look up
            
        Returns:
            dict: Result dictionary with URL information or error
        """
        try:
            if not short_code:
                return {
                    'success': False,
                    'error': 'Short code is required'
                }
            
            response = self.table.get_item(Key={'shortCode': short_code})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Short code not found'
                }
            
            item = response['Item']
            
            # Increment click count
            try:
                self.table.update_item(
                    Key={'shortCode': short_code},
                    UpdateExpression='SET clickCount = clickCount + :inc',
                    ExpressionAttributeValues={':inc': 1}
                )
            except ClientError as e:
                print(f"Error updating click count: {e}")
                # Don't fail the request if click count update fails
            
            return {
                'success': True,
                'originalUrl': item['originalUrl'],
                'shortCode': short_code,
                'createdAt': item.get('createdAt'),
                'clickCount': item.get('clickCount', 0) + 1
            }
            
        except Exception as e:
            print(f"Unexpected error in get_url: {e}")
            return {
                'success': False,
                'error': 'Internal server error',
                'message': 'Unable to retrieve URL at this time'
            }


# Convenience functions for backward compatibility and easy usage
def shorten_url(url, table_name=None, base_url=None, custom_code=None):
    """
    Convenience function to shorten a URL
    
    Args:
        url (str): The URL to shorten
        table_name (str): DynamoDB table name
        base_url (str): Base URL for shortened links
        custom_code (str): Optional custom short code
        
    Returns:
        dict: Result dictionary
    """
    shortener = URLShortener(table_name=table_name, base_url=base_url)
    return shortener.shorten_url(url, custom_code=custom_code)


def get_original_url(short_code, table_name=None):
    """
    Convenience function to get original URL by short code
    
    Args:
        short_code (str): The short code to look up
        table_name (str): DynamoDB table name
        
    Returns:
        dict: Result dictionary
    """
    shortener = URLShortener(table_name=table_name)
    return shortener.get_url(short_code)