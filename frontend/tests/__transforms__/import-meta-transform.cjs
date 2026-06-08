const { TsJestTransformer } = require('ts-jest');

/**
 * ts-jest transformer that rewrites `import.meta.env` (Vite-only syntax) into
 * plain objects/values so Jest, which runs in a CommonJS context, can evaluate
 * React Router framework code without choking on `import.meta`.
 */
class ImportMetaTransformer extends TsJestTransformer {
  constructor() {
    super({
      tsconfig: 'tsconfig.jest.json',
      useESM: true,
    });
  }

  process(sourceText, sourcePath, options) {
    const patched = sourceText
      .replace(/import\.meta\.env\.(\w+)/g, (_match, key) => {
        const envMap = { DEV: 'false', PROD: 'true', MODE: '"test"' };
        return envMap[key] || 'undefined';
      })
      .replace(/import\.meta\.env/g, '({})');
    return super.process(patched, sourcePath, options);
  }
}

module.exports = new ImportMetaTransformer();
