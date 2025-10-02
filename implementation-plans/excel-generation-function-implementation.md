# Excel Generation Function Implementation Plan

## Overview
Implementation of `send_as_excel` function following the existing `send_as_pdf` pattern for generating and uploading Excel spreadsheets from structured data.

## Implementation Directives

### 1. Tool Definition - `tools.py`

**Location**: Add to the `tools` list in [`tools.py`](../tools.py) at the end of the array (around line 712)

```python
{
    "type": "function",
    "function": {
        "name": "send_as_excel",
        "description": "Converts structured data to an Excel spreadsheet and uploads it to a specified Slack channel. Supports JSON data, lists of dictionaries, and CSV-formatted text input. Perfect for creating data reports, tables, and structured information sharing.",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Structured data to convert to Excel. Can be JSON array string, CSV-formatted text, or other structured data formats. Each row should represent a record with consistent fields."
                },
                "chat_id": {
                    "type": "string",
                    "description": "The ID of the Slack channel where the Excel file will be uploaded."
                },
                "title": {
                    "type": "string",
                    "description": "The title of the Excel file to be uploaded (without .xlsx extension)."
                },
                "ts": {
                    "type": "string",
                    "description": "Optional. The thread timestamp (ts) to reply in a thread."
                },
                "sheet_name": {
                    "type": "string", 
                    "description": "Optional. The name of the worksheet. Defaults to 'Sheet1'."
                },
                "include_headers": {
                    "type": "boolean",
                    "description": "Optional. Whether to include column headers in the first row. Defaults to true."
                }
            },
            "required": ["data", "chat_id", "title"]
        }
    }
}
```

### 2. Core Function Implementation - `lambda_function.py`

**Location**: Add after the `send_as_pdf` function (around line 1250)

