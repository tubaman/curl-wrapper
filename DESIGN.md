# Design: Python HTTP Client Library (curl wrapper)

## Overview
A lightweight Python HTTP client that wraps the `curl` command-line tool, providing a Pythonic interface while leveraging curl's battle-tested HTTP implementation.

## Core Architecture

### 1. Request Builder
- Translates Python method calls into curl command arguments
- Handles URL, headers, body, method, timeout, auth
- Returns `subprocess` result with parsed response

### 2. Response Object
- Wraps curl output (status code, headers, body)
- Parses headers from curl's `-i` flag or `-D` header dump
- Provides `.text`, `.json()`, `.status_code`, `.headers` properties

### 3. API Surface
```python
# Simple interface
response = curl.get(url, headers={}, params={})
response = curl.post(url, data={}, json={}, headers={})
response = curl.put/patch/delete(...)

# Session support (reuses cookies, connection settings)
session = curl.Session()
session.get(url)
```

## Implementation Strategy

### Command Construction
- Build curl args list: `['curl', '-s', '-i', '-X', 'POST', ...]`
- Map Python kwargs to curl flags:
  - `headers` → `-H "Key: Value"`
  - `json` → `-H "Content-Type: application/json"` + `-d` payload
  - `data` → `-d` or `--data-urlencode`
  - `timeout` → `--max-time`
  - `auth` → `-u user:pass`
  - `verify=False` → `-k`

### Response Parsing
- Use `-i` to include headers in output
- Split on `\r\n\r\n` to separate headers from body
- Parse status line and header key-values
- Handle redirects (curl follows by default with `-L`)

### Error Handling
- Check `subprocess` return code
- Raise exceptions for curl errors (connection failed, timeout)
- Expose HTTP errors (4xx, 5xx) via response object

## Key Design Decisions

**Why shell out?**
- Avoids reimplementing HTTP/2, TLS, compression
- Curl handles edge cases (redirects, encodings, protocols)
- Smaller dependency footprint

**Trade-offs:**
- Subprocess overhead (~5-10ms per request)
- Less control over low-level socket behavior
- Requires curl installed on system

**Security:**
- Use `subprocess.run()` with list args (no shell injection)
- Validate/escape user input in URLs and headers
- Default to certificate verification

## File Structure
```
curl_wrapper/
├── __init__.py       # Public API exports
├── client.py         # get/post/etc functions
├── session.py        # Session class
├── response.py       # Response class
├── builder.py        # Curl command builder
└── exceptions.py     # Custom exceptions
```

## Minimal Feature Set
- HTTP methods: GET, POST, PUT, PATCH, DELETE, HEAD
- Headers, query params, request body (form/json)
- Basic auth
- Timeout control
- Response: status, headers, body (text/json)
- Connection/HTTP errors as exceptions
