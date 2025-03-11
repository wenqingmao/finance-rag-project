// import { dirname } from "path";
// import { fileURLToPath } from "url";
// import { FlatCompat } from "@eslint/eslintrc";

// const __filename = fileURLToPath(import.meta.url);
// const __dirname = dirname(__filename);

// const compat = new FlatCompat({
//   baseDirectory: __dirname,
// });

// const eslintConfig = [...compat.extends("next/core-web-vitals")];

// export default eslintConfig;

import next from "@next/eslint-plugin-next";

/** @type {import("eslint").FlatConfig[]} */
const eslintConfig = [
  ...next.configs["core-web-vitals"], // ✅ Uses Next.js' Flat Config directly
];

export default eslintConfig;