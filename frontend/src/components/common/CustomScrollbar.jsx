import React from 'react';

const CustomScrollbar = ({ 
  children, 
  className = '', 
  height = '100%', 
  width = '100%',
  style = {}, 
  ...props 
}) => {
  return (
    <div 
      className={`custom-scrollbar ${className}`}
      style={{ 
        overflow: 'auto', 
        height, 
        width,
        ...style 
      }}
      {...props}
    >
      {children}
    </div>
  );
};

export default CustomScrollbar;