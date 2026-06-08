/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^~/(.*)$': '<rootDir>/app/$1',
    '\\.css$': '<rootDir>/tests/__mocks__/empty.cjs',
  },
  transform: {
    '^.+\\.(ts|tsx)$': '<rootDir>/tests/__transforms__/import-meta-transform.cjs',
  },
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testMatch: ['<rootDir>/tests/**/*.test.(ts|tsx)'],
  collectCoverageFrom: ['app/**/*.{ts,tsx}'],
  coveragePathIgnorePatterns: [
    '<rootDir>/app/root.tsx',
    '<rootDir>/app/entry.client.tsx',
    '<rootDir>/app/routes.ts',
    '/\\+types/',
  ],
  coverageReporters: ['text', 'lcov'],
  coverageThreshold: {
    global: {
      statements: 80,
      branches: 75,
      functions: 70,
      lines: 75,
    },
  },
  transformIgnorePatterns: ['node_modules/(?!(.*\\.mjs$))'],
};
