'use strict';
const stylisticTs = require('@stylistic/eslint-plugin-ts');
const stylisticJs = require('@stylistic/eslint-plugin-js');
const parserTs = require('@typescript-eslint/parser');
const tsLint = require('@typescript-eslint/eslint-plugin');
const eslintPluginUnicorn = require('eslint-plugin-unicorn');
const oxlint = require('eslint-plugin-oxlint');
const mdLint2 = require('eslint-plugin-markdownlint');
const parserMd = require('eslint-plugin-markdownlint/parser');
const reactHooks = require('eslint-plugin-react-hooks');
const reactRefresh = require('eslint-plugin-react-refresh');
const fileRules = require('eslint-plugin-check-file');

const tsRules = {
  'no-unused-vars': 'off',
  '@typescript-eslint/no-unused-vars': [
    'warn',
    { argsIgnorePattern: '^_', ignoreRestSiblings: true },
  ],
  '@typescript-eslint/consistent-type-imports': 'error',
  '@typescript-eslint/no-mixed-enums': 'error',
  '@typescript-eslint/no-unsafe-enum-comparison': 'error',
  '@typescript-eslint/prefer-enum-initializers': 'error',
  '@typescript-eslint/prefer-literal-enum-member': 'error',
  '@typescript-eslint/adjacent-overload-signatures': 'error',
  '@typescript-eslint/no-array-delete': 'error',
  '@typescript-eslint/no-misused-new': 'error',
  //   '@typescript-eslint/no-misused-promises': [
  //     'error',
  //     {
  //       'checksConditionals': true,
  //       'checksSpreads': true,
  //       'checksVoidReturn': true
  //     }
  //   ],
  
  // FORMATTING RULES
  '@stylistic/ts/lines-between-class-members': ['error', 'always', { exceptAfterOverload: true }],
  '@stylistic/ts/member-delimiter-style': 'error',
  '@stylistic/ts/space-before-blocks': 'error',
  '@stylistic/ts/type-annotation-spacing': 'error',
  '@stylistic/js/block-spacing': 'error',
  '@stylistic/js/brace-style': ['error', '1tbs', { allowSingleLine: true }],
  '@stylistic/js/comma-dangle': ['error', 'always-multiline'],
  '@stylistic/js/comma-spacing': ['error', { before: false, after: true }],
  '@stylistic/js/function-call-spacing': ['error', 'never'],
  '@stylistic/js/key-spacing': ['error', { beforeColon: false, afterColon: true }],
  '@stylistic/js/keyword-spacing': ['error', { before: true, after: true }],
  '@stylistic/js/no-extra-semi': 'error',
  '@stylistic/js/object-curly-spacing': ['error', 'always'],
  '@stylistic/js/padding-line-between-statements': [
    'error',
    { blankLine: 'always', prev: '*', next: 'return' },
  ],
  '@stylistic/js/quote-props': ['error', 'as-needed'],
  '@stylistic/js/quotes': ['error', 'single', { avoidEscape: true, allowTemplateLiterals: true }],
  '@stylistic/js/semi': 'error',
  '@stylistic/js/space-before-function-paren': ['error', {
    anonymous: 'always',
    named: 'never',
    asyncArrow: 'always',
  }],
  '@stylistic/js/space-infix-ops': 'error',
  
  '@stylistic/js/dot-location': ['error', 'property'],
  // https://github.com/sindresorhus/eslint-plugin-unicorn/tree/main/docs/rules
  '@unicorn/catch-error-name': [
    'error',
    {
      ignore: [
        '^error\\d*$',
        '^err\\d*$',
        /^ignore/i,
      ],
    },
  ],
  '@unicorn/filename-case': [
    'error',
    {
      case: 'kebabCase',
      ignore: [
        /^[0-9]{13}-/,
      ],
    },
  ],
  '@unicorn/new-for-builtins': 'error',
  '@unicorn/no-abusive-eslint-disable': 'error',
  '@unicorn/no-array-for-each': 'warn',
  '@unicorn/no-array-method-this-argument': 'error',
  '@unicorn/no-array-push-push': 'error',
  '@unicorn/no-await-in-promise-methods': 'error',
  '@unicorn/no-for-loop': 'warn',
  '@unicorn/no-instanceof-array': 'error',
  '@unicorn/no-new-buffer': 'error',
  '@unicorn/no-static-only-class': 'error',
  '@unicorn/no-thenable': 'error',
  '@unicorn/no-typeof-undefined': 'error',
  '@unicorn/no-unnecessary-await': 'error',
  '@unicorn/no-unnecessary-polyfills': [
    'error',
    {
      targets: 'node > 16',
    },
  ],
  '@unicorn/no-unreadable-iife': 'error',
  '@unicorn/no-useless-fallback-in-spread': 'error',
  '@unicorn/no-useless-length-check': 'error',
  '@unicorn/no-useless-promise-resolve-reject': 'error',
  '@unicorn/no-useless-spread': 'error',
  '@unicorn/numeric-separators-style': ['error',
    {
      onlyIfContainsSeparator: false,
      number: { minimumDigits: 5, groupLength: 3 },
      octal: { minimumDigits: 0, groupLength: 4 },
      hexadecimal: { minimumDigits: 0, groupLength: 4 },
      binary: { minimumDigits: 0, groupLength: 8 },
    },
  ],
  '@unicorn/prefer-array-find': 'error',
  '@unicorn/prefer-array-flat': 'error',
  '@unicorn/prefer-array-flat-map': 'error',
  '@unicorn/prefer-array-index-of': 'error',
  '@unicorn/prefer-array-some': 'error',
  '@unicorn/prefer-at': 'error',
  '@unicorn/prefer-code-point': 'error',
  '@unicorn/prefer-export-from': 'error',
  '@unicorn/prefer-includes': 'error',
  '@unicorn/prefer-json-parse-buffer': 'error',
  '@unicorn/prefer-logical-operator-over-ternary': 'error',
  '@unicorn/prefer-math-trunc': 'error',
  '@unicorn/prefer-modern-math-apis': 'error',
  // '@unicorn/prefer-module': 'error',
  '@unicorn/prefer-negative-index': 'error',
  '@unicorn/prefer-node-protocol': 'error',
  '@unicorn/prefer-number-properties': 'error',
  '@unicorn/prefer-prototype-methods': 'error',
  '@unicorn/prefer-regexp-test': 'error',
  '@unicorn/prefer-set-has': 'error',
  '@unicorn/prefer-set-size': 'error',
  '@unicorn/prefer-spread': 'error',
  '@unicorn/prefer-string-replace-all': 'error',
  '@unicorn/prefer-string-slice': 'error',
  '@unicorn/prefer-string-trim-start-end': 'error',
  '@unicorn/prefer-ternary': 'error',
  '@unicorn/require-array-join-separator': 'error',
  '@unicorn/require-number-to-fixed-digits-argument': 'error',
  '@unicorn/template-indent': 'error',
  '@unicorn/throw-new-error': 'error',
  
  // forbid usage of query builder 
  'no-restricted-properties': [
    'error',
    {
      object: 'QueryBuilder',
      message: 'USE ORM CAPABILITIES NOT QUERY BUILDER',
    },
  ],
};
const tsRulesForCommonLib = { ...tsRules, '@unicorn/filename-case': 'off' };
const tsRulesForWeb = {
  ...tsRules,
  'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
};

