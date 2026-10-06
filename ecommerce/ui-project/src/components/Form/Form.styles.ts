import styled from 'styled-components';

export const FormContainer = styled.form`
    display: flex;
    flex-direction: column;
    padding: 20px;
    border-radius: 8px;
    background-color: #f9f9f9;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
`;

export const FormTitle = styled.h2`
    margin-bottom: 20px;
    font-size: 1.5rem;
    color: #333;
`;

export const FormGroup = styled.div`
    margin-bottom: 15px;
`;

export const FormLabel = styled.label`
    margin-bottom: 5px;
    font-weight: 600;
    color: #555;
`;

export const FormInput = styled.input`
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
    &:focus {
        border-color: #667eea;
        outline: none;
        box-shadow: 0 0 5px rgba(102, 126, 234, 0.5);
    }
`;

export const FormButton = styled.button`
    padding: 10px;
    background-color: #667eea;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.3s;
    &:hover {
        background-color: #764ba2;
    }
`;