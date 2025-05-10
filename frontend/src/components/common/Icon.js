// frontend/src/components/common/Icon.js
import React from 'react';
import PropTypes from 'prop-types';
import { SvgIcon } from '@mui/material';
import * as MuiIcons from '@mui/icons-material';

/**
 * Unified icon component that works with Material-UI icons
 * Replaces LucideIcon and LucideIconFallback components
 * 
 * @param {Object} props - Component props
 * @param {string} props.icon - Name of the MUI icon to render
 * @param {string} props.color - Color of the icon
 * @param {string} props.size - Size of the icon
 * @param {Object} props.sx - Additional styling props
 * @returns {JSX.Element} Icon component
 */
const Icon = ({ icon, color, size, sx, ...rest }) => {
  // Get the icon component from MUI icons
  const IconComponent = MuiIcons[icon];
  
  if (!IconComponent) {
    console.error(`Icon "${icon}" not found in Material-UI icons`);
    return null;
  }
  
  return (
    <IconComponent
      color={color}
      fontSize={size}
      sx={sx}
      {...rest}
    />
  );
};

Icon.propTypes = {
  icon: PropTypes.string.isRequired,
  color: PropTypes.string,
  size: PropTypes.string,
  sx: PropTypes.object
};

export default Icon;