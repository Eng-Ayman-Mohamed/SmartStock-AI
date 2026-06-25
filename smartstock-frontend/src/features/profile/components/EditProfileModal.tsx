import { useState, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import Modal from '../../../shared/components/Modal';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import { useAuthStore } from '../../../store/authStore';
import { useToastStore } from '../../../store/toastStore';
import { updateProfile } from '../api';
import type { UpdateProfileData } from '../api';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function EditProfileModal({ open, onClose }: Props) {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const addToast = useToastStore((s) => s.addToast);
  const queryClient = useQueryClient();

  const [name, setName] = useState(user?.name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');

  const mutation = useMutation({
    mutationFn: async (data: UpdateProfileData) => {
      await updateProfile(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      if (user) {
        setUser({ ...user, name, email });
      }
      addToast('Profile updated', 'success');
      onClose();
    },
    onError: () => {
      addToast('Failed to update profile', 'error');
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate({ name: name.trim() || undefined, email: email.trim() || undefined });
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Edit Profile"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Saving…' : 'Save'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-body text-ink-muted mb-1">
            Name
          </label>
          <Input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-body text-ink-muted mb-1">
            Email
          </label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
          />
        </div>
      </form>
    </Modal>
  );
}