```python
def parse_excel_data(data):
    """
    Parse various input formats into standardized structure for Excel generation.
    
    Args:
        data (str): Input data in JSON, CSV, or other structured format
        
    Returns:
        tuple: (headers, rows) where headers is list of column names and rows is list of dictionaries
    """
    try:
        # Try parsing as JSON first
        if isinstance(data, str) and (data.strip().startswith('[') or data.strip().startswith('{')):
            parsed_data = json.loads(data)
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                if isinstance(parsed_data[0], dict):
                    headers = list(parsed_data[0].keys())
                    return headers, parsed_data
                else:
                    # List of lists format
                    headers = [f"Column_{i+1}" for i in range(len(parsed_data[0]))]
                    rows = [dict(zip(headers, row)) for row in parsed_data]
                    return headers, rows
        
        # Try parsing as CSV
        if '\n' in data and (',' in data or '\t' in data):
            lines = data.strip().split('\n')
            delimiter = ',' if ',' in data else '\t'
            
            reader = csv.DictReader(lines, delimiter=delimiter)
            rows = list(reader)
            if rows:
                headers = list(rows[0].keys())
                return headers, rows
        
        # Fallback: treat as single cell data
        return ['Data'], [{'Data': data}]
        
    except json.JSONDecodeError:
        # If JSON parsing fails, try CSV
        try:
            lines = data.strip().split('\n')
            delimiter = ',' if ',' in data else '\t'
            reader = csv.DictReader(lines, delimiter=delimiter)
            rows = list(reader)
            if rows:
                headers = list(rows[0].keys())
                return headers, rows
        except:
            pass
    
    except Exception as e:
        logger.error(f"Error parsing excel data: {str(e)}")
    
    # Ultimate fallback
    return ['Data'], [{'Data': str(data)}]


class ExcelGenerator:
    """
    Excel generation class with basic formatting and styling.
    """
    
    def __init__(self, title, sheet_name='Sheet1'):
        """Initialize Excel generator with workbook and worksheet."""
        self.workbook = openpyxl.Workbook()
        self.worksheet = self.workbook.active
        self.worksheet.title = sheet_name
        self.title = title
        
    def write_data(self, headers, rows, include_headers=True):
        """
        Write data to Excel worksheet with basic formatting.
        
        Args:
            headers (list): Column headers
            rows (list): List of dictionaries containing row data
            include_headers (bool): Whether to include header row
        """
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
        from openpyxl.utils import get_column_letter
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        border = Border(left=Side(border_style="thin"),
                       right=Side(border_style="thin"),
                       top=Side(border_style="thin"),
                       bottom=Side(border_style="thin"))
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        row_num = 1
        
        # Write headers if enabled
        if include_headers:
            for col_num, header in enumerate(headers, 1):
                cell = self.worksheet.cell(row=row_num, column=col_num)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = center_alignment
            row_num += 1
        
        # Write data rows
        for row_data in rows:
            for col_num, header in enumerate(headers, 1):
                cell = self.worksheet.cell(row=row_num, column=col_num)
                cell.value = row_data.get(header, "")
                cell.border = border
                
                # Auto-format numbers
                if isinstance(cell.value, (int, float)):
                    cell.alignment = Alignment(horizontal="right")
                elif isinstance(cell.value, str):
                    cell.alignment = Alignment(horizontal="left")
                    
            row_num += 1
        
        # Auto-size columns
        for col_num in range(1, len(headers) + 1):
            column_letter = get_column_letter(col_num)
            column = self.worksheet[column_letter]
            max_length = 0
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap width at 50
            self.worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def save(self, filepath):
        """Save workbook to specified file path."""
        self.workbook.save(filepath)


def send_as_excel(data, chat_id, title, ts=None, sheet_name='Sheet1', include_headers=True):
    """
    Generate Excel spreadsheet from structured data and upload to Slack.
    
    Args:
        data (str): Structured data (JSON, CSV, etc.)
        chat_id (str): Slack channel ID
        title (str): Excel filename (without .xlsx extension)
        ts (str, optional): Slack thread timestamp
        sheet_name (str, optional): Worksheet name
        include_headers (bool, optional): Whether to include column headers
        
    Returns:
        str: Status message indicating success or failure
    """
    excel_path = f"/tmp/{title}.xlsx"
    
    try:
        # Parse input data
        headers, rows = parse_excel_data(data)
        
        if not rows:
            return "Failure: No valid data found to convert to Excel"
        
        # Generate Excel file
        excel_generator = ExcelGenerator(title, sheet_name)
        excel_generator.write_data(headers, rows, include_headers)
        excel_generator.save(excel_path)
        
        # Upload to S3
        try:
            bucket_name = docs_bucket_name
            folder_name = 'uploads'
            file_key = f"{folder_name}/{title}.xlsx"
            s3_client = boto3.client('s3')
            s3_client.upload_file(excel_path, bucket_name, file_key)
            s3_status = "uploaded to S3"
        except NameError:
            s3_status = "S3 upload skipped (docs_bucket_name not defined)"
        except Exception as s3_error:
            s3_status = f"S3 upload failed: {s3_error}"
        
        # Upload to Slack
        try:
            send_file_to_slack(excel_path, chat_id, title, ts)
            slack_status = "sent to Slack"
        except NameError:
            slack_status = "Slack upload skipped (send_file_to_slack not defined)"
        except Exception as slack_error:
            slack_status = f"Slack upload failed: {slack_error}"
        
        status = f"Success: Excel file generated with {len(rows)} rows, {s3_status}, and {slack_status}."
        
    except Exception as e:
        status = f"Failure: {str(e)}"
        logger.error(f"Error in send_as_excel: {str(e)}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(excel_path):
            os.remove(excel_path)
            
    return status
```

### 3. Function Mapping - `lambda_function.py`

**Location**: Add to the `common_functions` dictionary in `get_available_functions()` (around line 507)

```python
"send_as_excel": send_as_excel,
```

### 4. Cerebras Integration - `conversation.py`

**Location**: Add to the `tool_names` set in `select_cerebras_tools()` function (around line 575)

```python
"send_as_excel",
```

### 5. Required Imports

**Verify these imports exist in `lambda_function.py` (they should already be present):**
- `import openpyxl` (line 15)
- `import csv` (line 7)
- `import json` (line 9)