const jsRules = {
  'no-unused-vars': 'off',
  '@typescript-eslint/no-unused-vars': [
    'warn',
    { argsIgnorePattern: '^_', ignoreRestSiblings: true },
  ],
  '@typescript-eslint/consistent-type-imports': ['error', { fixStyle: 'inline-type-imports' }],
  '@typescript-eslint/no-mixed-enums': 'error',
  '@typescript-eslint/no-unsafe-enum-comparison': 'error',
  '@typescript-eslint/prefer-enum-initializers': 'error',
  '@typescript-eslint/prefer-literal-enum-member': 'error',
  '@typescript-eslint/adjacent-overload-signatures': 'error',
  '@typescript-eslint/no-array-delete': 'error',
  '@typescript-eslint/no-misused-new': 'error',
  //   '@typescript-eslint/no-misused-promises': [
  //     'error',
  //     {
  //       'checksConditionals': true,
  //       'checksSpreads': true,
  //       'checksVoidReturn': true
  //     }
  //   ],
  
  // FORMATTING RULES
  '@stylistic/js/block-spacing': 'error',
  '@stylistic/js/brace-style': ['error', '1tbs', { allowSingleLine: true }],
  '@stylistic/js/comma-dangle': ['error', 'always-multiline'],
  '@stylistic/js/comma-spacing': ['error', { before: false, after: true }],
  '@stylistic/js/function-call-spacing': ['error', 'never'],
  '@stylistic/js/key-spacing': ['error', { beforeColon: false, afterColon: true }],
  '@stylistic/js/keyword-spacing': ['error', { before: true, after: true }],
  '@stylistic/js/no-extra-semi': 'error',
  '@stylistic/js/object-curly-spacing': ['error', 'always'],
  '@stylistic/js/padding-line-between-statements': [
    'error',
    { blankLine: 'always', prev: '*', next: 'return' },
  ],
  '@stylistic/js/quote-props': ['error', 'as-needed'],
  '@stylistic/js/quotes': ['error', 'single', { avoidEscape: true, allowTemplateLiterals: true }],
  '@stylistic/js/semi': 'error',
  '@stylistic/js/space-before-function-paren': ['error', { anonymous: 'always', named: 'never', asyncArrow: 'always' }],
  '@stylistic/js/space-infix-ops': 'error',
  
  '@stylistic/js/dot-location': ['error', 'property'],
  // https://github.com/sindresorhus/eslint-plugin-unicorn/tree/main/docs/rules
  '@unicorn/catch-error-name': [
    'error',
    {
      ignore: [
        '^error\\d*$',
        '^err\\d*$',
        /^ignore/i,
      ],
    },
  ],
  '@unicorn/filename-case': [
    'error',
    {
      case: 'kebabCase',
    },
  ],
  '@unicorn/new-for-builtins': 'error',
  '@unicorn/no-abusive-eslint-disable': 'error',
  '@unicorn/no-array-for-each': 'warn',
  '@unicorn/no-array-method-this-argument': 'error',
  '@unicorn/no-array-push-push': 'error',
  '@unicorn/no-await-in-promise-methods': 'error',
  '@unicorn/no-for-loop': 'warn',
  '@unicorn/no-instanceof-array': 'error',
  '@unicorn/no-new-buffer': 'error',
  '@unicorn/no-static-only-class': 'error',
  '@unicorn/no-thenable': 'error',
  '@unicorn/no-typeof-undefined': 'error',
  '@unicorn/no-unnecessary-await': 'error',
  '@unicorn/no-unnecessary-polyfills': [
    'error',
    {
      targets: 'node > 16',
    },
  ],
  '@unicorn/no-unreadable-iife': 'error',
  '@unicorn/no-useless-fallback-in-spread': 'error',
  '@unicorn/no-useless-length-check': 'error',
  '@unicorn/no-useless-promise-resolve-reject': 'error',
  '@unicorn/no-useless-spread': 'error',
  '@unicorn/numeric-separators-style': ['error',
    {
      onlyIfContainsSeparator: false,
      number: { minimumDigits: 5, groupLength: 3 },
      octal: { minimumDigits: 0, groupLength: 4 },
      hexadecimal: { minimumDigits: 0, groupLength: 4 },
      binary: { minimumDigits: 0, groupLength: 8 },
    },
  ],
  '@unicorn/prefer-array-find': 'error',
  '@unicorn/prefer-array-flat': 'error',
  '@unicorn/prefer-array-flat-map': 'error',
  '@unicorn/prefer-array-index-of': 'error',
  '@unicorn/prefer-array-some': 'error',
  '@unicorn/prefer-at': 'error',
  '@unicorn/prefer-code-point': 'error',
  '@unicorn/prefer-export-from': 'error',
  '@unicorn/prefer-includes': 'error',
  '@unicorn/prefer-json-parse-buffer': 'error',
  '@unicorn/prefer-logical-operator-over-ternary': 'error',
  '@unicorn/prefer-math-trunc': 'error',
  '@unicorn/prefer-modern-math-apis': 'error',
  // '@unicorn/prefer-module': 'error',
  '@unicorn/prefer-negative-index': 'error',
  '@unicorn/prefer-node-protocol': 'error',
  '@unicorn/prefer-number-properties': 'error',
  '@unicorn/prefer-prototype-methods': 'error',
  '@unicorn/prefer-regexp-test': 'error',
  '@unicorn/prefer-set-has': 'error',
  '@unicorn/prefer-set-size': 'error',
  '@unicorn/prefer-string-replace-all': 'error',
  '@unicorn/prefer-string-slice': 'error',
  '@unicorn/prefer-string-trim-start-end': 'error',
  '@unicorn/prefer-ternary': 'error',
  '@unicorn/require-array-join-separator': 'error',
  '@unicorn/require-number-to-fixed-digits-argument': 'error',
  '@unicorn/template-indent': 'error',
  '@unicorn/throw-new-error': 'error',
};
const jsRulesRelaxed = { ...jsRules, '@unicorn/prefer-spread': 'warn' };


