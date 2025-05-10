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
      
      // Don't rewrite the path
      pathRewrite: {
        '^/api': '/api',
      },
      
      // Log request details
      onProxyReq: (proxyReq, req, res) => {
        console.log(`Proxying ${req.method} ${req.path} to ${proxyReq.path}`);
        
        // Special handling for form-urlencoded requests (like OAuth2 token requests)
        if (req.method === 'POST' && 
            req.headers['content-type'] && 
            req.headers['content-type'].includes('application/x-www-form-urlencoded')) {
          console.log('Form URL-encoded request detected - passing through as-is');
          // These requests are already properly formatted for OAuth2
        }
        // For regular JSON requests, restream the body if needed
        else if ((req.method === 'POST' || req.method === 'PUT') && req.body) {
          try {
            const bodyStr = JSON.stringify(req.body);
            console.log('Request body:', bodyStr);
            
            // Only restream if we have a body and headers aren't sent
            if (!proxyReq.headersSent) {
              proxyReq.setHeader('Content-Type', 'application/json');
              proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyStr));
              proxyReq.write(bodyStr);
              proxyReq.end();
            }
          } catch (error) {
            console.error('Error processing request body:', error);
          }
        }
      },
      
      // Log response details
      onProxyRes: (proxyRes, req, res) => {
        console.log(`Response from backend: ${proxyRes.statusCode} for ${req.method} ${req.path}`);
        
        // Add CORS headers
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      },
      
      // Handle proxy errors
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