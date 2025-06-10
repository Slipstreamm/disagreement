# Agents 
- There are no nested `AGENTS.md` files; this is the only one in the project.
- Tools to use for testing: `pyright`, `pylint`, `pytest`, `black`

- You have a Python script `tavilytool.py` in the project root that you can use to search the web.

# Tavily API Script Usage Instructions

## Basic Usage
Search for information using simple queries:
```bash
python tavilytool.py "your search query"
```

## Examples
```bash
python tavilytool.py "latest AI development 2024"
python tavilytool.py "how to make chocolate chip cookies"
python tavilytool.py "current weather in New York"
python tavilytool.py "best programming practices Python"
```

## Advanced Options

### Search Depth
- **Basic search**: `python tavilytool.py "query"` (default)
- **Advanced search**: `python tavilytool.py "query" --depth advanced`

### Control Results
- **Limit results**: `python tavilytool.py "query" --max-results 3`
- **Include images**: `python tavilytool.py "query" --include-images`
- **Skip AI answer**: `python tavilytool.py "query" --no-answer`

### Domain Filtering
- **Include specific domains**: `python tavilytool.py "query" --include-domains reddit.com stackoverflow.com`
- **Exclude domains**: `python tavilytool.py "query" --exclude-domains wikipedia.org`

### Output Format
- **Formatted output**: `python tavilytool.py "query"` (default - human readable)
- **Raw JSON**: `python tavilytool.py "query" --raw` (for programmatic processing)

## Output Structure
The default formatted output includes:
- 🤖 **AI Answer**: Direct answer to your query
- 🔍 **Search Results**: Titles, URLs, and content snippets
- 🖼️ **Images**: Relevant images (when `--include-images` is used)

## Command Combinations
```bash
# Advanced search with images, limited results
python tavilytool.py "machine learning tutorials" --depth advanced --include-images --max-results 3

# Search specific sites only, raw output
python tavilytool.py "Python best practices" --include-domains github.com stackoverflow.com --raw

# Quick search without AI answer
python tavilytool.py "today's news" --no-answer --max-results 5
```

## Tips
- Always quote your search queries to handle spaces and special characters
- Use `--max-results` to control response length and API usage
- Use `--raw` when you need to parse results programmatically
- Combine options as needed for specific use cases
