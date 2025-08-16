# Documentação do Backend FS3M

## 1. Documentação da API (Swagger/Redoc)

A API do backend FS3M é documentada usando o padrão OpenAPI 3.0, permitindo a geração automática de interfaces interativas como Swagger UI e Redoc.

- **Especificação OpenAPI:** O arquivo `openapi_schema.yaml` contém a definição completa de todos os endpoints, modelos de dados, autenticação e operações da API. Este arquivo pode ser utilizado para gerar clientes de API, realizar validações e explorar a estrutura da API.

  [Download openapi_schema.yaml](/home/ubuntu/fs3m/backend/openapi_schema.yaml)

- **Documentação Interativa (Redoc):** Uma versão estática e interativa da documentação da API, gerada com Redoc, está disponível no arquivo `redoc-static.html`. Esta interface oferece uma visualização amigável e navegável de todos os recursos da API.

  [Visualizar redoc-static.html](/home/ubuntu/fs3m/backend/redoc-static.html)

## 2. Estrutura do Banco de Dados

O backend do FS3M utiliza o Django ORM para gerenciar a estrutura do banco de dados. As definições dos modelos estão localizadas nos arquivos `models.py` dentro de cada aplicação Django. Abaixo, um resumo da estrutura das principais aplicações:

### `users`

Gerencia usuários e autenticação.

- **User:** Modelo principal para usuários, com campos como `email`, `username`, `first_name`, `last_name`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`, `role`, `empresas`, `cliente`, `gestor_referente`, `formularios_ids`, `is_2fa_enabled`, `otp_secret`, `otp_backup_codes`.

### `frameworks`

Define estruturas de avaliação, domínios, controles e questões.

- **Framework:** Representa uma estrutura de avaliação (ex: ISO 27001, LGPD). Campos incluem `name`, `slug`, `version`, `description`, `active`, `editable`.
- **Domain:** Categorias ou áreas dentro de um framework. Campos: `framework` (FK), `code`, `title`, `parent` (FK para Domain, para hierarquia), `order`.
- **Control:** Controles específicos dentro de um domínio. Campos: `framework` (FK), `domain` (FK), `code`, `title`, `description`, `order`, `active`, `scoring_model` (FK).
- **Question:** Questões associadas a controles. Campos: `control` (FK), `local_code`, `prompt`, `type` (text, number, boolean, single, multiple, scale, json, file), `required`, `order`, `meta` (JSONField), `scoring_model` (FK).
- **ChoiceOption:** Opções para questões de múltipla escolha. Campos: `question` (FK), `label`, `value`, `weight`, `order`, `active`.
- **ScoringModel:** Modelos de pontuação para questões/controles. Campos: `name`, `slug`, `mapping` (JSONField), `rules` (JSONField).
- **FormTemplate:** Modelos de formulários. Campos: `name`, `slug`, `framework` (FK), `version`, `description`, `active`, `editable`.
- **TemplateItem:** Itens dentro de um FormTemplate, ligando a controles e questões. Campos: `template` (FK), `control` (FK), `question` (FK), `order`.
- **ControlMapping:** Mapeamento entre controles de diferentes frameworks. Campos: `origin` (FK para Control), `target` (FK para Control), `weight`, `note`.

### `assessments`

Gerencia as avaliações.

- **Assessment:** Representa uma avaliação. Campos: `submission` (FK), `framework` (FK), `status`, `start_date`, `end_date`.

### `responses`

Armazena as respostas das avaliações.

- **Submission:** Uma submissão de avaliação. Campos: `client` (FK para User), `framework` (FK), `start_date`, `end_date`, `status`.
- **Answer:** Respostas individuais para questões. Campos: `submission` (FK), `question` (FK), `value`, `meta` (JSONField).

### `actionplans`

Gerencia planos de ação.

- **ActionPlan:** Planos de ação. Campos: `client` (FK para User), `created_by` (FK para User), `observations`, `due_date`, `severity`, `urgency`, `category`, `max_budget`, `submission` (FK), `recommendations` (M2M para Recommendation).

### `recommendations`

Gerencia recomendações.

- **Recommendation:** Recomendações. Campos: `title`, `description`, `priority`, `applicability`, `category`, `recommended_due_date`, `required_resources`, `observations`.

Esta documentação será entregue ao final do processo.

