// src/types/index.ts

export interface ButtonProps {
    label: string;
    onClick: () => void;
    disabled?: boolean;
}

export interface FormProps {
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
    children: React.ReactNode;
}