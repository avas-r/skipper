module.exports = function override(config, env) {
  // Tell source-map-loader to skip lucide-react
  if (config.module && config.module.rules) {
    // Find the source-map-loader rule
    for (const rule of config.module.rules) {
      if (rule.enforce === 'pre' && rule.use && Array.isArray(rule.use)) {
        for (const useItem of rule.use) {
          if (typeof useItem === 'object' && useItem.loader && useItem.loader.includes('source-map-loader')) {
            // Add exclude for lucide-react
            rule.exclude = [
              /node_modules\/lucide-react/,
              ...(Array.isArray(rule.exclude) ? rule.exclude : rule.exclude ? [rule.exclude] : [])
            ];
            console.log('Added lucide-react to source-map-loader exclusions');
          }
        }
      } else if (rule.enforce === 'pre' && rule.loader && rule.loader.includes('source-map-loader')) {
        // Direct loader configuration (not in a use array)
        rule.exclude = [
          /node_modules\/lucide-react/,
          ...(Array.isArray(rule.exclude) ? rule.exclude : rule.exclude ? [rule.exclude] : [])
        ];
        console.log('Added lucide-react to source-map-loader exclusions');
      }
    }
  }

  return config;
};