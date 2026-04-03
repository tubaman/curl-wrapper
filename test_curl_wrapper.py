import pytest
from unittest.mock import patch, MagicMock
import subprocess
import os
from curl_wrapper import get, post, Session, Response, CurlError, HTTPError, Timeout
from curl_wrapper.builder import build_curl_command, parse_response

class TestBuildCurlCommand:
    def test_basic_get(self):
        cmd = build_curl_command('http://example.com')
        assert cmd == ['curl', '-s', '-i', '-L', '-w', '\n__FINAL_URL__:%{url_effective}', 'http://example.com']
    
    def test_with_headers(self):
        cmd = build_curl_command('http://example.com', headers={'User-Agent': 'test'})
        assert '-H' in cmd and 'User-Agent: test' in cmd
    
    def test_with_json(self):
        cmd = build_curl_command('http://example.com', method='POST', json={'key': 'value'})
        assert '-d' in cmd and '{"key": "value"}' in cmd
    
    def test_with_auth(self):
        cmd = build_curl_command('http://example.com', auth=('user', 'pass'))
        assert '-u' in cmd and 'user:pass' in cmd
    
    def test_custom_curl_path(self):
        cmd = build_curl_command('http://example.com', curl_path='/custom/curl')
        assert cmd[0] == '/custom/curl'

    def test_with_method(self):
        cmd = build_curl_command('http://example.com', method='PUT')
        assert '-X' in cmd and cmd[cmd.index('-X') + 1] == 'PUT'

    def test_without_method(self):
        cmd = build_curl_command('http://example.com', data='key=value')
        assert '-X' not in cmd
        assert '-d' in cmd

class TestParseResponse:
    def test_parse_basic_response(self):
        output = b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html></html>'
        resp = parse_response(output, 'http://example.com')
        assert resp.status_code == 200
        assert resp.headers['Content-Type'] == 'text/html'
        assert resp.text == '<html></html>'
    
    def test_parse_redirect_response(self):
        output = b'HTTP/1.1 302 Found\r\nLocation: /redirect\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"result": "ok"}'
        resp = parse_response(output, 'http://example.com')
        assert resp.status_code == 200
        assert resp.headers['Content-Type'] == 'application/json'
        assert resp.json() == {'result': 'ok'}
        assert len(resp.history) == 1
        assert resp.history[0].status_code == 302
        assert resp.history[0].headers['Location'] == '/redirect'
    
    def test_parse_multiple_redirects(self):
        output = b'HTTP/1.1 301 Moved\r\nLocation: /first\r\n\r\nHTTP/1.1 302 Found\r\nLocation: /second\r\n\r\nHTTP/1.1 200 OK\r\n\r\nfinal'
        resp = parse_response(output, 'http://example.com')
        assert resp.status_code == 200
        assert len(resp.history) == 2
        assert resp.history[0].status_code == 301
        assert resp.history[1].status_code == 302
    
    def test_parse_no_redirects(self):
        output = b'HTTP/1.1 200 OK\r\n\r\nbody'
        resp = parse_response(output, 'http://example.com')
        assert resp.status_code == 200
        assert len(resp.history) == 0
    
    def test_parse_duplicate_headers(self):
        output = b'HTTP/1.1 200 OK\r\nSet-Cookie: a=1\r\nSet-Cookie: b=2\r\n\r\nbody'
        resp = parse_response(output, 'http://example.com')
        assert resp.headers.getall('Set-Cookie') == ['a=1', 'b=2']

    def test_parse_binary_data(self):
        # JPEG magic bytes followed by some data
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x02\x00\x00\x01\x00\x01\x00\x00'
        output = b'HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg_data
        resp = parse_response(output, 'http://example.com')
        assert resp.status_code == 200
        assert resp.content == jpeg_data
        assert resp.content[:4] == b'\xff\xd8\xff\xe0'

class TestResponse:
    def test_json_parsing(self):
        resp = Response(200, {}, '{"key": "value"}', 'http://example.com')
        assert resp.json() == {'key': 'value'}
    
    def test_raise_for_status_ok(self):
        resp = Response(200, {}, '', 'http://example.com')
        resp.raise_for_status()
    
    def test_raise_for_status_error(self):
        resp = Response(404, {}, '', 'http://example.com')
        with pytest.raises(HTTPError):
            resp.raise_for_status()
    
    def test_binary_content(self):
        binary_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        resp = Response(200, {}, binary_data, 'http://example.com')
        assert resp.content == binary_data
        assert isinstance(resp.content, bytes)
    
    def test_charset_from_content_type(self):
        body = 'café'.encode('iso-8859-1')
        resp = Response(200, {'content-type': 'text/html; charset=iso-8859-1'}, body, 'http://example.com')
        assert resp.text == 'café'

@patch('curl_wrapper.builder.subprocess.run')
class TestClient:
    def test_get_request(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        resp = get('http://example.com')
        assert resp.status_code == 200
    
    def test_post_request(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 201 Created\r\n\r\n{}')
        resp = post('http://example.com', json={'data': 'test'})
        assert resp.status_code == 201
    
    def test_timeout_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=28, stderr=b'timeout')
        with pytest.raises(Timeout):
            get('http://example.com', timeout=5)
    
    def test_curl_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr=b'error')
        with pytest.raises(CurlError):
            get('http://example.com')
    
    def test_allow_redirects_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}\n__FINAL_URL__:http://example.com/final')
        resp = get('http://example.com/redirect', allow_redirects=True)
        assert resp.url == 'http://example.com/final'
        assert '-L' in mock_run.call_args[0][0]
    
    def test_allow_redirects_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 302 Found\r\nLocation: /final\r\n\r\n\n__FINAL_URL__:http://example.com/redirect')
        resp = get('http://example.com/redirect', allow_redirects=False)
        assert resp.url == 'http://example.com/redirect'
        assert '-L' not in mock_run.call_args[0][0]
    
    def test_custom_curl_path(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        get('http://example.com', curl_path='/custom/curl')
        assert mock_run.call_args[0][0][0] == '/custom/curl'

@patch('curl_wrapper.builder.subprocess.run')
class TestSession:
    def test_session_headers(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        session = Session()
        session.headers['Authorization'] = 'Bearer token'
        session.get('http://example.com')
        assert any('Authorization: Bearer token' in str(call) for call in mock_run.call_args_list)
        session.close()
    
    def test_session_cookie_jar(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        session = Session()
        assert session.cookie_jar
        assert os.path.exists(session.cookie_jar)
        session.get('http://example.com')
        assert any(session.cookie_jar in str(call) for call in mock_run.call_args_list)
        session.close()
        assert not os.path.exists(session.cookie_jar)
    
    def test_session_cleanup_on_del(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        session = Session()
        cookie_jar_path = session.cookie_jar
        assert os.path.exists(cookie_jar_path)
        del session
        assert not os.path.exists(cookie_jar_path)
    
    def test_session_custom_curl_path(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        session = Session(curl_path='/custom/curl')
        session.get('http://example.com')
        assert mock_run.call_args[0][0][0] == '/custom/curl'
        session.close()

    def test_session_request_method(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b'HTTP/1.1 200 OK\r\n\r\n{}')
        session = Session()
        session.headers['X-Custom'] = 'test'
        response = session.request('GET', 'http://example.com')
        assert response.status_code == 200
        assert any('X-Custom: test' in str(call) for call in mock_run.call_args_list)
        session.close()
