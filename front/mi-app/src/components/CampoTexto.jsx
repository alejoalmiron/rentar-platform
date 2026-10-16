export default function CampoTexto({label, type = "text", name, value,onChange,placeholder = "", required = false, autoComplete}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
      {label && (
        <label style={{ fontWeight: '600', fontSize: '14px', color: '#374151' }}>
          {label} {required && <span style={{ color: '#dc2626' }}>*</span>}
        </label>
      )}
      <input
        type={type}
        name={name}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        style={{
          padding: '10px 12px',
          borderRadius: '6px',
          border: '1px solid #d1d5db',
          fontSize: '14px',
          outline: 'none',
          backgroundColor: '#ffffff',
          color: '#1f2937'
        }}
      />
    </div>
  );
}