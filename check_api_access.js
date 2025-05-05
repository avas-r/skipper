#!/usr/bin/env node
const axios = require('axios');

// API endpoints to test
const endpoints = [
  { url: 'http://localhost:8000/api/v1/healthcheck', method: 'get', description: 'API Health Check' },
  { url: 'http://localhost:8000/api/v1/subscriptions/tiers/public', method: 'get', description: 'Public Subscription Tiers' },
  { url: 'http://localhost:3000/api/v1/subscriptions/tiers/public', method: 'get', description: 'Frontend Proxy to Public Tiers' }
];

// Run tests
async function runTests() {
  console.log('📡 Testing API connectivity...\n');
  
  for (const endpoint of endpoints) {
    try {
      console.log(`Testing: ${endpoint.description} - ${endpoint.url}`);
      const response = await axios({
        method: endpoint.method,
        url: endpoint.url,
        timeout: 5000,
        headers: {
          'Accept': 'application/json'
        }
      });
      
      console.log(`✅ SUCCESS (${response.status}): ${endpoint.description}`);
      
      if (response.data) {
        if (Array.isArray(response.data)) {
          console.log(`   Received ${response.data.length} items`);
        } else if (typeof response.data === 'object') {
          console.log(`   Response: ${JSON.stringify(response.data).slice(0, 100)}...`);
        }
      }
    } catch (err) {
      console.log(`❌ FAILED: ${endpoint.description}`);
      
      if (err.response) {
        console.log(`   Status: ${err.response.status}`);
        console.log(`   Data: ${JSON.stringify(err.response.data).slice(0, 100)}...`);
      } else if (err.request) {
        console.log(`   No response received`);
      } else {
        console.log(`   Error: ${err.message}`);
      }
    }
    console.log(''); // Add spacing between tests
  }
  
  console.log('📋 Test Summary:');
  console.log('1. If direct API calls (localhost:8000) fail but proxy calls (localhost:3000) succeed:');
  console.log('   - Your proxy is working correctly but has CORS issues');
  console.log('2. If both direct and proxy calls fail:');
  console.log('   - Your backend might not be running or has configuration issues');
  console.log('3. If direct calls succeed but proxy calls fail:');
  console.log('   - Your proxy configuration needs to be fixed');
}

runTests().catch(console.error);