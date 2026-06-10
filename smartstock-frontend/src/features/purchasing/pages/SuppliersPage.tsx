import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SupplierModal } from '../components/SupplierModal';
import { useAuthStore } from '../../../store/authStore';
import { useSuppliers, useCreateSupplier, useUpdateSupplier, useDeleteSupplier } from '../hooks/useSuppliers';
import type { Supplier } from '../types';

export const SuppliersPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const role = user?.role;
  const isManagerOrAbove = role === 'manager' || role === 'admin';

  const { data: suppliers, isLoading, error } = useSuppliers();
  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
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

  const handleOpenEditModal = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setIsModalOpen(true);
  };

  const handleSaveSupplier = async (data: Parameters<typeof createMutation.mutateAsync>[0]) => {
    setErrorMessage(null);
    if (editingSupplier) {
      await updateMutation.mutateAsync({ id: editingSupplier.id, payload: data });
    } else {
      await createMutation.mutateAsync(data);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    setErrorMessage(null);
    const confirmed = window.confirm(`Are you sure you want to delete supplier "${name}"?`);
    if (!confirmed) return;

    try {
      await deleteMutation.mutateAsync(id);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 409) {
        setErrorMessage(
          axiosErr.response.data?.detail || 'Cannot delete supplier because they have open Purchase Orders.'
        );
      } else {
        setErrorMessage('An error occurred while attempting to delete the supplier.');
      }
    }
  };

  const filteredSuppliers = suppliers?.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const sortedSuppliers = [...filteredSuppliers].sort((a, b) => {
    const valueA = a[sortField as keyof Supplier] ?? '';
    const valueB = b[sortField as keyof Supplier] ?? '';
    if (valueA < valueB) return sortOrder === 'asc' ? -1 : 1;
    if (valueA > valueB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  if (isLoading) {
    return <div className="supplier-management-container"><p>Loading suppliers...</p></div>;
  }

  if (error) {
    return (
      <div className="supplier-management-container">
        <div className="alert alert-danger">Failed to load suppliers. Please try again later.</div>
      </div>
    );
  }

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
            <th onClick={() => handleSort('default_lead_time_days')}>Default Lead Time {sortField === 'default_lead_time_days' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedSuppliers.map((supplier) => (
            <tr key={supplier.id}>
              <td>{supplier.name}</td>
              <td>{supplier.contact_email || '—'}</td>
              <td>{supplier.contact_phone || '—'}</td>
              <td>{supplier.address || '—'}</td>
              <td>{supplier.default_lead_time_days} days</td>
              <td>
                <span className={`badge ${supplier.is_active ? 'active' : 'inactive'}`}>
                  {supplier.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="actions-cell">
                <button
                  className="link-btn"
                  onClick={() => navigate(`/inventory?supplierId=${supplier.id}`)}
                >
                  View Products
                </button>

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
