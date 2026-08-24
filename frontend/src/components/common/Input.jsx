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
      />

      {rightElement}
    </div>
  );
};

export default Input;  