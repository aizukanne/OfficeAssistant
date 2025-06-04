# Document Management

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Web and Search](web-and-search.md)

The document management functions in `lambda_function.py` provide capabilities for handling various document formats, converting content to PDF, and managing files in storage.

## Overview

The document management functions enable Maria to:

- Convert text to PDF documents
- List files in storage
- Download and read files from various sources
- Process different document formats
- Share documents with users

## Send as PDF

```python
def send_as_pdf(text, chat_id, title, ts=None)
```

This function converts text to PDF and shares it:

**Parameters:**
- `text`: The text to convert to PDF
- `chat_id`: The chat ID to send the PDF to
- `title`: The title of the PDF
- `ts`: (Optional) Thread timestamp if sending to a thread

**Returns:**
- True if successful, False otherwise

**Example:**
```python
# Convert text to PDF and send
success = send_as_pdf("# Report\n\nThis is a sample report.", "C12345", "Sample Report")
```

**Example Usage:**

```
User: Can you create a PDF summary of our meeting notes?
Maria: I've created a PDF summary of the meeting notes and attached it here.
[PDF file attachment]
```

## List Files

```python
def list_files(folder_prefix='uploads')
```

This function lists files in S3 storage:

**Parameters:**
- `folder_prefix`: (Optional) The folder prefix to list files from (default: 'uploads')

**Returns:**
- A list of files in the specified folder

**Example:**
```python
# List files in the uploads folder
files = list_files()

# List files in a specific folder
files = list_files('documents/2023')
```

**Example Usage:**

```
User: What files do we have in the uploads folder?
Maria: Here are the files in the uploads folder:

1. quarterly_report_q1_2023.pdf (2.4 MB, uploaded on Jan 15, 2023)
2. meeting_minutes_feb_2023.docx (156 KB, uploaded on Feb 10, 2023)
3. sales_data_march_2023.csv (890 KB, uploaded on Apr 2, 2023)
4. product_images.zip (15.6 MB, uploaded on Mar 28, 2023)
```

## Download and Read File

```python
def download_and_read_file(url, content_type)
```

This function downloads and extracts text from a file:

**Parameters:**
- `url`: The URL of the file to download
- `content_type`: The MIME type of the file

**Returns:**
- The extracted text from the file

**Example:**
```python
# Download and read a PDF file
text = download_and_read_file("https://example.com/document.pdf", "application/pdf")

# Download and read a Word document
text = download_and_read_file("https://example.com/document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
```

**Example Usage:**

```
User: [Uploads a PDF document]
Maria: I've processed the document you uploaded. Here's a summary of its contents:
[Summary of the document content]
```

## Implementation Details

### Send as PDF Implementation

```python
def send_as_pdf(text, chat_id, title, ts=None):
    """Convert text to PDF and share it."""
    try:
        # Create a temporary file
        pdf_file = f"/tmp/{title.replace(' ', '_')}.pdf"
        
        # Convert text to PDF
        create_pdf_from_text(text, pdf_file, title)
        
        # Upload to Slack
        send_file_to_slack(pdf_file, chat_id, title, ts)
        
        # Clean up
        os.remove(pdf_file)
        
        return True
    except Exception as e:
        logger.error(f"Error in send_as_pdf: {str(e)}")
        return False
```

### Create PDF from Text

