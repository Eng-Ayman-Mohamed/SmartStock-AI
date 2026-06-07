import { useState } from 'react';

interface Supplier {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  lead_time_days: number;
  is_active: boolean;
}

export function useSuppliers() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([
    { id: 'SUP-001', name: 'TechSupply Co.', email: 'orders@techsupply.com', phone: '+1-555-0192', address: '123 Silicon Blvd, San Jose CA', lead_time_days: 5, is_active: true },
    { id: 'SUP-002', name: 'Global Parts Inc.', email: 'sales@globalparts.com', phone: '+1-555-0143', address: '456 Logistics Way, Chicago IL', lead_time_days: 12, is_active: true },
    { id: 'SUP-003', name: 'Warehouse Direct', email: 'support@whdirect.com', phone: '+1-555-0177', address: '789 Bulk Rd, Austin TX', lead_time_days: 3, is_active: false },
  ]);

  const addSupplier = async (data: Omit<Supplier, 'id'>) => {
    const newSupplier: Supplier = { ...data, id: `SUP-00${suppliers.length + 1}` };
    setSuppliers(prev => [...prev, newSupplier]);
  };

  const updateSupplier = async (id: string, data: Partial<Supplier>) => {
    setSuppliers(prev => prev.map(s => s.id === id ? { ...s, ...data } : s));
  };

  const deleteSupplier = async (id: string) => {
    if (id === 'SUP-001') {
      const error: any = new Error("Conflict");
      error.response = {
        status: 409,
        data: { detail: "Cannot delete supplier TechSupply Co. because they have open Purchase Orders." }
      };
      throw error;
    }
    setSuppliers(prev => prev.filter(s => s.id !== id));
  };

  return { suppliers, addSupplier, updateSupplier, deleteSupplier };
}
