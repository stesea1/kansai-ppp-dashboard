"""Polite read-only fetcher: robots.txt check, >=3s per-host delay, on-disk cache, identifying UA. GET only."""
import signal, hashlib, os, time, json, urllib.robotparser, urllib.parse, datetime as dt
import requests
UA = 'kansai-ppp-dashboard-research/0.3 (+https://github.com/stesea1/kansai-ppp-dashboard; read-only, low rate)'
CACHE = '/workspace/ppp-dashboard/raw/signals/cache/'
LOG = '/workspace/ppp-dashboard/raw/signals/fetch_log.jsonl'
DELAY = 3.0
_last, _robots = {}, {}
def allowed(url):
    p = urllib.parse.urlparse(url); base = f'{p.scheme}://{p.netloc}'
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            t0 = time.time(); r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=(10, 15), stream=True); buf = b''
            for ch in r.iter_content(65536):
                buf += ch
                if time.time() - t0 > 30: raise TimeoutError('robots > 30s')
            if r.status_code == 200 and 'text/plain' in r.headers.get('content-type', ''): rp.parse(buf.decode('utf-8', 'ignore').splitlines())
            else: rp.parse([])  # no robots.txt -> allowed
        except Exception: rp.parse([])
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)
def get(url, refresh=False, binary=False):
    """returns (text or bytes, final_url, status) ; cached by URL"""
    key = hashlib.sha1(url.encode()).hexdigest(); fn = CACHE + key
    if os.path.exists(fn) and not refresh:
        meta = json.load(open(fn + '.json')); data = open(fn, 'rb').read()
        return (data if binary else data.decode(meta.get('enc') or 'utf-8', 'ignore')), meta['final'], meta['status']
    if url.startswith('http://'):
        # outbound port 80 is blocked from this network; Japanese gov sites serve the same page over https
        alt = 'https://' + url[7:]
        res = get(alt, refresh=refresh, binary=binary)
        if res[0] is not None:
            return res
    if not allowed(url):
        open(LOG, 'a').write(json.dumps({'url': url, 'robots': 'disallow', 't': str(dt.datetime.now())}) + '\n'); return None, url, 'robots'
    host = urllib.parse.urlparse(url).netloc
    w = DELAY - (time.time() - _last.get(host, 0))
    if w > 0: time.sleep(w)
    def _alarm(*a): raise TimeoutError('hard wall 60s')
    signal.signal(signal.SIGALRM, _alarm); signal.alarm(60)  # hard wall-clock cap (a stalled TLS/proxy read can outlive requests' timeouts)
    try:
        t0 = time.time(); r = requests.get(url, headers={'User-Agent': UA}, timeout=(10, 20), stream=True); buf = b''
        for ch in r.iter_content(65536):
            buf += ch
            if time.time() - t0 > 45: raise TimeoutError('total read > 45s')
        r._content = buf; _last[host] = time.time(); signal.alarm(0)
    except Exception as e:
        signal.alarm(0); _last[host] = time.time(); open(LOG, 'a').write(json.dumps({'url': url, 'err': str(e)[:200]}) + '\n'); return None, url, 'err'
    enc = r.encoding if r.encoding and r.encoding.lower() not in ('iso-8859-1',) else r.apparent_encoding
    open(fn, 'wb').write(r.content); json.dump({'url': url, 'final': r.url, 'status': r.status_code, 'enc': enc, 't': str(dt.datetime.now())}, open(fn + '.json', 'w'))
    open(LOG, 'a').write(json.dumps({'url': url, 'status': r.status_code, 't': str(dt.datetime.now())}) + '\n')
    return (r.content if binary else r.content.decode(enc or 'utf-8', 'ignore')), r.url, r.status_code
