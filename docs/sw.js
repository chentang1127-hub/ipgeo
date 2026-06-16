// Service Worker: proxy blocked Paddle domains through getipgeo.com
// cdn.paddle.com, sandbox-api.paddle.com, etc. are inaccessible from China

const PROXY_MAP = [
  { host: 'cdn.paddle.com',              proxy: '/paddle/' },
  { host: 'sandbox-cdn.paddle.com',      proxy: '/paddle-cdn/' },
  { host: 'sandbox-api.paddle.com',      proxy: '/paddle-api/' },
  { host: 'sandbox-checkout.paddle.com',  proxy: '/paddle-checkout/' },
  { host: 'api.paddle.com',              proxy: '/paddle-api/' },
  { host: 'checkout.paddle.com',         proxy: '/paddle-checkout/' },
];

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const map = PROXY_MAP.find(m => url.hostname === m.host);
  if (!map) return;

  const newUrl = event.request.url.replace(
    `https://${map.host}`,
    map.proxy.replace(/\/$/, '')
  );

  // Clone the request but with our proxied URL
  const init = {
    method: event.request.method,
    headers: event.request.headers,
    body: event.request.body,
    mode: 'same-origin',
    credentials: 'omit',
    redirect: 'follow',
  };

  // Can't clone body on GET/HEAD
  if (event.request.method === 'GET' || event.request.method === 'HEAD') {
    delete init.body;
  }

  event.respondWith(fetch(newUrl, init));
});
