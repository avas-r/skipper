import React from 'react';
import PropTypes from 'prop-types';
import { SvgIcon } from '@mui/material';

/**
 * A simpler version of LucideIcon that uses a direct import approach
 * This is useful if the dynamic import approach is causing issues
 */
const LucideIconFallback = ({ icon, color, size, sx, ...rest }) => {
  try {
    // This approach requires the icon to be imported directly at the top of the file that uses this component
    // Example: import { Play, Pause } from 'lucide-react';
    // Then: <LucideIconFallback icon={Play} />
    return (
      <SvgIcon 
        component={icon} 
        inheritViewBox 
        color={color}
        fontSize={size}
        sx={sx}
        {...rest} 
      />
    );
  } catch (error) {
    console.error(`Error rendering icon:`, error);
    return null;
  }
};

LucideIconFallback.propTypes = {
  icon: PropTypes.elementType.isRequired,
  color: PropTypes.string,
  size: PropTypes.string,
  sx: PropTypes.object
};

export default LucideIconFallback;