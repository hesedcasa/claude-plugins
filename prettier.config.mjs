export default {
  plugins: ["prettier-plugin-sh"],
  overrides: [
    {
      files: ["*.js", "*.mjs", "*.cjs"],
      options: {
        semi: true,
        singleQuote: false,
        printWidth: 120,
      },
    },
    {
      files: ["*.sh"],
      options: {
        printWidth: 120,
      },
    },
  ],
};
