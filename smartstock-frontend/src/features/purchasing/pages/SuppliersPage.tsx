import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SupplierModal } from '../components/SupplierModal';
import { useAuthStore } from '../../../store/authStore';
import { useSuppliers, useCreateSupplier, useUpdateSupplier, useDeleteSupplier } from '../hooks/useSuppliers';
import { useToastStore } from '../../../store/toastStore';
import type { Supplier } from '../types';

export const SuppliersPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const role = user?.role;
  const isManagerOrAbove = role === 'manager' || role === 'admin';
  const isViewer = role === 'viewer';

  const [searchQuery, setSearchQuery] = useState('');

  const { data: suppliers, isLoading, error } = useSuppliers(searchQuery || undefined);
  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();
  const [sortField, setSortField] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null);

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

  const addToast = useToastStore((s) => s.addToast);

  const handleSaveSupplier = async (data: Parameters<typeof createMutation.mutateAsync>[0]) => {
    setErrorMessage(null);
    try {
      if (editingSupplier) {
        await updateMutation.mutateAsync({ id: editingSupplier.id, payload: data });
        addToast('Supplier updated', 'success');
      } else {
        await createMutation.mutateAsync(data);
        addToast('Supplier created', 'success');
      }
      setIsModalOpen(false);
    } catch {
      addToast('Failed to save supplier', 'error');
    }
  };

  const handleDelete = async (id: number, name: string) => {
    setErrorMessage(null);
    setDeleteConfirm({ id, name });
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    const { id } = deleteConfirm;
    setDeleteConfirm(null);

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
              <td>{isViewer ? '—' : (supplier.contact_email || '—')}</td>
              <td>{isViewer ? '—' : (supplier.contact_phone || '—')}</td>
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

      {deleteConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
          onClick={() => setDeleteConfirm(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Confirm deletion"
        >
          <div
            className="bg-white rounded-lg shadow-elevated w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900">Delete Supplier</h2>
              <p className="mt-2 text-sm text-gray-600">
                Are you sure you want to delete supplier <strong>{deleteConfirm.name}</strong>? This action cannot be undone.
              </p>
            </div>
            <div className="flex items-center justify-end gap-3 px-6 pb-6">
              <button
                className="px-4 py-2 text-sm rounded-md border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 text-sm rounded-md bg-red-600 text-white hover:bg-red-700 transition-colors"
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
