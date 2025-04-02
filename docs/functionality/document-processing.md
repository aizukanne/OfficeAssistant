# Document Processing

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Information Retrieval](information-retrieval.md) | [Message Management →](message-management.md)

Maria can work with various document formats, providing capabilities for file operations, document analysis, and content processing.

## File Operations

Maria can perform various file operations to manage documents:

### List Files

```python
def list_files(folder_prefix='uploads')
```

This function lists files stored in S3 storage:

**Parameters:**
- `folder_prefix`: The folder prefix to list files from (default: 'uploads')

**Example:**
```python
files = list_files('documents/2023')
# Returns: [{"key": "documents/2023/report.pdf", "size": 1024, "last_modified": "2023-01-15T12:30:45Z"}, ...]
```

**Example Usage:**

```
User: Can you list the files in the uploads folder?
Maria: Here are the files in the uploads folder:

1. quarterly_report_q1_2023.pdf (2.4 MB, uploaded on Jan 15, 2023)
2. meeting_minutes_feb_2023.docx (156 KB, uploaded on Feb 10, 2023)
3. sales_data_march_2023.csv (890 KB, uploaded on Apr 2, 2023)
4. product_images.zip (15.6 MB, uploaded on Mar 28, 2023)
```

### Download and Read Files

```python
def download_and_read_file(url, content_type)
```

This function downloads and extracts text from files:

**Parameters:**
- `url`: The URL of the file to download
- `content_type`: The MIME type of the file

**Example:**
```python
text = download_and_read_file("https://example.com/document.pdf", "application/pdf")
```

**Example Usage:**

```
User: [Uploads a PDF document]
Maria: I've processed the document you uploaded. Here's a summary of its contents:
[Summary of the document content]
```

### Send as PDF

```python
def send_as_pdf(text, chat_id, title, ts=None)
```

This function converts text to PDF and shares it:

**Parameters:**
- `text`: The text to convert to PDF
- `chat_id`: The chat ID to send the PDF to
- `title`: The title of the PDF
- `ts`: (Optional) Thread timestamp if sending to a thread

**Example:**
```python
send_as_pdf("# Report\n\nThis is a sample report.", "C12345", "Sample Report")
```

**Example Usage:**

```
User: Can you create a PDF summary of our meeting notes?
Maria: I've created a PDF summary of the meeting notes and attached it here.
[PDF file attachment]
```

## Document Analysis

Maria can analyze various document types to extract and process content:

### PDF Processing

Maria can extract text from PDF documents, including:

- Text content extraction
- Basic structure analysis
- Content summarization

**Example Usage:**

```
User: [Uploads a PDF report]
Maria: I've analyzed the PDF report you shared. The document is a 15-page financial report for Q1 2023. 
Key findings include:
- Revenue increased by 12% compared to Q4 2022
- Operating expenses decreased by 5%
- New product lines contributed 8% to overall revenue
Would you like me to extract any specific section?
```

### Word Document Processing

Maria can process Microsoft Word documents, including:

- Text extraction
- Format preservation
- Table and list recognition

**Example Usage:**

```
User: [Uploads a Word document]
Maria: I've processed the Word document you shared. It contains the project proposal with the following sections:
1. Executive Summary
2. Project Scope
3. Timeline
4. Budget
5. Resource Requirements
Would you like me to summarize any particular section?
```

### CSV Processing

Maria can analyze CSV files for data processing:

- Data extraction
- Basic statistical analysis
- Trend identification

**Example Usage:**

```
User: [Uploads a CSV file with sales data]
Maria: I've analyzed the sales data CSV. Here's what I found:
- Total sales: $1,245,678
- Highest performing product: Product X (32% of total sales)
- Lowest performing region: West (15% of total sales)
- Month-over-month growth: 8.5%
Would you like me to create a more detailed analysis?
```

## Implementation Details

### File Listing Implementation

The file listing functionality uses AWS S3:

```python
def list_files(folder_prefix='uploads'):
    """List files in S3 bucket with the given prefix."""
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=folder_prefix
        )
        
        if 'Contents' not in response:
            return []
        
        files = []
        for item in response['Contents']:
            files.append({
                'key': item['Key'],
                'size': item['Size'],
                'last_modified': item['LastModified'].isoformat()
            })
        
        return files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return []
```

### File Download and Processing

The file download and processing functionality handles various file types:

```python
def download_and_read_file(url, content_type):
    """Download and extract text from a file."""
    try:
        # Download file
        response = requests.get(url)
        file_content = response.content
        
        # Process based on content type
        if content_type == "application/pdf":
            return extract_text_from_pdf(file_content)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(file_content)
        elif content_type == "text/csv":
            return extract_text_from_csv(file_content)
        elif content_type.startswith("text/"):
            return file_content.decode('utf-8')
        else:
            return f"Unsupported file type: {content_type}"
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return f"Error processing file: {str(e)}"
```

### PDF Generation

The PDF generation functionality creates PDF documents from text:

```python
def send_as_pdf(text, chat_id, title, ts=None):
    """Convert text to PDF and share it."""
    try:
        # Create PDF
        pdf_file = f"/tmp/{title.replace(' ', '_')}.pdf"
        create_pdf_from_text(text, pdf_file, title)
        
        # Upload to Slack
        send_file_to_slack(pdf_file, chat_id, title, ts)
        
        return True
    except Exception as e:
        logger.error(f"Error creating PDF: {str(e)}")
        return False
```

## Document Extraction Functions

Various helper functions extract text from different document types:

```python
def extract_text_from_pdf(pdf_data):
    """Extract text from PDF data."""
    # Implementation using PyPDF2 or similar library
    
def extract_text_from_docx(docx_data):
    """Extract text from DOCX data."""
    # Implementation using python-docx or similar library
    
def extract_text_from_csv(csv_data):
    """Extract text from CSV data."""
    # Implementation using csv module or pandas
```

## Best Practices

When working with document processing:

- Provide clear file types for better processing
- Be specific about what information to extract
- Consider file size limitations
- Be aware of processing time for large documents
- Ensure proper permissions for file access

## Future Enhancements

Planned enhancements for document processing include:

- Enhanced OCR capabilities for scanned documents
- Improved table and chart extraction
- Document comparison functionality
- Template-based document generation
- Multi-language document support

---

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Information Retrieval](information-retrieval.md) | [Message Management →](message-management.md)