## Testing Requirements

### 1. Unit Tests
Create test file: `tests/test_excel_generation.py`

```python
def test_parse_excel_data_json():
    """Test JSON data parsing"""
    json_data = '[{"Name": "John", "Age": 30}, {"Name": "Jane", "Age": 25}]'
    headers, rows = parse_excel_data(json_data)
    assert headers == ["Name", "Age"]
    assert len(rows) == 2
    assert rows[0]["Name"] == "John"

def test_parse_excel_data_csv():
    """Test CSV data parsing"""
    csv_data = "Name,Age\nJohn,30\nJane,25"
    headers, rows = parse_excel_data(csv_data)
    assert headers == ["Name", "Age"]
    assert len(rows) == 2

def test_excel_generation():
    """Test Excel file generation"""
    generator = ExcelGenerator("test", "TestSheet")
    headers = ["Name", "Age"]
    rows = [{"Name": "John", "Age": 30}, {"Name": "Jane", "Age": 25}]
    generator.write_data(headers, rows, True)
    # Test file creation and content
```

### 2. Integration Tests

Add to existing test files:

**`test_complete_integration.py`:**
```python
def test_send_as_excel_function_mapping():
    """Test that send_as_excel is in function mapping"""
    from lambda_function import get_available_functions
    functions = get_available_functions()
    assert "send_as_excel" in functions

def test_cerebras_excel_tool_filtering():
    """Test that send_as_excel is in Cerebras tool selection"""
    from conversation import select_cerebras_tools
    from tools import tools
    
    cerebras_tools = select_cerebras_tools(tools)
    tool_names = [tool['function']['name'] for tool in cerebras_tools]
    assert "send_as_excel" in tool_names
```

## Implementation Checklist

- [ ] **Step 1**: Add tool definition to `tools.py`
- [ ] **Step 2**: Implement core functions in `lambda_function.py`:
  - [ ] `parse_excel_data()`
  - [ ] `ExcelGenerator` class
  - [ ] `send_as_excel()` main function
- [ ] **Step 3**: Add function to `common_functions` mapping in `get_available_functions()`
- [ ] **Step 4**: Add function name to `tool_names` set in `select_cerebras_tools()`
- [ ] **Step 5**: Create unit tests for data parsing and Excel generation
- [ ] **Step 6**: Add integration tests for function mapping and Cerebras tool selection
- [ ] **Step 7**: Test with sample JSON and CSV data
- [ ] **Step 8**: Verify S3 upload and Slack file sharing functionality

## Usage Examples

### JSON Data Input
```python
data = '[{"Product": "Laptop", "Price": 999.99, "Stock": 50}, {"Product": "Mouse", "Price": 29.99, "Stock": 200}]'
result = send_as_excel(data, "C12345", "Product_Inventory", sheet_name="Products")
```

### CSV Data Input
```python
data = "Name,Department,Salary\nJohn Doe,Engineering,75000\nJane Smith,Marketing,65000"
result = send_as_excel(data, "C12345", "Employee_Report", include_headers=True)
```

### LLM Usage
```
User: "Can you create an Excel file with the following sales data and send it to our team channel?"
LLM: Uses send_as_excel function with provided data, appropriate channel ID, and descriptive title.
```

## Error Handling

The implementation includes comprehensive error handling for:
- Invalid JSON/CSV format
- Empty or malformed data
- S3 upload failures (graceful degradation)
- Slack upload failures (graceful degradation)
- File system errors
- Excel generation errors

## File Size and Performance Considerations

- **Row Limit**: Consider implementing a reasonable limit (e.g., 10,000 rows) for performance
- **Column Limit**: Limit columns to prevent excessive memory usage
- **File Size**: Monitor generated Excel file sizes and implement warnings for large datasets
- **Cleanup**: Ensure temporary files are always cleaned up, even on error

## Future Enhancements

- Support for multiple worksheets
- Advanced formatting options (colors, fonts, borders)
- Chart generation from data
- Template-based Excel generation
- Data validation and conditional formatting