```python
def create_pdf_from_text(text, output_file, title):
    """Create a PDF document from text."""
    try:
        # Create a PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']
        
        # Convert markdown to HTML
        html = markdown.markdown(text)
        
        # Parse HTML and create PDF elements
        soup = BeautifulSoup(html, 'html.parser')
        elements = []
        
        # Add title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        # Process HTML elements
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol']):
            if element.name.startswith('h'):
                # Heading
                level = int(element.name[1])
                style = styles[f'Heading{level}']
                elements.append(Paragraph(element.text, style))
            elif element.name == 'p':
                # Paragraph
                elements.append(Paragraph(element.text, normal_style))
            elif element.name in ['ul', 'ol']:
                # List
                items = []
                for li in element.find_all('li'):
                    items.append(li.text)
                
                if element.name == 'ul':
                    # Unordered list
                    list_style = ListStyle(
                        name='unordered',
                        bulletType='bullet',
                        bulletFontName='Helvetica',
                        bulletFontSize=10,
                        bulletIndent=0,
                        leftIndent=20
                    )
                else:
                    # Ordered list
                    list_style = ListStyle(
                        name='ordered',
                        bulletType='1',
                        bulletFontName='Helvetica',
                        bulletFontSize=10,
                        bulletIndent=0,
                        leftIndent=20
                    )
                
                pdf_list = ListFlowable(
                    [Paragraph(item, normal_style) for item in items],
                    style=list_style
                )
                elements.append(pdf_list)
            
            # Add spacing
            elements.append(Spacer(1, 6))
        
        # Build the PDF
        doc.build(elements)
        
        return True
    except Exception as e:
        logger.error(f"Error in create_pdf_from_text: {str(e)}")
        return False
```

### List Files Implementation

```python
def list_files(folder_prefix='uploads'):
    """List files in S3 storage."""
    try:
        # List objects in the S3 bucket
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=folder_prefix
        )
        
        # Check if there are any objects
        if 'Contents' not in response:
            return []
        
        # Format the file list
        files = []
        for item in response['Contents']:
            # Skip folders
            if item['Key'].endswith('/'):
                continue
            
            # Add file info
            files.append({
                'key': item['Key'],
                'size': item['Size'],
                'last_modified': item['LastModified'].isoformat()
            })
        
        return files
    except Exception as e:
        logger.error(f"Error in list_files: {str(e)}")
        return []
```

### Download and Read File Implementation

```python
def download_and_read_file(url, content_type):
    """Download and extract text from a file."""
    try:
        # Download the file
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Error downloading file: {response.status_code}")
            return f"Error downloading file: HTTP {response.status_code}"
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        # Extract text based on content type
        if content_type == "application/pdf":
            text = extract_text_from_pdf(temp_file_path)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx(temp_file_path)
        elif content_type == "text/csv":
            text = extract_text_from_csv(temp_file_path)
        elif content_type.startswith("text/"):
            text = response.text
        else:
            text = f"Unsupported file type: {content_type}"
        
        # Clean up
        os.remove(temp_file_path)
        
        return text
    except Exception as e:
        logger.error(f"Error in download_and_read_file: {str(e)}")
        return f"Error processing file: {str(e)}"
```

## Document Extraction Functions

Various helper functions extract text from different document types:

```python
def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        text = ""
        with open(file_path, "rb") as file:
            # Use PyPDF2 to extract text
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from a Word document."""
    try:
        # Use python-docx to extract text
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return f"Error extracting text from DOCX: {str(e)}"

def extract_text_from_csv(file_path):
    """Extract text from a CSV file."""
    try:
        # Read CSV file
        with open(file_path, "r") as file:
            reader = csv.reader(file)
            rows = list(reader)
        
        # Format as text
        text = ""
        for row in rows:
            text += ", ".join(row) + "\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from CSV: {str(e)}")
        return f"Error extracting text from CSV: {str(e)}"
```

## Document Processing Workflow

The typical document processing workflow follows these steps:

1. **Receive Document**: Receive a document from Slack or other sources
2. **Identify Type**: Determine the document type (PDF, Word, CSV, etc.)
3. **Extract Content**: Extract text and structure from the document
4. **Process Content**: Analyze, summarize, or format the content
5. **Generate Response**: Create a response based on the document content
6. **Deliver Result**: Send the result back to the user

## Best Practices

When working with document management:

- Handle large files efficiently
- Support common document formats
- Implement proper error handling
- Consider format compatibility
- Optimize for performance
- Clean up temporary files
- Respect privacy and data protection
- Integrate with [Privacy Detection](privacy-detection.md) for PII scanning in documents

## Future Enhancements

Planned enhancements for document management include:

- Enhanced PDF generation with better formatting
- Support for additional document formats
- Improved text extraction from complex documents
- Document comparison capabilities
- Template-based document generation
- Advanced document analysis

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Web and Search](web-and-search.md)