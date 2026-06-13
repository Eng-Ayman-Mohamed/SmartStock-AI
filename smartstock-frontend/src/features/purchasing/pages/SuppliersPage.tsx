import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit3, ExternalLink, Plus, Search, Trash2, Truck, X } from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';
import { useSuppliers, useCreateSupplier, useUpdateSupplier, useDeleteSupplier } from '../hooks/useSuppliers';
import { useDebounce } from '../../../shared/hooks/useDebounce';
import { useToastStore } from '../../../store/toastStore';
import type { Supplier, CreateSupplierPayload } from '../types';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Badge from '../../../shared/components/Badge';
import Skeleton from '../../../shared/components/Skeleton';
import Modal from '../../../shared/components/Modal';
import DataTable from '../../../shared/components/DataTable';
import type { Column } from '../../../shared/components/DataTable';

export function SuppliersPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const role = user?.role;
  const isManagerOrAbove = role === 'manager' || role === 'admin';
  const isViewer = role === 'viewer';

  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, 300);

  const { data: suppliers, isLoading, error: queryError } = useSuppliers(debouncedSearch || undefined);
  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();
  const addToast = useToastStore((s) => s.addToast);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Supplier | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formData, setFormData] = useState<CreateSupplierPayload>({
    name: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    default_lead_time_days: 1,
    is_active: true,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const openAddModal = () => {
    setEditingSupplier(null);
    setFormData({
      name: '',
      contact_email: '',
      contact_phone: '',
      address: '',
      default_lead_time_days: 1,
      is_active: true,
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  const openEditModal = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      name: supplier.name,
      contact_email: supplier.contact_email,
      contact_phone: supplier.contact_phone,
      address: supplier.address,
      default_lead_time_days: supplier.default_lead_time_days,
      is_active: supplier.is_active,
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  const handleDeleteClick = (supplier: Supplier) => {
    setDeleteTarget(supplier);
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.name.trim()) {
      errors.name = 'Supplier name is required.';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.contact_email || !emailRegex.test(formData.contact_email)) {
      errors.contact_email = 'A valid contact email is required.';
    }
    if (!formData.default_lead_time_days || formData.default_lead_time_days < 1 || !Number.isInteger(formData.default_lead_time_days)) {
      errors.default_lead_time_days = 'Lead time must be a positive integer.';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;
    setErrorMessage(null);
    try {
      if (editingSupplier) {
        await updateMutation.mutateAsync({ id: editingSupplier.id, payload: formData });
        addToast('Supplier updated', 'success');
      } else {
        await createMutation.mutateAsync(formData);
        addToast('Supplier created', 'success');
      }
      setIsModalOpen(false);
    } catch {
      addToast('Failed to save supplier', 'error');
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const { id } = deleteTarget;
    setDeleteTarget(null);
    setErrorMessage(null);
    try {
      await deleteMutation.mutateAsync(id);
      addToast('Supplier deleted', 'success');
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

  const sortedSuppliers = useMemo(() => {
    if (!suppliers) return [];
    return [...suppliers].sort((a, b) => a.name.localeCompare(b.name));
  }, [suppliers]);

  const columns: Column<Supplier>[] = [
    {
      key: 'name',
      label: 'Supplier Name',
      render: (r) => <span className="truncate block font-medium text-ink">{r.name}</span>,
    },
    {
      key: 'contact_email',
      label: 'Contact Email',
      render: (r) => <span className="truncate block text-ink-muted">{isViewer ? '—' : (r.contact_email || '—')}</span>,
    },
    {
      key: 'contact_phone',
      label: 'Contact Phone',
      render: (r) => <span className="text-ink-muted">{isViewer ? '—' : (r.contact_phone || '—')}</span>,
    },
    {
      key: 'address',
      label: 'Address',
      render: (r) => <span className="truncate block text-ink-muted">{r.address || '—'}</span>,
    },
    {
      key: 'default_lead_time_days',
      label: 'Lead Time',
      width: '120px',
      render: (r) => <span className="tabular-nums">{r.default_lead_time_days} days</span>,
    },
    {
      key: 'is_active',
      label: 'Status',
      width: '120px',
      render: (r) => <Badge variant={r.is_active ? 'Active' : 'Inactive'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
    },
    {
      key: 'actions',
      label: 'Actions',
      width: '120px',
      render: (r) => (
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" className="w-7 px-0" onClick={() => navigate(`/inventory?supplierId=${r.id}`)} aria-label="View products">
            <ExternalLink className="w-4 h-4" />
          </Button>
          {isManagerOrAbove && (
            <>
              <Button variant="ghost" size="sm" className="w-7 px-0" onClick={() => openEditModal(r)} aria-label="Edit supplier">
                <Edit3 className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" className="w-7 px-0" onClick={() => handleDeleteClick(r)} aria-label="Delete supplier">
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-page-heading text-ink">Suppliers</h1>
        {isManagerOrAbove && (
          <Button variant="primary" size="md" onClick={openAddModal}>
            <Plus className="w-4 h-4" /> Add Supplier
          </Button>
        )}
      </div>

      {errorMessage && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
          {errorMessage}
        </div>
      )}

      {queryError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
          Failed to load suppliers. Please try again later.
        </div>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-faint" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search suppliers by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-9 pl-10 pr-4 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors duration-150"
            aria-label="Search suppliers"
          />
        </div>
      </div>

      <Card noPadding>
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((item) => <Skeleton key={item} className="h-10" />)}
          </div>
        ) : sortedSuppliers.length === 0 ? (
          <EmptyState
            icon={Truck}
            heading="No suppliers yet"
            body="Add your first supplier to start managing procurement."
            actionLabel={isManagerOrAbove ? 'Add Supplier' : undefined}
            onAction={isManagerOrAbove ? openAddModal : undefined}
          />
        ) : (
          <DataTable
            columns={columns}
            data={sortedSuppliers}
            keyExtractor={(r) => String(r.id)}
            caption="Suppliers list"
          />
        )}
      </Card>

      <Modal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingSupplier ? 'Edit Supplier' : 'Add Supplier'}
        footer={
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="md" onClick={() => setIsModalOpen(false)}>
              <X className="w-4 h-4" /> Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={handleSave}
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              <Plus className="w-4 h-4" /> {editingSupplier ? 'Save Changes' : 'Create Supplier'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-caption text-ink-muted mb-1">Supplier Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              placeholder="Acme Supplies"
              aria-label="Supplier name"
            />
            {formErrors.name && <p className="text-caption text-red-600 mt-1">{formErrors.name}</p>}
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">Contact Email *</label>
            <input
              type="email"
              value={formData.contact_email}
              onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              placeholder="contact@acme.com"
              aria-label="Contact email"
            />
            {formErrors.contact_email && <p className="text-caption text-red-600 mt-1">{formErrors.contact_email}</p>}
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">Contact Phone</label>
            <input
              type="text"
              value={formData.contact_phone || ''}
              onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              placeholder="+1 (555) 123-4567"
              aria-label="Contact phone"
            />
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">Address</label>
            <input
              type="text"
              value={formData.address || ''}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              placeholder="123 Main St, City, State"
              aria-label="Address"
            />
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">Default Lead Time (Days) *</label>
            <input
              type="number"
              value={formData.default_lead_time_days}
              onChange={(e) => setFormData({ ...formData, default_lead_time_days: parseInt(e.target.value) || 0 })}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink tabular-nums placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              placeholder="7"
              aria-label="Default lead time in days"
            />
            {formErrors.default_lead_time_days && <p className="text-caption text-red-600 mt-1">{formErrors.default_lead_time_days}</p>}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded border-hairline text-brand-600 focus:ring-brand-600"
            />
            <label htmlFor="is_active" className="text-body text-ink">Active Supplier</label>
          </div>
        </div>
      </Modal>

      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete Supplier"
        footer={
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="md" onClick={() => setDeleteTarget(null)}>
              <X className="w-4 h-4" /> Cancel
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={confirmDelete}
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="w-4 h-4" /> {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        }
      >
        <p className="text-body text-ink-secondary">
          Are you sure you want to delete supplier <strong>{deleteTarget?.name}</strong>? This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}