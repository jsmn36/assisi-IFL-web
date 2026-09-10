/**
 * Mobile Form Component
 * Touch-friendly form with mobile optimizations
 */
import { useState, type FormEvent } from 'react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { Input } from '@/components/Input';
import { Select } from '@/components/Select';
import { Label } from '@/components/Label';
import { Button } from '@/components/Button';

interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'date' | 'select' | 'textarea';
  placeholder?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
  rows?: number;
}

interface MobileFormProps {
  fields: FormField[];
  onSubmit: (data: any) => void;
  submitLabel?: string;
  loading?: boolean;
  initialValues?: any;
}

export function MobileForm({
  fields,
  onSubmit,
  submitLabel = 'Submit',
  loading = false,
  initialValues = {},
}: MobileFormProps) {
  const isMobile = useIsMobile();
  const [formData, setFormData] = useState(initialValues);

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const inputClassName = isMobile
    ? 'h-12 text-base' // Larger touch targets on mobile
    : 'h-10 text-sm';

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {fields.map((field) => (
        <div key={field.name} className="space-y-1.5">
          <Label className={isMobile ? 'text-base' : 'text-sm'}>
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          
          {field.type === 'select' ? (
            <Select
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              className={inputClassName}
              options={[
                { value: '', label: `Select ${field.label}` },
                ...(field.options || [])
              ]}
            />
          ) : field.type === 'textarea' ? (
            <textarea
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              required={field.required}
              rows={field.rows || 4}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${isMobile ? 'text-base' : 'text-sm'}`}
            />
          ) : (
            <Input
              type={field.type}
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              required={field.required}
              className={inputClassName}
            />
          )}
        </div>
      ))}

      <Button
        type="submit"
        disabled={loading}
        className={`w-full ${isMobile ? 'h-12 text-base' : 'h-10 text-sm'}`}
      >
        {loading ? 'Submitting...' : submitLabel}
      </Button>
    </form>
  );
}
