import React from 'react';
import PropTypes from 'prop-types';
import { SvgIcon } from '@mui/material';
import * as LucideIcons from 'lucide-react';

/**
 * LucideIcon - A wrapper component that allows Lucide React icons to be used with Material-UI
 * 
 * @param {Object} props - Component props
 * @param {string} props.icon - Name of the Lucide icon to render
 * @param {string} props.color - Color of the icon (inherits if not specified)
 * @param {string} props.size - Size of the icon (inherits fontSize if not specified)
 * @param {Object} props.sx - Additional SvgIcon sx props
 * @returns {JSX.Element} SvgIcon component wrapped around the Lucide icon
 */
const LucideIcon = ({ icon, color, size, sx, ...rest }) => {
  // Get the icon component from Lucide library
  const IconComponent = LucideIcons[icon];
  
  if (!IconComponent) {
    console.error(`Lucide icon "${icon}" not found`);
    return null;
  }
  
  return (
    <SvgIcon 
      component={IconComponent} 
      inheritViewBox 
      color={color}
      fontSize={size}
      sx={sx}
      {...rest} 
    />
  );
};

LucideIcon.propTypes = {
  icon: PropTypes.string.isRequired,
  color: PropTypes.string,
  size: PropTypes.string,
  sx: PropTypes.object
};

export default LucideIcon;