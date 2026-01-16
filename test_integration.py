import pytest
from curl_wrapper import get, post, Session

class TestHttpBin:
    def test_get_request(self):
        resp = get('http://httpbin.org/get')
        assert resp.status_code == 200
        data = resp.json()
        assert data['url'] == 'http://httpbin.org/get'
    
    def test_post_json(self):
        resp = post('http://httpbin.org/post', json={'key': 'value'})
        assert resp.status_code == 200
        data = resp.json()
        assert data['json'] == {'key': 'value'}
    
    def test_headers(self):
        resp = get('http://httpbin.org/headers', headers={'X-Custom': 'test'})
        assert resp.status_code == 200
        data = resp.json()
        assert data['headers']['X-Custom'] == 'test'
    
    def test_basic_auth(self):
        resp = get('http://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
        assert resp.status_code == 200
        data = resp.json()
        assert data['authenticated'] == True
    
    def test_redirect_follow(self):
        resp = get('http://httpbin.org/redirect/2', allow_redirects=True)
        assert resp.status_code == 200
        assert resp.url == 'http://httpbin.org/get'
    
    def test_redirect_no_follow(self):
        resp = get('http://httpbin.org/redirect/1', allow_redirects=False)
        assert resp.status_code == 302
        assert resp.url == 'http://httpbin.org/redirect/1'
    
    def test_session_cookies(self):
        session = Session()
        resp = session.get('http://httpbin.org/cookies/set?session=test')
        assert resp.status_code == 200
        
        # Verify cookie is in the jar file
        with open(session.cookie_jar, 'r') as f:
            cookie_data = f.read()
            assert 'session' in cookie_data
            assert 'test' in cookie_data
        
        resp = session.get('http://httpbin.org/cookies')
        data = resp.json()
        assert data['cookies']['session'] == 'test'
        session.close()
    
    def test_session_manual_cookies(self):
        session = Session()
        
        # Manually add cookie to jar file
        with open(session.cookie_jar, 'w') as f:
            f.write('# Netscape HTTP Cookie File\n')
            f.write('httpbin.org\tFALSE\t/\tFALSE\t0\tmanual\tvalue123\n')
        
        resp = session.get('http://httpbin.org/cookies')
        data = resp.json()
        assert data['cookies']['manual'] == 'value123'
        session.close()
