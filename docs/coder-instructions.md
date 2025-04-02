# Instructions for Converting HTML Documentation to GitHub Markdown

This document provides specific step-by-step instructions for converting the Maria AI Assistant HTML documentation to GitHub-friendly Markdown format.

## Prerequisites

Before starting the conversion, ensure you have:

1. Access to the source HTML file (`docs/maria-documentation.html`)
2. Basic knowledge of HTML and Markdown
3. Git installed for testing on GitHub
4. A text editor or IDE (VS Code recommended)

## Step-by-Step Conversion Process

### Step 1: Set Up the Directory Structure

Create the following directories if they don't already exist:

```bash
mkdir -p docs/functionality
mkdir -p docs/functions
```

### Step 2: Initial Conversion

You have two options for the initial conversion:

#### Option A: Use Pandoc (Recommended)

If you have Pandoc installed:

```bash
pandoc -f html -t gfm docs/maria-documentation.html -o docs/temp.md
```

This will create a single Markdown file with the converted content.

#### Option B: Manual Conversion

If you prefer manual conversion or don't have Pandoc:

1. Open `docs/maria-documentation.html` in your editor
2. Create a new file `docs/temp.md`
3. Copy and convert content section by section following the conversion rules in [conversion-guide.md](conversion-guide.md)

### Step 3: Create the Main README.md

1. Use the provided [README.md](README.md) as a template
2. Update it with any project-specific information
3. Ensure all links in the table of contents point to the correct files

### Step 4: Split Content into Separate Files

For each section in the documentation:

1. Identify the corresponding section in `temp.md`
2. Copy the content to the appropriate file based on the file structure
3. Add navigation links at the top and bottom of each file
4. Update internal links to point to the correct files

Use the example files as templates:
- [system-architecture.md](system-architecture.md)
- [functions/lambda-function.md](functions/lambda-function.md)
- [functionality/communication.md](functionality/communication.md)

### Step 5: Create Index Files for Subdirectories

Create index files for each subdirectory:

1. Use [functions/README.md](functions/README.md) and [functionality/README.md](functionality/README.md) as templates
2. Update with section-specific content
3. Ensure all links point to the correct files

### Step 6: Update Internal Links

For each file:

1. Update links to sections within the same file to use anchor links: `[Text](#heading-id)`
2. Update links to other files to use relative paths: `[Text](./path/to/file.md)`
3. Update links to sections in other files to combine both: `[Text](./path/to/file.md#heading-id)`

### Step 7: Format Code Blocks

For all code blocks:

1. Use triple backticks with language identifiers
2. Ensure proper indentation
3. Remove any HTML entities or escape characters

Example:

````markdown
```python
def lambda_handler(event, context):
    # Process Slack event
```
````

### Step 8: Format Tables

For all tables:

1. Use Markdown table syntax
2. Align columns for readability
3. Use headers appropriately

Example:

```markdown
| Function | Description | Parameters |
|----------|-------------|------------|
| `function_name` | What it does | `param1`, `param2` |
```

### Step 9: Add Navigation Links

For each file:

1. Add navigation links at the top:
   ```markdown
   [← Back to Main](../README.md) | [Next Section →](next-section.md)
   ```

2. Add navigation links at the bottom:
   ```markdown
   ---
   
   [← Back to Main](../README.md) | [Next Section →](next-section.md)
   ```

### Step 10: Test on GitHub

1. Commit and push your changes to a test branch
2. View the documentation on GitHub
3. Test all links and navigation
4. Check formatting of code blocks, tables, and other elements
5. Verify that images (if any) display correctly

### Step 11: Refine and Polish

1. Fix any issues identified during testing
2. Improve formatting where needed
3. Add any missing content
4. Ensure consistent styling across all files

### Step 12: Final Review

1. Review all files for consistency
2. Check for any remaining HTML tags or formatting issues
3. Verify that all links work correctly
4. Ensure the documentation is complete and accurate

## Conversion Rules Quick Reference

| HTML Element | Markdown Equivalent |
|--------------|---------------------|
| `<h1>` | `# Heading` |
| `<h2>` | `## Heading` |
| `<h3>` | `### Heading` |
| `<h4>` | `#### Heading` |
| `<p>` | Plain text |
| `<ul><li>` | `- Item` or `* Item` |
| `<ol><li>` | `1. Item` |
| `<pre><code>` | ````language` |
| `<code>` | `` |
| `<a href="...">` | `[Text](...)` |
| `<strong>` | `**bold**` |
| `<em>` | `*italic*` |
| `<blockquote>` | `> Quote` |

## GitHub-Specific Features

Consider adding these GitHub-specific features:

1. **Collapsible Sections**:
   ```markdown
   <details>
   <summary>Click to expand</summary>
   
   Content here
   </details>
   ```

2. **Task Lists**:
   ```markdown
   - [x] Completed task
   - [ ] Incomplete task
   ```

3. **Emoji**:
   ```markdown
   :rocket: :warning: :information_source:
   ```

## Reference Materials

Refer to these documents for more detailed guidance:

- [github-conversion-instructions.md](github-conversion-instructions.md): Detailed conversion instructions
- [conversion-guide.md](conversion-guide.md): Comprehensive conversion guide
- [conversion-summary.md](conversion-summary.md): Overview of the conversion approach

## Example Files

Use these files as templates:

- [README.md](README.md): Main index template
- [system-architecture.md](system-architecture.md): Section file template
- [functions/README.md](functions/README.md): Subdirectory index template
- [functions/lambda-function.md](functions/lambda-function.md): Function description template
- [functionality/README.md](functionality/README.md): Another subdirectory index template
- [functionality/communication.md](functionality/communication.md): Functionality description template

## Final Notes

- Keep file names lowercase and use hyphens instead of spaces
- Use relative links rather than absolute links
- Be consistent with formatting across all files
- Test thoroughly on GitHub before finalizing
- Consider adding a `.gitattributes` file to ensure line endings are consistent

Good luck with the conversion! The result will be a well-structured, GitHub-friendly documentation set that is easy to navigate and maintain.