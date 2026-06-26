import { useEffect } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import ToastContainer from './Toast';
import { useToastStore } from '../../store/toastStore';
import Button from './Button';

const meta = {
  title: 'Primitives/Toast',
  component: ToastContainer,
  tags: ['autodocs'],
} satisfies Meta<typeof ToastContainer>;

export default meta;
type Story = StoryObj<typeof meta>;

function addToast(type: 'success' | 'error' | 'info', message: string) {
  useToastStore.getState().addToast({ type, message });
}

export const Success: Story = {
  render: () => {
    useEffect(() => {
      addToast('success', 'Product updated successfully');
    }, []);
    return <ToastContainer />;
  },
};

export const Error: Story = {
  render: () => {
    useEffect(() => {
      addToast('error', 'Failed to save changes. Please try again.');
    }, []);
    return <ToastContainer />;
  },
};

export const Info: Story = {
  render: () => {
    useEffect(() => {
      addToast('info', 'Your session will expire in 5 minutes.');
    }, []);
    return <ToastContainer />;
  },
};

export const Stacked: Story = {
  render: () => {
    useEffect(() => {
      addToast('success', 'Product created');
      addToast('info', 'Syncing with supplier...');
      addToast('error', 'Failed to update inventory');
    }, []);
    return <ToastContainer />;
  },
};

export const Interactive: Story = {
  render: () => {
    const add = (type: 'success' | 'error' | 'info') => {
      const messages = {
        success: 'Operation completed successfully!',
        error: 'Something went wrong. Please retry.',
        info: 'Here is some useful information.',
      };
      addToast(type, messages[type]);
    };
    return (
      <div className="flex gap-2">
        <Button variant="primary" size="sm" onClick={() => add('success')}>Success</Button>
        <Button variant="danger" size="sm" onClick={() => add('error')}>Error</Button>
        <Button variant="secondary" size="sm" onClick={() => add('info')}>Info</Button>
        <ToastContainer />
      </div>
    );
  },
};