module.exports = [
  oxlint.configs['flat/recommended'],
  // oxlint can add some js files for testing - ignore every and each `dist` dir...
  {
    ignores: [
      '**/.yarn/**',
      '**/./**',
      '**/coverage/**',
    ],
  },
  // forbid (in modules---nodenext) usage of .ts files -> .mts should be used instead!
  {
    files: [
      'src/**/*.?mts',
    ],
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        EXPERIMENTAL_useProjectService: {
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 20_000,
        },
      },
    },
    plugins: {
      '@filenames': fileRules,
    },
    rules: {
      '@filenames/filename-blocklist': ['error', {
        '**/*.ts': '*.ts',
      }],
    },
  },
  {
    files: [
      'src/**/*.ts',
      'src/**/*.mts',
    ],
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        EXPERIMENTAL_useProjectService: {
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 20_000,
        },
      },
    },
    plugins: {
      '@typescript-eslint': tsLint,
      '@stylistic/ts': stylisticTs,
      '@stylistic/js': stylisticJs,
      '@unicorn': eslintPluginUnicorn,
    },
    rules: tsRules,
  },
  {
    files: [
      'src/**/*.ts',
      'src/**/*.mts',
    ],
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      'node_modules/**',
      'dist/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        EXPERIMENTAL_useProjectService: {
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 20_000,
        },
      },
    },
    plugins: {
      '@typescript-eslint': tsLint,
      '@stylistic/ts': stylisticTs,
      '@stylistic/js': stylisticJs,
      '@unicorn': eslintPluginUnicorn,
    },
    rules: tsRulesForCommonLib,
  },
  {
    files: ['**/*.js'],
    ignores: [
      '**/.yarn/**',
      '**/node_modules/**',
      '**/dist/**',
      '**/coverage/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        EXPERIMENTAL_useProjectService: {
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 20_000,
        },
      },
    },
    plugins: {
      '@typescript-eslint': tsLint,
      '@stylistic/js': stylisticJs,
      
      '@unicorn': eslintPluginUnicorn,
    },
    rules: jsRules,
  },
  {
    files: ['**/*.mjs'],
    ignores: [
      '**/.yarn/**',
      '**/node_modules/**',
      '**/dist/**',
      '**/coverage/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        EXPERIMENTAL_useProjectService: {
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 20_000,
        },
      },
    },
    plugins: {
      '@typescript-eslint': tsLint,
      '@stylistic/js': stylisticJs,
      
      '@unicorn': eslintPluginUnicorn,
    },
    rules: jsRulesRelaxed,
  },
  {
    files: ['**/*.md'],
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserMd,
    },
    plugins: {
      markdownlint: mdLint2,
    },
    rules: {
      'markdownlint/md001': 'off',
      'markdownlint/md003': 'off',
      'markdownlint/md004': 'error',
      'markdownlint/md005': 'error',
      'markdownlint/md007': 'error',
      'markdownlint/md009': ['error', { list_item_empty_lines: true, strict: true }],
      'markdownlint/md010': 'error',
      'markdownlint/md011': 'error',
      'markdownlint/md012': ['error', { maximum: 5 }],
      'markdownlint/md013': 'off',
      'markdownlint/md014': 'error',
      'markdownlint/md018': 'error',
      'markdownlint/md019': 'error',
      'markdownlint/md020': 'error',
      'markdownlint/md021': 'error',
      'markdownlint/md022': ['error', { lines_above: -1, lines_below: 0 }],
      'markdownlint/md023': 'error',
      'markdownlint/md024': ['warn', { siblings_only: true }],
      'markdownlint/md025': 'off',
      'markdownlint/md026': ['error', { punctuation: '.,;:' }],
      'markdownlint/md027': 'error',
      'markdownlint/md028': 'off',
      'markdownlint/md029': 'error',
      'markdownlint/md030': 'error',
      'markdownlint/md031': ['error', { list_items: false }],
      'markdownlint/md032': 'error',
      'markdownlint/md033': ['error', { allowed_elements: ['details', 'summary'] }],
      'markdownlint/md034': 'error',
      'markdownlint/md035': 'error',
      'markdownlint/md036': 'error',
      'markdownlint/md037': 'error',
      'markdownlint/md038': 'error',
      'markdownlint/md039': 'error',
      'markdownlint/md040': 'error',
      'markdownlint/md041': 'off',
      'markdownlint/md042': 'error',
      'markdownlint/md043': 'warn',
      'markdownlint/md044': 'off',
      'markdownlint/md045': 'warn',
      'markdownlint/md046': 'warn',
      'markdownlint/md047': 'error',
      'markdownlint/md048': 'warn',
      'markdownlint/md049': 'error',
      'markdownlint/md050': 'error',
      // 'markdownlint/md051': 'error',
      // 'markdownlint/md052': 'error',
      // 'markdownlint/md053': 'error',
      'markdownlint/md054': 'off',
      // 'markdownlint/md055': 'error',
      // 'markdownlint/md056': 'error',
    },
  },
  {
    files: ['src/web/**.ts'],
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      'store/**',
    ],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        EXPERIMENTAL_useProjectService: {
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 20_000,
        },
      },
    },
    plugins: {
      '@typescript-eslint': tsLint,
      '@stylistic/ts': stylisticTs,
      '@stylistic/js': stylisticJs,
      '@unicorn': eslintPluginUnicorn,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: tsRulesForWeb,
  },
];
