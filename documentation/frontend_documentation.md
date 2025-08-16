# Documentação do Frontend FS3M

## 1. Visão Geral do Projeto

O frontend do sistema FS3M é construído com **Next.js**, um framework React para produção que oferece renderização do lado do servidor (SSR), geração de site estático (SSG) e otimização de desempenho. A aplicação utiliza **TypeScript** para tipagem estática, **Tailwind CSS** para estilização rápida e responsiva, e **Axios** para requisições HTTP.

## 2. Estrutura de Diretórios

A estrutura de diretórios do frontend segue as convenções do Next.js, com algumas adições para organização de componentes, utilitários e estilos:

```
frontend/
├── public/                 # Arquivos estáticos (imagens, fontes, etc.)
├── src/
│   ├── app/                # Rotas e páginas da aplicação Next.js
│   │   ├── api/            # Rotas de API (Next.js API Routes)
│   │   ├── (auth)/         # Rotas relacionadas à autenticação
│   │   ├── (dashboard)/    # Rotas principais do dashboard
│   │   └── layout.tsx      # Layouts globais da aplicação
│   ├── components/         # Componentes React reutilizáveis
│   │   ├── ui/             # Componentes de UI genéricos (botões, inputs, etc.)
│   │   └── ...             # Componentes específicos da aplicação
│   ├── lib/                # Funções utilitárias, hooks, configurações da API
│   │   ├── api.ts          # Configuração da instância Axios para a API
│   │   ├── auth.ts         # Funções relacionadas à autenticação
│   │   └── utils.ts        # Funções utilitárias diversas
│   ├── styles/             # Arquivos de estilo globais ou específicos
│   │   └── globals.css     # Estilos globais (Tailwind CSS base)
│   └── types/              # Definições de tipos TypeScript
│       └── index.d.ts      # Tipos globais da aplicação
├── .env.example            # Exemplo de variáveis de ambiente
├── next.config.mjs         # Configuração do Next.js
├── package.json            # Dependências e scripts do projeto
├── postcss.config.mjs      # Configuração do PostCSS
├── tailwind.config.ts      # Configuração do Tailwind CSS
├── tsconfig.json           # Configuração do TypeScript
└── ...
```

## 3. Principais Dependências

As principais dependências do projeto, conforme `package.json`, incluem:

- **`next`**: O framework React para construção da aplicação.
- **`react`**, **`react-dom`**: Bibliotecas essenciais para a interface do usuário.
- **`axios`**: Cliente HTTP para fazer requisições à API do backend.
- **`clsx`**: Utilitário para construir `className` strings condicionalmente.
- **`lucide-react`**, **`react-icons`**: Bibliotecas de ícones.
- **`next-themes`**: Para gerenciamento de temas (claro/escuro).
- **`recharts`**: Biblioteca para criação de gráficos.
- **`swr`**: Hook React para busca de dados com cache e revalidação.

## 4. Como Rodar o Projeto

Para rodar o projeto frontend localmente, siga os passos:

1.  **Instalar Dependências:**
    ```bash
    npm install
    # ou yarn install
    # ou pnpm install
    ```

2.  **Configurar Variáveis de Ambiente:** Crie um arquivo `.env.local` na raiz do projeto (baseado no `.env.example`) e configure as variáveis necessárias, como a URL da API do backend.

    Exemplo de `.env.local`:
    ```
    NEXT_PUBLIC_API_URL=http://localhost:8000/api
    ```

3.  **Iniciar o Servidor de Desenvolvimento:**
    ```bash
    npm run dev
    ```

    A aplicação estará disponível em `http://localhost:3000`.

## 5. Testes

Atualmente, o projeto não possui uma configuração explícita para testes unitários ou de integração no `package.json`. No entanto, a estrutura do Next.js e a utilização de TypeScript facilitam a integração com ferramentas de teste como **Jest** e **React Testing Library**.

### 5.1. Configuração Sugerida para Testes

Para adicionar testes ao projeto, os seguintes passos são recomendados:

1.  **Instalar Dependências de Teste:**
    ```bash
    npm install --save-dev jest @testing-library/react @testing-library/jest-dom @types/jest babel-jest
    ```

2.  **Configurar Jest:** Crie um arquivo `jest.config.js` na raiz do projeto:

    ```javascript
    // jest.config.js
    const nextJest = require('next/jest');

    const createJestConfig = nextJest({
      dir: './',
    });

    const customJestConfig = {
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
      moduleNameMapper: {
        '^@/components/(.*)$': '<rootDir>/src/components/$1',
        '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
        '^@/app/(.*)$': '<rootDir>/src/app/$1',
      },
      testEnvironment: 'jest-environment-jsdom',
    };

    module.exports = createJestConfig(customJestConfig);
    ```

3.  **Configurar `jest.setup.js`:** Crie este arquivo para importações globais e configurações do Jest.

    ```javascript
    // jest.setup.js
    import '@testing-library/jest-dom/extend-expect';
    ```

4.  **Adicionar Scripts de Teste ao `package.json`:**

    ```json
    {
      "scripts": {
        "test": "jest",
        "test:watch": "jest --watch"
      }
    }
    ```

### 5.2. Exemplos de Testes

Com a configuração acima, você pode criar arquivos de teste (ex: `*.test.tsx` ou `*.spec.tsx`) ao lado dos componentes ou funções que deseja testar.

Exemplo de teste para um componente simples (`src/components/ui/Button.tsx`):

```typescript
// src/components/ui/Button.test.tsx
import { render, screen } from '@testing-library/react';
import Button from './Button';

describe('Button', () => {
  it('renders a button with the correct text', () => {
    render(<Button>Click me</Button>);
    const buttonElement = screen.getByText(/click me/i);
    expect(buttonElement).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    screen.getByText(/click me/i).click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

Esta documentação será entregue ao final do processo.

