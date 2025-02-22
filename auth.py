import os
import requests

def authenticate():
    """
    Authenticates the user and returns a session cookie.
    
    Returns:
    - dict: A dictionary containing the session cookie or an error message.
    """
    odoo_url = os.getenv('ODOO_URL')
    odoo_db = os.getenv('ODOO_DB')
    odoo_login = os.getenv('ODOO_LOGIN')
    odoo_password = os.getenv('ODOO_PASSWORD')

    endpoint = f"{odoo_url}/web/session/authenticate"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "params": {
            "db": odoo_db,
            "login": odoo_login,
            "password": odoo_password
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        session_id = response.cookies.get('session_id')
        if session_id:
            return {'session_id': session_id}
        else:
            return {'error': 'Authentication failed. No session ID returned.'}
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}