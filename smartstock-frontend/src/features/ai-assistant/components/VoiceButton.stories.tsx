import type { Meta, StoryObj } from '@storybook/react-vite';
import VoiceButton from './VoiceButton';

const meta = {
  title: 'AI Assistant/VoiceButton',
  component: VoiceButton,
  tags: ['autodocs'],
  args: {
    onTranscript: (text: string) => console.log('Transcript:', text),
  },
  parameters: {
    a11y: {
      config: {
        rules: [{ id: 'aria-allowed-role', enabled: false }],
      },
    },
  },
} satisfies Meta<typeof VoiceButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
