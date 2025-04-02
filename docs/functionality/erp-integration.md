# ERP Integration

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Communication](communication.md) | [Information Retrieval →](information-retrieval.md)

Maria provides robust integration with Enterprise Resource Planning (ERP) systems, allowing users to access and manipulate business data directly through conversational interfaces.

## ERPNext Integration

Maria integrates with ERPNext to provide access to business data and operations:

### Available Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `erpnext_list_doctypes` | List available document types | None |
| `erpnext_list_doctype_fields` | List fields for a document type | `doctype_name` |
| `erpnext_get_documents` | Fetch documents based on criteria | `doc_type`, `document_name`, `fields`, `filters`, `limit_page_length`, `limit_start` |

### Example Usage

```
User: Can you list all the sales orders from last month?
Maria: I'll retrieve that information for you. Here are the sales orders from last month:
[List of sales orders with details]
```

### Implementation Details

The ERPNext integration is implemented in `erpnext_functions.py` and provides the following capabilities:

```python
def erpnext_get_documents(doc_type, document_name=None, fields=None, filters=None, limit_page_length=20, limit_start=0)
def erpnext_list_doctypes()
def erpnext_list_doctype_fields(doctype_name)
```

These functions communicate with the ERPNext API to retrieve and manipulate data.

## Odoo Integration

Maria also integrates with Odoo ERP system for comprehensive business operations:

### Available Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `odoo_get_mapped_models` | Get mapped models and their fields | `include_fields`, `model_name` |
| `odoo_get_mapped_fields` | Get fields for a specific model | `model` |
| `odoo_fetch_records` | Retrieve records based on criteria | `external_model`, `filters` |
| `odoo_create_record` | Create a new record | `external_model`, `**kwargs` |
| `odoo_update_record` | Update an existing record | `external_model`, `record_id`, `**kwargs` |
| `odoo_delete_record` | Delete a record | `external_model`, `record_id` |

### Example Usage

```
User: Create a new customer named "Acme Corporation" with email "contact@acme.com"
Maria: I'll create that customer record for you. 
[Creates the record]
The customer "Acme Corporation" has been created successfully with ID #1234.
```

### Implementation Details

The Odoo integration is implemented in `odoo_functions.py` and provides the following capabilities:

```python
def authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
def odoo_get_mapped_models(include_fields=True, model_name=None)
def odoo_get_mapped_fields(model)
def odoo_fetch_records(external_model, filters=None)
def odoo_create_record(external_model, **kwargs)
def odoo_update_record(external_model, record_id, **kwargs)
def odoo_delete_record(external_model, record_id)
```

These functions communicate with the Odoo API to retrieve and manipulate data.

## Integration Architecture

The ERP integrations follow a common pattern:

1. **Authentication**: Secure connection to the ERP system
2. **Model Discovery**: Retrieving available models and fields
3. **Data Operations**: Creating, reading, updating, and deleting records
4. **Response Formatting**: Converting API responses to user-friendly formats

This architecture allows Maria to provide a consistent interface across different ERP systems.

## Best Practices

When working with ERP integrations:

- Provide specific criteria to narrow down results
- Use field lists to limit the data returned
- Handle pagination for large result sets
- Include error handling for API failures
- Respect user permissions and access controls

## Future Enhancements

Planned enhancements for ERP integration include:

- Support for additional ERP systems
- Enhanced reporting capabilities
- Workflow automation
- Document generation
- Multi-system operations

---

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Communication](communication.md) | [Information Retrieval →](information-retrieval.md)