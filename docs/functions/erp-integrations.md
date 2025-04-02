# ERP Integrations

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Media Processing](media-processing.md) | [External Services →](external-services.md)

The ERP integrations modules in `erpnext_functions.py` and `odoo_functions.py` provide functionality for interacting with Enterprise Resource Planning (ERP) systems, enabling Maria to access and manipulate business data.

## Overview

The ERP integration modules handle:

- Connecting to ERP systems
- Retrieving document types and fields
- Fetching, creating, updating, and deleting records
- Formatting ERP data for user consumption

## ERPNext Functions

The `erpnext_functions.py` module provides integration with the ERPNext ERP system.

### Get Documents

```python
def erpnext_get_documents(doc_type, document_name=None, fields=None, filters=None, limit_page_length=20, limit_start=0)
```

This function retrieves documents from ERPNext:

**Parameters:**
- `doc_type`: The type of document to retrieve
- `document_name`: (Optional) The name of a specific document
- `fields`: (Optional) List of fields to retrieve
- `filters`: (Optional) Filters to apply
- `limit_page_length`: (Optional) Maximum number of records to retrieve (default: 20)
- `limit_start`: (Optional) Starting index for pagination (default: 0)

**Returns:**
- A list of documents matching the criteria

**Example:**
```python
# Get all sales orders
sales_orders = erpnext_get_documents("Sales Order")

# Get a specific sales order
order = erpnext_get_documents("Sales Order", "SO-00001")

# Get sales orders with filters
filtered_orders = erpnext_get_documents(
    "Sales Order",
    filters={"status": "Open", "transaction_date": [">=", "2023-01-01"]}
)
```

**Example Usage:**

```
User: Show me the open sales orders from January 2023
Maria: Here are the open sales orders from January 2023:

1. SO-00123: Customer ABC, $5,000.00, Due: Feb 15, 2023
2. SO-00124: Customer XYZ, $7,500.00, Due: Feb 28, 2023
3. SO-00125: Customer DEF, $3,200.00, Due: Feb 10, 2023
```

### List DocTypes

```python
def erpnext_list_doctypes()
```

This function lists available document types in ERPNext:

**Returns:**
- A list of available document types

**Example:**
```python
doctypes = erpnext_list_doctypes()
```

**Example Usage:**

```
User: What types of documents can I access in ERPNext?
Maria: Here are the document types available in ERPNext:

1. Sales Order
2. Purchase Order
3. Customer
4. Supplier
5. Item
6. Invoice
7. Payment Entry
8. Journal Entry
...
```

### List DocType Fields

```python
def erpnext_list_doctype_fields(doctype_name)
```

This function lists fields for a specific document type:

**Parameters:**
- `doctype_name`: The name of the document type

**Returns:**
- A list of fields for the specified document type

**Example:**
```python
fields = erpnext_list_doctype_fields("Sales Order")
```

**Example Usage:**

```
User: What fields are available for a Customer in ERPNext?
Maria: Here are the fields available for a Customer in ERPNext:

1. name: The customer ID
2. customer_name: The customer's full name
3. customer_type: Individual or Company
4. customer_group: The customer group
5. territory: The customer's territory
6. tax_id: Tax identification number
7. default_currency: Default currency for transactions
8. default_price_list: Default price list
...
```

## Odoo Functions

The `odoo_functions.py` module provides integration with the Odoo ERP system.

### Authentication

```python
def authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
```

This function authenticates with the Odoo API:

**Parameters:**
- `odoo_url`: The URL of the Odoo instance
- `odoo_db`: The database name
- `odoo_login`: The login username
- `odoo_password`: The login password

**Returns:**
- An authenticated Odoo client

**Example:**
```python
client = authenticate("https://example.odoo.com", "example_db", "admin", "password")
```

### Get Mapped Models

```python
def odoo_get_mapped_models(include_fields=True, model_name=None)
```

This function retrieves mapped models from Odoo:

**Parameters:**
- `include_fields`: (Optional) Whether to include fields (default: True)
- `model_name`: (Optional) A specific model name to retrieve

**Returns:**
- A dictionary of mapped models

**Example:**
```python
# Get all models with fields
models = odoo_get_mapped_models()

# Get a specific model
model = odoo_get_mapped_models(model_name="res.partner")
```

**Example Usage:**

```
User: What models are available in Odoo?
Maria: Here are the available models in Odoo:

1. res.partner: Partners (customers, suppliers)
2. sale.order: Sales Orders
3. purchase.order: Purchase Orders
4. product.template: Products
5. account.invoice: Invoices
...
```

### Get Mapped Fields

```python
def odoo_get_mapped_fields(model)
```

This function retrieves fields for a specific model:

**Parameters:**
- `model`: The model name

**Returns:**
- A dictionary of fields for the specified model

**Example:**
```python
fields = odoo_get_mapped_fields("res.partner")
```

