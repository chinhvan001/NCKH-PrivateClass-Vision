const Input = ({
  id,
  type = "text",
  placeholder,
  value,
  onChange,
  autoComplete,
  icon,
  rightElement,
  className = "",
  disabled = false,
}) => {
  return (
    <div className={`input-wrapper ${className}`}>
      {icon}

      <input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        disabled={disabled}
      />

      {rightElement}
    </div>
  );
};

export default Input;