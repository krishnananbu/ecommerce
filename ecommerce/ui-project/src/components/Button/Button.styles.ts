import styled from 'styled-components';

export const ButtonStyled = styled.button<{ disabled?: boolean }>`
  background-color: ${({ disabled }) => (disabled ? '#ccc' : '#667eea')};
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-size: 1rem;
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({ disabled }) => (disabled ? '#ccc' : '#764ba2')};
  }
`;