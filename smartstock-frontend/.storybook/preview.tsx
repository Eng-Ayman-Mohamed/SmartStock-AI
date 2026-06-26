import type { Preview } from '@storybook/react-vite';
import { withRouter, withQueryClient } from '../src/shared/test-utils/decorators';
import '../src/index.css';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      disable: true,
    },
  },
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'Global theme for components',
      defaultValue: 'light',
      toolbar: {
        icon: 'circlehollow',
        items: [
          { value: 'light', icon: 'sun', title: 'Light' },
          { value: 'dark', icon: 'moon', title: 'Dark' },
        ],
        dynamicTitle: true,
      },
    },
  },
  decorators: [
    withRouter,
    withQueryClient,
    (Story, context) => {
      const theme = context.globals.theme;
      const root = document.documentElement;
      root.classList.toggle('dark', theme === 'dark');
      return <Story />;
    },
  ],
  initialGlobals: {
    theme: 'light',
  },
};

export default preview;
