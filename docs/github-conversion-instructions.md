# GitHub Documentation Conversion Instructions

This document provides detailed instructions for converting the HTML documentation to a GitHub-friendly format using multiple Markdown files.

## Step 1: Set Up the File Structure

Create the following directory structure:

```
docs/
├── README.md
├── system-architecture.md
├── functionality/
│   ├── README.md
│   ├── communication.md
│   ├── erp-integration.md
│   ├── information-retrieval.md
│   ├── document-processing.md
│   ├── message-management.md
│   └── user-management.md
├── functions/
│   ├── README.md
│   ├── lambda-function.md
│   ├── conversation-management.md
│   ├── storage-operations.md
│   ├── slack-integration.md
│   ├── media-processing.md
│   ├── erp-integrations.md
│   ├── external-services.md
│   ├── web-and-search.md
│   └── document-management.md
├── routing-configuration.md
├── prompt-configuration.md
├── invocation-flow.md
└── configuration.md
```

## Step 2: HTML to Markdown Conversion

### Conversion Guidelines

When converting HTML to Markdown, follow these guidelines:

1. **Headings**:
   - `<h1>` → `# Heading`
   - `<h2>` → `## Heading`
   - `<h3>` → `### Heading`
   - `<h4>` → `#### Heading`

2. **Lists**:
   - Unordered lists (`<ul><li>`) → `- Item` or `* Item`
   - Ordered lists (`<ol><li>`) → `1. Item`

3. **Code Blocks**:
   - `<pre><code>` → ````python` (with appropriate language identifier)
   - Inline `<code>` → `` (backticks)

4. **Links**:
   - `<a href="...">Text</a>` → `[Text](...)` 
   - For internal links to other markdown files: `[Text](./path/to/file.md)`
   - For section links within the same file: `[Text](#section-name)`

5. **Emphasis**:
   - `<strong>` → `**bold**`
   - `<em>` → `*italic*`

6. **Tables**:
   ```
   | Header 1 | Header 2 |
   |----------|----------|
   | Cell 1   | Cell 2   |
   ```

7. **Images** (if any):
   - `<img src="..." alt="...">` → `![Alt text](path/to/image)`

### Automated Conversion Tools

You can use these tools to help with the initial conversion:

- **Pandoc**: `pandoc -f html -t gfm maria-documentation.html -o temp.md`
- **Online converters**: Various online HTML to Markdown converters
- **VS Code extensions**: Markdown All in One, Paste Image, etc.

After automated conversion, you'll need to manually clean up and organize the content.

## Step 3: Create the Main README.md

The main README.md should include:

```markdown
# Maria: AI Executive Assistant Documentation

Maria is an AI executive assistant designed to facilitate communication and task execution within a Slack workspace. Built on Claude 3.7 Sonnet, Maria presents herself as a friendly Canadian lady working at Cerenyi AI. The system integrates with various services including Slack, ERPNext, Amazon, Google APIs, and more to provide a wide range of functionalities.

## Table of Contents

- [System Architecture](system-architecture.md)
- Functionality
  - [Overview](functionality/README.md)
  - [Communication](functionality/communication.md)
  - [ERP Integration](functionality/erp-integration.md)
  - [Information Retrieval](functionality/information-retrieval.md)
  - [Document Processing](functionality/document-processing.md)
  - [Message Management](functionality/message-management.md)
  - [User Management](functionality/user-management.md)
- Function Descriptions
  - [Overview](functions/README.md)
  - [Lambda Function](functions/lambda-function.md)
  - [Conversation Management](functions/conversation-management.md)
  - [Storage Operations](functions/storage-operations.md)
  - [Slack Integration](functions/slack-integration.md)
  - [Media Processing](functions/media-processing.md)
  - [ERP Integrations](functions/erp-integrations.md)
  - [External Services](functions/external-services.md)
  - [Web and Search](functions/web-and-search.md)
  - [Document Management](functions/document-management.md)
- [Routing Configuration](routing-configuration.md)
- [Prompt Configuration](prompt-configuration.md)
- [Invocation Flow](invocation-flow.md)
- [Configuration](configuration.md)
```

## Step 4: Extract and Convert Content by Section

For each section in the HTML document:

1. Extract the relevant content
2. Convert to Markdown following the guidelines above
3. Save to the appropriate file in the structure
4. Add navigation links at the top and bottom of each file

### Example Navigation Links

Add these at the top of each Markdown file:

```markdown
[← Back to Main](../README.md) | [System Architecture →](system-architecture.md)
```

## Step 5: Update Internal Links

After creating all the files, update all internal links to point to the correct Markdown files:

1. Links to sections within the same file should use anchor links: `[Text](#heading-id)`
2. Links to other files should use relative paths: `[Text](./path/to/file.md)`
3. Links to sections in other files should combine both: `[Text](./path/to/file.md#heading-id)`

Note: GitHub automatically generates heading IDs by converting the heading text to lowercase and replacing spaces with hyphens.

## Step 6: GitHub-Specific Enhancements

### Code Syntax Highlighting

Use language identifiers with code blocks:

````markdown
```python
def lambda_handler(event, context):
    # Process Slack event
```
````

### Collapsible Sections

For lengthy sections:

```markdown
<details>
<summary>Click to expand detailed function list</summary>

- Function 1
- Function 2
- Function 3
</details>
```

### Tables

For better readability:

```markdown
| Function | Description | Parameters |
|----------|-------------|------------|
| `function_name` | What it does | `param1`, `param2` |
```

## Step 7: Testing

After conversion:

1. Push the changes to a test branch
2. Verify all links work correctly
3. Check formatting on different devices
4. Ensure code blocks render with proper syntax highlighting

## Additional Tips

1. Use relative links rather than absolute links for better portability
2. Keep file names lowercase and use hyphens instead of spaces
3. Add a `.gitattributes` file to ensure line endings are consistent
4. Consider adding a GitHub Actions workflow for validating links
5. Add a license file if appropriate

## Example Conversion

### HTML:
```html
<h3 id="lambda-function">Lambda Function (Main Entry Point)</h3>
<p>The <code>lambda_handler</code> in <code>lambda_function.py</code> is the main entry point that:</p>
<ol>
    <li>Parses incoming Slack events</li>
    <li>Retrieves message history</li>
    <li>Processes any attached files or media</li>
    <li>Routes the message to the appropriate handler</li>
    <li>Generates and sends responses</li>
</ol>
```

### Markdown:
```markdown
## Lambda Function (Main Entry Point)

The `lambda_handler` in `lambda_function.py` is the main entry point that:

1. Parses incoming Slack events
2. Retrieves message history
3. Processes any attached files or media
4. Routes the message to the appropriate handler
5. Generates and sends responses