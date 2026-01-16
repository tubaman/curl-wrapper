# curl-wrapper

A lightweight Python HTTP client that wraps curl, providing a requests-like interface while leveraging curl's battle-tested HTTP implementation.

## Install

```bash
pip install curl-wrapper
```

## Developing

In a virtualenv, install the dev dependencies: `pip install -e .[dev]`.
Then to run the tests: `pytest`.

Then to build:

```bash
pip install build
python -m build
```

## Usage

```python
import curl_wrapper as curl

# Simple GET request
response = curl.get('https://api.example.com/data')
print(response.status_code)
print(response.json())

# POST with JSON
response = curl.post('https://api.example.com/users', 
                     json={'name': 'Alice'})

# Custom headers
response = curl.get('https://api.example.com/data',
                    headers={'Authorization': 'Bearer token'})

# Session support
session = curl.Session()
session.get('https://api.example.com/login')
session.post('https://api.example.com/data')
```

## Features

- HTTP methods: GET, POST, PUT, PATCH, DELETE, HEAD
- JSON and form data support
- Custom headers and query parameters
- Basic authentication
- Timeout control
- Session management (cookies, connection reuse)
- Response parsing (status, headers, body)

## Why curl?

- Avoids reimplementing HTTP/2, TLS, and compression
- Handles edge cases like redirects and encodings
- Smaller dependency footprint
- Battle-tested reliability
