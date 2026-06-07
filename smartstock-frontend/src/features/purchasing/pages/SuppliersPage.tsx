import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SupplierModal } from '../components/SupplierModal';
import { useAuthStore } from '../../../store/authStore';
import { useSuppliers } from '../hooks/useSuppliers';

export const SuppliersPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const role = user?.role;
  const isManagerOrAbove = role === 'manager' || role === 'admin';

  // Custom hook utilities to pull supplier records
  const { suppliers, addSupplier, updateSupplier, deleteSupplier } = useSuppliers();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSort = (field: string) => {
    const order = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortOrder(order);
  };

  const handleOpenAddModal = () => {
    setEditingSupplier(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (supplier: any) => {
    setEditingSupplier(supplier);
    setIsModalOpen(true);
  };

  const handleSaveSupplier = async (data: any) => {
    if (editingSupplier) {
      await updateSupplier(editingSupplier.id, data);
    } else {
      await addSupplier(data);
    }
    setIsModalOpen(false);
  };

  const handleDelete = async (id: string, name: string) => {
    setErrorMessage(null);
    const confirmed = window.confirm(`Are you sure you want to delete supplier "${name}"?`);
    if (!confirmed) return;

    try {
      await deleteSupplier(id);
    } catch (err: any) {
      // Explicit 409 error conflict detection for open POs
      if (err.response && err.response.status === 409) {
        setErrorMessage(err.response.data.detail || 'Cannot delete supplier because they have open Purchase Orders.');
      } else {
        setErrorMessage('An error occurred while attempting to delete the supplier.');
      }
    }
  };

  // 1. Search filter execution
  const filteredSuppliers = suppliers?.filter((s: any) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // 2. Sort calculation execution
  const sortedSuppliers = [...filteredSuppliers].sort((a: any, b: any) => {
    const valueA = a[sortField] ?? '';
    const valueB = b[sortField] ?? '';
    if (valueA < valueB) return sortOrder === 'asc' ? -1 : 1;
    if (valueA > valueB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });


  return (
    <div className="supplier-management-container">
      <div className="header-actions">
        <h1>Supplier Management</h1>
        {isManagerOrAbove && (
          <button className="add-btn" onClick={handleOpenAddModal}>Add Supplier</button>
        )}
      </div>

      {errorMessage && <div className="alert alert-danger">{errorMessage}</div>}

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search suppliers by name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <table className="suppliers-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('name')}>Supplier Name {sortField === 'name' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</th>
            <th>Contact Email</th>
            <th>Contact Phone</th>
            <th>Address</th>
            <th onClick={() => handleSort('lead_time_days')}>Default Lead Time {sortField === 'lead_time_days' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedSuppliers.map((supplier: any) => (
            <tr key={supplier.id}>
              <td>{supplier.name}</td>
              {/* Graceful UX Redaction Check for missing fields when role is Viewer */}
              <td>{supplier.email ? supplier.email : '—'}</td>
              <td>{supplier.phone ? supplier.phone : '—'}</td>
              <td>{supplier.address ? supplier.address : '—'}</td>
              <td>{supplier.lead_time_days} days</td>
              <td>
                <span className={`badge ${supplier.is_active ? 'active' : 'inactive'}`}>
                  {supplier.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="actions-cell">
                {/* 1. Filtered inventory navigation link */}
                <button 
                  className="link-btn" 
                  onClick={() => navigate(`/inventory?supplierId=${supplier.id}`)}
                >
                  View Products
                </button>

                {/* 2. Management specific functional overrides */}
                {isManagerOrAbove && (
                  <>
                    <button className="edit-btn" onClick={() => handleOpenEditModal(supplier)}>Edit</button>
                    <button className="delete-btn" onClick={() => handleDelete(supplier.id, supplier.name)}>Delete</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <SupplierModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveSupplier}
        initialData={editingSupplier}
      />
    </div>
  );
};