# ui-project

This project is a user interface section developed using React and TypeScript. It includes reusable components, global styles, and utility functions to facilitate the development of a modern web application.

## Project Structure

```
ui-project
├── src
│   ├── components
│   │   ├── Button
│   │   │   ├── Button.tsx
│   │   │   ├── Button.styles.ts
│   │   │   └── Button.test.tsx
│   │   ├── Form
│   │   │   ├── Form.tsx
│   │   │   ├── Form.styles.ts
│   │   │   └── Form.test.tsx
│   │   └── shared
│   │       └── index.ts
│   ├── styles
│   │   ├── global.css
│   │   ├── theme.ts
│   │   └── variables.ts
│   ├── utils
│   │   └── index.ts
│   └── types
│       └── index.ts
├── package.json
├── tsconfig.json
└── README.md
```

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ui-project
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the application:**
   ```bash
   npm start
   ```

## Components

- **Button**: A reusable button component that accepts `label`, `onClick`, and `disabled` props.
- **Form**: A reusable form component that accepts `onSubmit` and `children` props.

## Styles

- Global styles are defined in `src/styles/global.css`.
- The theme and design tokens are managed in `src/styles/theme.ts` and `src/styles/variables.ts`.

## Utilities

Utility functions can be found in `src/utils/index.ts`.

## Types

TypeScript types and interfaces are defined in `src/types/index.ts`.

## License

This project is licensed under the MIT License.