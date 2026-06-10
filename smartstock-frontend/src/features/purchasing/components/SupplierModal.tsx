import React, { useState } from 'react';
import type { Supplier, CreateSupplierPayload } from '../types';

interface SupplierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: CreateSupplierPayload) => Promise<void>;
  initialData?: Supplier | null;
}

function getInitialFormData(initialData?: Supplier | null): CreateSupplierPayload {
  if (initialData) {
    return {
      name: initialData.name,
      contact_email: initialData.contact_email,
      contact_phone: initialData.contact_phone,
      address: initialData.address,
      default_lead_time_days: initialData.default_lead_time_days,
      is_active: initialData.is_active,
    };
  }
  return { name: '', contact_email: '', contact_phone: '', address: '', default_lead_time_days: 1, is_active: true };
}

export const SupplierModal: React.FC<SupplierModalProps> = ({ isOpen, onClose, onSave, initialData }) => {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  return (
    <SupplierModalForm
      key={initialData?.id ?? 'new'}
      initialData={initialData}
      onClose={onClose}
      onSave={onSave}
      errors={errors}
      setErrors={setErrors}
      isSubmitting={isSubmitting}
      setIsSubmitting={setIsSubmitting}
    />
  );
};

interface FormProps {
  initialData: Supplier | null | undefined;
  onClose: () => void;
  onSave: (data: CreateSupplierPayload) => Promise<void>;
  errors: Record<string, string>;
  setErrors: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  isSubmitting: boolean;
  setIsSubmitting: React.Dispatch<React.SetStateAction<boolean>>;
}

const SupplierModalForm: React.FC<FormProps> = ({ initialData, onClose, onSave, errors, setErrors, isSubmitting, setIsSubmitting }) => {
  const [formData, setFormData] = useState<CreateSupplierPayload>(() => getInitialFormData(initialData));

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Supplier name is required.';

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.contact_email || !emailRegex.test(formData.contact_email)) {
      newErrors.contact_email = 'A valid contact email is required.';
    }

    if (!formData.default_lead_time_days || formData.default_lead_time_days < 1 || !Number.isInteger(formData.default_lead_time_days)) {
      newErrors.default_lead_time_days = 'Lead time must be a positive integer.';
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
    } catch {
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
            <label>Contact Email *</label>
            <input
              type="email"
              value={formData.contact_email}
              onChange={e => setFormData({...formData, contact_email: e.target.value})}
            />
            {errors.contact_email && <span className="error-text">{errors.contact_email}</span>}
          </div>

          <div className="form-group">
            <label>Contact Phone</label>
            <input
              type="text"
              value={formData.contact_phone || ''}
              onChange={e => setFormData({...formData, contact_phone: e.target.value})}
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
              value={formData.default_lead_time_days}
              onChange={e => setFormData({...formData, default_lead_time_days: parseInt(e.target.value) || 0})}
            />
            {errors.default_lead_time_days && <span className="error-text">{errors.default_lead_time_days}</span>}
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
