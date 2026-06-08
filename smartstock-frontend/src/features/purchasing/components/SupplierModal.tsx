import React, { useState, useEffect } from 'react';

interface Supplier {
  id?: number;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  lead_time_days: number;
  is_active: boolean;
}

interface SupplierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Supplier) => Promise<void>;
  initialData?: Supplier | null;
}

export const SupplierModal: React.FC<SupplierModalProps> = ({ isOpen, onClose, onSave, initialData }) => {
  const [formData, setFormData] = useState<Supplier>({
    name: '',
    email: '',
    phone: '',
    address: '',
    lead_time_days: 1,
    is_active: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Pre-populate form data when editing an existing supplier
  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({ name: '', email: '', phone: '', address: '', lead_time_days: 1, is_active: true });
    }
    setErrors({});
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Supplier name is required.';
    
    // Simple email regex validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address.';
    }

    // Lead time must be a positive integer
    if (!formData.lead_time_days || formData.lead_time_days <= 0 || !Number.isInteger(Number(formData.lead_time_days))) {
      newErrors.lead_time_days = 'Lead time must be a positive integer.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await onSave(formData);
      onClose();
    } catch (err) {
      // Errors coming back from the save API call can be set here
      setErrors({ api: 'Failed to save supplier records.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{initialData ? 'Edit Supplier' : 'Add Supplier'}</h2>
        <form onSubmit={handleSubmit}>
          {errors.api && <div className="error-banner">{errors.api}</div>}
          
          <div className="form-group">
            <label>Supplier Name *</label>
            <input 
              type="text" 
              value={formData.name} 
              onChange={e => setFormData({...formData, name: e.target.value})}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label>Contact Email</label>
            <input 
              type="text" 
              value={formData.email || ''} 
              onChange={e => setFormData({...formData, email: e.target.value})}
            />
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label>Contact Phone</label>
            <input 
              type="text" 
              value={formData.phone || ''} 
              onChange={e => setFormData({...formData, phone: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Address</label>
            <input 
              type="text" 
              value={formData.address || ''} 
              onChange={e => setFormData({...formData, address: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Default Lead Time (Days) *</label>
            <input 
              type="number" 
              value={formData.lead_time_days} 
              onChange={e => setFormData({...formData, lead_time_days: parseInt(e.target.value) || 0})}
            />
            {errors.lead_time_days && <span className="error-text">{errors.lead_time_days}</span>}
          </div>

          <div className="form-group checkbox">
            <label>
              <input 
                type="checkbox" 
                checked={formData.is_active} 
                onChange={e => setFormData({...formData, is_active: e.target.checked})}
              />
              Active Supplier Status
            </label>
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose} disabled={isSubmitting}>Cancel</button>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Supplier'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};