**Example Usage:**

```
User: What fields are available for a Product in Odoo?
Maria: Here are the fields available for a Product in Odoo:

1. name: Product name
2. description: Product description
3. list_price: Sales price
4. standard_price: Cost price
5. default_code: Internal reference
6. barcode: Barcode
7. active: Active status
8. sale_ok: Can be sold
9. purchase_ok: Can be purchased
...
```

### Fetch Records

```python
def odoo_fetch_records(external_model, filters=None)
```

This function retrieves records from Odoo:

**Parameters:**
- `external_model`: The model name
- `filters`: (Optional) Filters to apply

**Returns:**
- A list of records matching the criteria

**Example:**
```python
# Get all customers
customers = odoo_fetch_records("res.partner", [("customer_rank", ">", 0)])

# Get products with filters
products = odoo_fetch_records("product.template", [("sale_ok", "=", True), ("list_price", ">", 100)])
```

**Example Usage:**

```
User: Show me active products with a price over $100
Maria: Here are the active products with a price over $100:

1. Laptop X1: $1,299.00, In Stock: 25
2. Smartphone Pro: $899.00, In Stock: 42
3. Wireless Headphones: $199.00, In Stock: 78
4. Tablet Ultra: $649.00, In Stock: 15
...
```

### Create Record

```python
def odoo_create_record(external_model, **kwargs)
```

This function creates a new record in Odoo:

**Parameters:**
- `external_model`: The model name
- `**kwargs`: Fields and values for the new record

**Returns:**
- The ID of the created record

**Example:**
```python
# Create a new customer
customer_id = odoo_create_record(
    "res.partner",
    name="Acme Corporation",
    email="contact@acme.com",
    phone="123-456-7890",
    customer_rank=1
)
```

**Example Usage:**

```
User: Create a new customer named "Acme Corporation" with email "contact@acme.com" and phone "123-456-7890"
Maria: I've created a new customer in Odoo:
Name: Acme Corporation
Email: contact@acme.com
Phone: 123-456-7890
Customer ID: 42
```

### Update Record

```python
def odoo_update_record(external_model, record_id, **kwargs)
```

This function updates an existing record in Odoo:

**Parameters:**
- `external_model`: The model name
- `record_id`: The ID of the record to update
- `**kwargs`: Fields and values to update

**Returns:**
- True if successful, False otherwise

**Example:**
```python
# Update a customer
success = odoo_update_record(
    "res.partner",
    42,
    email="new.email@acme.com",
    phone="987-654-3210"
)
```

**Example Usage:**

```
User: Update the email for customer Acme Corporation to "new.email@acme.com"
Maria: I've updated the customer information:
Name: Acme Corporation
New Email: new.email@acme.com
Customer ID: 42
```

### Delete Record

```python
def odoo_delete_record(external_model, record_id)
```

This function deletes a record from Odoo:

**Parameters:**
- `external_model`: The model name
- `record_id`: The ID of the record to delete

**Returns:**
- True if successful, False otherwise

**Example:**
```python
# Delete a customer
success = odoo_delete_record("res.partner", 42)
```

**Example Usage:**

```
User: Delete the customer record for Acme Corporation
Maria: I've deleted the customer record for Acme Corporation (ID: 42).
```

## Implementation Details

### ERPNext API Integration

The ERPNext integration uses the Frappe REST API:

```python
def erpnext_api_call(method, endpoint, data=None):
    """Make an API call to ERPNext."""
    url = f"{ERPNEXT_URL}/api/method/{endpoint}"
    headers = {
        "Authorization": f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}",
        "Content-Type": "application/json"
    }
    
    if method == "GET":
        response = requests.get(url, headers=headers, params=data)
    else:
        response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        logger.error(f"ERPNext API error: {response.status_code} - {response.text}")
        return None
    
    return response.json()
```

### Odoo API Integration

The Odoo integration uses the XML-RPC API:

```python
def odoo_api_call(model, method, *args, **kwargs):
    """Make an API call to Odoo."""
    try:
        # Get authenticated client
        client = authenticate(ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_PASSWORD)
        
        # Call the method
        result = getattr(client.env[model], method)(*args, **kwargs)
        
        return result
    except Exception as e:
        logger.error(f"Odoo API error: {str(e)}")
        return None
```

## Best Practices

When working with ERP integrations:

- Use appropriate filters to limit result sets
- Handle authentication securely
- Implement proper error handling
- Consider rate limiting and API quotas
- Cache frequently accessed data
- Validate input data before creating or updating records
- Respect user permissions and access controls

## Future Enhancements

Planned enhancements for ERP integrations include:

- Support for additional ERP systems
- Enhanced reporting capabilities
- Workflow automation
- Batch operations for improved performance
- Real-time data synchronization
- Advanced filtering options

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Media Processing](media-processing.md) | [External Services →](external-services.md)