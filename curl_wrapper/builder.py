import subprocess
import json as json_lib
from urllib.parse import urlencode
from .response import Response
from .exceptions import CurlError, Timeout

def build_curl_command(method, url, headers=None, params=None, data=None, json=None, 
                       auth=None, timeout=None, verify=True, cookie_jar=None, allow_redirects=True, curl_path='curl'):
    cmd = [curl_path, '-s', '-i']
    
    if method != 'GET':
        cmd.extend(['-X', method])
    
    if allow_redirects:
        cmd.append('-L')
    
    cmd.extend(['-w', '\n__FINAL_URL__:%{url_effective}'])
    
    if params:
        url = url + ('&' if '?' in url else '?') + urlencode(params)
    
    if headers:
        for key, value in headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
    
    if cookie_jar:
        cmd.extend(['-b', cookie_jar, '-c', cookie_jar])
    
    if json is not None:
        cmd.extend(['-H', 'Content-Type: application/json'])
        cmd.extend(['-d', json_lib.dumps(json)])
    elif data:
        if isinstance(data, dict):
            for key, value in data.items():
                cmd.extend(['--data-urlencode', f'{key}={value}'])
        else:
            cmd.extend(['-d', data])
    
    if auth:
        cmd.extend(['-u', f'{auth[0]}:{auth[1]}'])
    
    if timeout:
        cmd.extend(['--max-time', str(timeout)])
    
    if not verify:
        cmd.append('-k')
    
    cmd.append(url)
    return cmd

def parse_headers(header_section):
    header_str = header_section.decode('utf-8', errors='replace')
    lines = header_str.split('\n')
    status_code = int(lines[0].split()[1])
    
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    
    return status_code, headers

def parse_response(output, request_url):
    output_str = output.decode('utf-8', errors='replace')
    
    if '__FINAL_URL__:' in output_str:
        parts = output_str.rsplit('__FINAL_URL__:', 1)
        response_data = parts[0].encode('utf-8')
        final_url = parts[1].strip()
    else:
        response_data = output
        final_url = request_url
    
    # Split by double newline to separate headers from body
    parts = response_data.split(b'\r\n\r\n')
    if len(parts) < 2:
        parts = response_data.split(b'\n\n')
    
    # Parse all HTTP responses (redirects + final)
    history = []
    header_sections = []
    body_start_idx = 0
    
    for i, part in enumerate(parts[:-1]):
        if part.startswith(b'HTTP/'):
            header_sections.append(part)
            body_start_idx = i + 1
    
    if not header_sections:
        header_sections = [parts[0]]
        body_start_idx = 1
    
    # Parse redirect history
    for header_section in header_sections[:-1]:
        status_code, headers = parse_headers(header_section)
        redirect_url = headers.get('Location', '')
        history.append(Response(status_code, headers, b'', redirect_url))
    
    # Parse final response
    status_code, headers = parse_headers(header_sections[-1])
    body = b'\n\n'.join(parts[body_start_idx:]) if body_start_idx < len(parts) else b''
    
    return Response(status_code, headers, body, final_url, history)

def execute_request(method, url, **kwargs):
    cmd = build_curl_command(method, url, **kwargs)
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        if result.returncode == 28:
            raise Timeout(f"Request timed out")
        raise CurlError(f"Curl failed with code {result.returncode}: {result.stderr.decode()}")
    
    return parse_response(result.stdout, url)
