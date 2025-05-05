const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  console.log('Setting up proxy middleware for API requests');
  
  // Proxy all /api requests to backend server
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      pathRewrite: {
        '^/api': '/api',  // keep '/api' prefix when forwarding
      },
      onProxyReq: (proxyReq, req) => {
        // Log request details
        console.log(`Proxying ${req.method} ${req.path} to ${proxyReq.path}`);
        
        // For debugging request body on POST/PUT requests
        if (req.body && (req.method === 'POST' || req.method === 'PUT')) {
          console.log('Request body:', JSON.stringify(req.body));
          
          // If body-parser already consumed the body, we need to restream it
          if (req.body && !proxyReq.headersSent) {
            const bodyData = JSON.stringify(req.body);
            proxyReq.setHeader('Content-Type', 'application/json');
            proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
            proxyReq.write(bodyData);
          }
        }
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log(`Received response: ${proxyRes.statusCode} for ${req.method} ${req.path}`);
        
        // Add CORS headers to ensure browser accepts the response
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      },
      onError: (err, req, res) => {
        console.error(`Proxy error for ${req.method} ${req.path}:`, err);
        
        if (!res.headersSent) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            error: 'Proxy error', 
            message: err.message,
            path: req.path
          }));
        }
      }
    })
  );
};