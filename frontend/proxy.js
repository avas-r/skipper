// Simple proxy config for development
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to the backend server
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      logLevel: 'debug',
      secure: false,
      pathRewrite: {
        '^/api': '/api'
      },
      onProxyReq: (proxyReq, req, res) => {
        // Log the request
        console.log(`Proxying ${req.method} request to: ${proxyReq.path}`);
        
        // Log request body for debugging if it's a POST or PUT
        if (req.method === 'POST' || req.method === 'PUT') {
          const bodyData = JSON.stringify(req.body);
          console.log('Request Body:', bodyData);
        }
      },
      onProxyRes: (proxyRes, req, res) => {
        // Log response for debugging
        console.log(`Response from backend: ${proxyRes.statusCode}`);
        
        // Capture the response body for debugging
        let responseBody = '';
        const originalPipe = proxyRes.pipe;
        
        proxyRes.pipe = function(dest) {
          proxyRes.on('data', chunk => {
            responseBody += chunk.toString('utf8');
          });
          
          proxyRes.on('end', () => {
            console.log('Response Body:', responseBody);
          });
          
          return originalPipe.call(this, dest);
        };
      }
    })
  );
};