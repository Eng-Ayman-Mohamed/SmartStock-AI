import type { TestRunnerConfig } from '@storybook/test-runner';

const config: TestRunnerConfig = {
  async postVisit(page, context) {
    await page.screenshot({
      path: `__snapshots__/${context.id}.png`,
      fullPage: true,
    });
  },
};

export default config;
