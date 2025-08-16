# FS3M - Framework Security Maturity Management

Sistema de gestão de maturidade de segurança baseado em frameworks como NIST CSF, CIS Controls, ISO 27001, etc.

## Arquitetura

- **Backend**: Django REST Framework com PostgreSQL
- **Frontend**: Next.js 15 com React 19
- **Containerização**: Docker e Docker Compose

## Pré-requisitos

- Docker e Docker Compose
- Node.js 20+ (para desenvolvimento local)
- Python 3.11+ (para desenvolvimento local)

## Execução com Docker

### Desenvolvimento

```bash
# Clonar o repositório
git clone <repository-url>
cd fs3m

# Executar com Docker Compose
docker-compose up --build

# Acessar a aplicação
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Documentação da API: http://localhost:8000/api/docs/
```

### Produção

```bash
# Executar em modo de produção
docker-compose -f docker-compose.prod.yml up --build -d

# Acessar a aplicação
# Frontend: http://localhost (via Nginx)
# Backend API: http://localhost/api/
```

## Desenvolvimento Local

### Backend (Django)

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
python manage.py migrate

# Executar servidor de desenvolvimento
python manage.py runserver
```

### Frontend (Next.js)

```bash
cd frontend

# Instalar dependências
npm install

# Executar servidor de desenvolvimento
npm run dev
```

## Testes

### Backend

```bash
cd backend
python manage.py test
```

### Frontend

```bash
cd frontend
npm test
```

## Estrutura do Projeto

```
fs3m/
├── backend/                 # Backend Django
│   ├── config/             # Configurações do Django
│   ├── users/              # App de usuários
│   ├── frameworks/         # App de frameworks de segurança
│   ├── assessments/        # App de avaliações
│   ├── actionplans/        # App de planos de ação
│   └── requirements.txt    # Dependências Python
├── frontend/               # Frontend Next.js
│   ├── src/
│   │   ├── app/           # App Router do Next.js
│   │   ├── components/    # Componentes React
│   │   ├── services/      # Serviços de API
│   │   └── types/         # Tipos TypeScript
│   └── package.json       # Dependências Node.js
├── docker-compose.yml      # Configuração Docker para desenvolvimento
├── docker-compose.prod.yml # Configuração Docker para produção
└── nginx.conf             # Configuração Nginx para produção
```

## Funcionalidades

- **Gestão de Usuários**: Autenticação, autorização e perfis de usuário
- **Frameworks de Segurança**: Suporte a múltiplos frameworks (NIST CSF, CIS Controls, etc.)
- **Avaliações**: Criação e execução de avaliações de maturidade
- **Planos de Ação**: Geração e acompanhamento de planos de melhoria
- **Dashboard**: Visualização de métricas e progresso
- **API REST**: Interface completa para integração

## Variáveis de Ambiente

### Produção

Crie um arquivo `.env` na raiz do projeto:

```env
# Banco de dados
POSTGRES_PASSWORD=sua_senha_segura

# Django
SECRET_KEY=sua_chave_secreta_django
ALLOWED_HOSTS=seu-dominio.com,localhost

# Frontend
NEXT_PUBLIC_API_URL=https://seu-dominio.com
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
