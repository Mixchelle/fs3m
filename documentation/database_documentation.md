# Documentação do Banco de Dados FS3M

## 1. Visão Geral

O banco de dados do sistema FS3M é modelado usando o Django ORM, que mapeia objetos Python para tabelas de banco de dados. As definições dos modelos estão localizadas nos arquivos `models.py` dentro de cada aplicação Django. O sistema utiliza um banco de dados PostgreSQL, conforme configurado no `docker-compose.yml`.

## 2. Modelos e Tabelas

Abaixo, detalhamos os principais modelos (e suas correspondentes tabelas) e seus campos, com base na análise dos arquivos `models.py`:

### Aplicação `users`

Gerencia usuários e autenticação. A tabela principal é `users_user`.

| Campo             | Tipo de Dados (Django) | Descrição                                        |
|-------------------|------------------------|--------------------------------------------------|
| `id`              | `AutoField`            | Chave primária, auto-incremento.                 |
| `password`        | `CharField`            | Hash da senha do usuário.                        |
| `last_login`      | `DateTimeField`        | Data e hora do último login.                     |
| `is_superuser`    | `BooleanField`         | Indica se o usuário tem todas as permissões.     |
| `username`        | `CharField`            | Nome de usuário único.                           |
| `first_name`      | `CharField`            | Primeiro nome do usuário.                        |
| `last_name`       | `CharField`            | Sobrenome do usuário.                            |
| `email`           | `EmailField`           | Endereço de e-mail, único.                       |
| `is_staff`        | `BooleanField`         | Indica se o usuário pode acessar o admin site.   |
| `is_active`       | `BooleanField`         | Indica se a conta do usuário está ativa.         |
| `date_joined`     | `DateTimeField`        | Data e hora de criação da conta.                 |
| `role`            | `CharField`            | Papel do usuário (cliente, subcliente, analista, gestor). |
| `empresas`        | `CharField`            | Empresas associadas ao usuário (pode ser nulo).  |
| `cliente`         | `ForeignKey` (`User`)  | Cliente ao qual o usuário está associado (para subclientes). |
| `gestor_referente`| `ForeignKey` (`User`)  | Gestor referente ao usuário (pode ser nulo).     |
| `formularios_ids` | `JSONField`            | IDs de formulários associados (lista de inteiros). |
| `is_2fa_enabled`  | `BooleanField`         | Indica se a autenticação de dois fatores está ativada. |
| `otp_secret`      | `CharField`            | Segredo para 2FA (pode ser nulo).                |
| `otp_backup_codes`| `JSONField`            | Códigos de backup para 2FA (lista de strings, pode ser nulo). |

### Aplicação `frameworks`

Define estruturas de avaliação, domínios, controles e questões. As tabelas principais são `frameworks_framework`, `frameworks_domain`, `frameworks_control`, `frameworks_question`, `frameworks_choiceoption`, `frameworks_scoringmodel`, `frameworks_formtemplate`, `frameworks_templateitem`, `frameworks_controlmapping`.

#### `frameworks_framework`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `slug`        | `SlugField`            | Identificador único amigável para URLs.          |
| `name`        | `CharField`            | Nome da estrutura de avaliação.                  |
| `version`     | `CharField`            | Versão da estrutura.                             |
| `description` | `TextField`            | Descrição detalhada da estrutura.                |
| `active`      | `BooleanField`         | Indica se a estrutura está ativa.                |
| `editable`    | `BooleanField`         | Indica se a estrutura pode ser editada.          |
| `created_at`  | `DateTimeField`        | Data e hora de criação.                          |
| `updated_at`  | `DateTimeField`        | Data e hora da última atualização.               |

#### `frameworks_domain`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `framework_id`| `ForeignKey`           | Chave estrangeira para `frameworks_framework`.   |
| `code`        | `CharField`            | Código do domínio.                               |
| `title`       | `CharField`            | Título do domínio.                               |
| `parent_id`   | `ForeignKey`           | Chave estrangeira para `frameworks_domain` (auto-referência para hierarquia). |
| `order`       | `IntegerField`         | Ordem de exibição.                               |

#### `frameworks_control`

| Campo             | Tipo de Dados (Django) | Descrição                                        |
|-------------------|------------------------|--------------------------------------------------|
| `id`              | `AutoField`            | Chave primária.                                  |
| `framework_id`    | `ForeignKey`           | Chave estrangeira para `frameworks_framework`.   |
| `domain_id`       | `ForeignKey`           | Chave estrangeira para `frameworks_domain`.      |
| `code`            | `CharField`            | Código do controle.                              |
| `title`           | `CharField`            | Título do controle.                              |
| `description`     | `TextField`            | Descrição detalhada do controle.                 |
| `order`           | `IntegerField`         | Ordem de exibição.                               |
| `active`          | `BooleanField`         | Indica se o controle está ativo.                 |
| `scoring_model_id`| `ForeignKey`           | Chave estrangeira para `frameworks_scoringmodel`.|

#### `frameworks_question`

| Campo             | Tipo de Dados (Django) | Descrição                                        |
|-------------------|------------------------|--------------------------------------------------|
| `id`              | `AutoField`            | Chave primária.                                  |
| `control_id`      | `ForeignKey`           | Chave estrangeira para `frameworks_control`.     |
| `local_code`      | `CharField`            | Código local da questão.                         |
| `prompt`          | `CharField`            | Texto da questão.                                |
| `type`            | `CharField`            | Tipo da questão (text, number, boolean, single, multiple, scale, json, file). |
| `required`        | `BooleanField`         | Indica se a questão é obrigatória.               |
| `order`           | `IntegerField`         | Ordem de exibição.                               |
| `meta`            | `JSONField`            | Metadados adicionais em formato JSON.            |
| `scoring_model_id`| `ForeignKey`           | Chave estrangeira para `frameworks_scoringmodel`.|

#### `frameworks_choiceoption`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `question_id` | `ForeignKey`           | Chave estrangeira para `frameworks_question`.    |
| `label`       | `CharField`            | Rótulo da opção.                                 |
| `value`       | `CharField`            | Valor da opção.                                  |
| `weight`      | `DecimalField`         | Peso da opção para pontuação.                    |
| `order`       | `IntegerField`         | Ordem de exibição.                               |
| `active`      | `BooleanField`         | Indica se a opção está ativa.                    |

#### `frameworks_scoringmodel`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `name`        | `CharField`            | Nome do modelo de pontuação.                     |
| `slug`        | `SlugField`            | Identificador único amigável.                    |
| `mapping`     | `JSONField`            | Mapeamento de pontuação em formato JSON.         |
| `rules`       | `JSONField`            | Regras de pontuação em formato JSON.             |

#### `frameworks_formtemplate`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `name`        | `CharField`            | Nome do modelo de formulário.                    |
| `slug`        | `SlugField`            | Identificador único amigável.                    |
| `framework_id`| `ForeignKey`           | Chave estrangeira para `frameworks_framework`.   |
| `version`     | `CharField`            | Versão do modelo.                                |
| `description` | `TextField`            | Descrição detalhada.                             |
| `active`      | `BooleanField`         | Indica se o modelo está ativo.                   |
| `editable`    | `BooleanField`         | Indica se o modelo pode ser editado.             |
| `created_at`  | `DateTimeField`        | Data e hora de criação.                          |
| `updated_at`  | `DateTimeField`        | Data e hora da última atualização.               |

#### `frameworks_templateitem`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `template_id` | `ForeignKey`           | Chave estrangeira para `frameworks_formtemplate`.|
| `control_id`  | `ForeignKey`           | Chave estrangeira para `frameworks_control`.     |
| `question_id` | `ForeignKey`           | Chave estrangeira para `frameworks_question` (pode ser nulo). |
| `order`       | `IntegerField`         | Ordem de exibição.                               |

#### `frameworks_controlmapping`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `origin_id`   | `ForeignKey`           | Chave estrangeira para `frameworks_control` (controle de origem). |
| `target_id`   | `ForeignKey`           | Chave estrangeira para `frameworks_control` (controle de destino). |
| `weight`      | `DecimalField`         | Peso do mapeamento.                              |
| `note`        | `TextField`            | Notas sobre o mapeamento.                        |

### Aplicação `assessments`

Gerencia as avaliações. A tabela principal é `assessments_assessment`.

#### `assessments_assessment`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `submission_id`| `ForeignKey`           | Chave estrangeira para `responses_submission`.   |
| `framework_id`| `ForeignKey`           | Chave estrangeira para `frameworks_framework`.   |
| `status`      | `CharField`            | Status da avaliação (Rascunho, Em Progresso, Concluído, Arquivado). |
| `start_date`  | `DateTimeField`        | Data e hora de início da avaliação.              |
| `end_date`    | `DateTimeField`        | Data e hora de término da avaliação (pode ser nulo). |

### Aplicação `responses`

Armazena as respostas das avaliações. As tabelas principais são `responses_submission` e `responses_answer`.

#### `responses_submission`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `client_id`   | `ForeignKey`           | Chave estrangeira para `users_user` (cliente que realizou a submissão). |
| `framework_id`| `ForeignKey`           | Chave estrangeira para `frameworks_framework`.   |
| `start_date`  | `DateTimeField`        | Data e hora de início da submissão.              |
| `end_date`    | `DateTimeField`        | Data e hora de término da submissão (pode ser nulo). |
| `status`      | `CharField`            | Status da submissão.                             |
| `created_at`  | `DateTimeField`        | Data e hora de criação.                          |
| `updated_at`  | `DateTimeField`        | Data e hora da última atualização.               |

#### `responses_answer`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `submission_id`| `ForeignKey`           | Chave estrangeira para `responses_submission`.   |
| `question_id` | `ForeignKey`           | Chave estrangeira para `frameworks_question`.    |
| `value`       | `CharField`            | Valor da resposta.                               |
| `meta`        | `JSONField`            | Metadados adicionais em formato JSON.            |
| `created_at`  | `DateTimeField`        | Data e hora de criação.                          |
| `updated_at`  | `DateTimeField`        | Data e hora da última atualização.               |

### Aplicação `actionplans`

Gerencia planos de ação. A tabela principal é `actionplans_actionplan`.

#### `actionplans_actionplan`

| Campo         | Tipo de Dados (Django) | Descrição                                        |
|---------------|------------------------|--------------------------------------------------|
| `id`          | `AutoField`            | Chave primária.                                  |
| `client_id`   | `ForeignKey`           | Chave estrangeira para `users_user`.             |
| `created_by_id`| `ForeignKey`           | Chave estrangeira para `users_user` (usuário que criou o plano). |
| `observations`| `TextField`            | Observações sobre o plano de ação.               |
| `due_date`    | `CharField`            | Prazo para conclusão.                            |
| `severity`    | `CharField`            | Gravidade do plano.                              |
| `urgency`     | `CharField`            | Urgência do plano.                               |
| `category`    | `CharField`            | Categoria do plano.                              |
| `max_budget`  | `CharField`            | Orçamento máximo.                                |
| `submission_id`| `ForeignKey`           | Chave estrangeira para `responses_submission` (pode ser nulo). |
| `created_at`  | `DateTimeField`        | Data e hora de criação.                          |
| `updated_at`  | `DateTimeField`        | Data e hora da última atualização.               |

#### `actionplans_actionplan_recommendations` (Tabela intermediária para M2M)

| Campo               | Tipo de Dados (Django) | Descrição                                        |
|---------------------|------------------------|--------------------------------------------------|
| `id`                | `AutoField`            | Chave primária.                                  |
| `actionplan_id`     | `ForeignKey`           | Chave estrangeira para `actionplans_actionplan`. |
| `recommendation_id` | `ForeignKey`           | Chave estrangeira para `recommendations_recommendation`. |

### Aplicação `recommendations`

Gerencia recomendações. A tabela principal é `recommendations_recommendation`.

#### `recommendations_recommendation`

| Campo                 | Tipo de Dados (Django) | Descrição                                        |
|-----------------------|------------------------|--------------------------------------------------|
| `id`                  | `AutoField`            | Chave primária.                                  |
| `title`               | `CharField`            | Título da recomendação.                          |
| `description`         | `TextField`            | Descrição detalhada da recomendação.             |
| `priority`            | `CharField`            | Prioridade da recomendação.                      |
| `applicability`       | `CharField`            | Aplicabilidade da recomendação.                  |
| `category`            | `CharField`            | Categoria da recomendação.                       |
| `recommended_due_date`| `CharField`            | Prazo recomendado (pode ser nulo).                |
| `required_resources`  | `TextField`            | Recursos necessários (pode ser nulo).            |
| `observations`        | `TextField`            | Observações adicionais (pode ser nulo).          |
| `data_criacao`        | `DateTimeField`        | Data e hora de criação.                          |
| `data_atualizacao`    | `DateTimeField`        | Data e hora da última atualização.               |

Esta documentação será entregue ao final do processo.




## 3. Documentação da API

A documentação da API do backend FS3M é gerada automaticamente a partir do código-fonte usando o `drf-spectacular`, seguindo o padrão OpenAPI 3.0. Isso permite que a API seja facilmente explorada e integrada por outros sistemas.

### 3.1. Especificação OpenAPI (YAML)

O arquivo `openapi_schema.yaml` é a fonte de verdade para a definição da API. Ele descreve todos os endpoints, métodos HTTP suportados, parâmetros de requisição, modelos de dados (schemas), tipos de autenticação e possíveis respostas. Este arquivo é essencial para ferramentas de desenvolvimento, como geradores de clientes de API e validadores.

[Download da Especificação OpenAPI (YAML)](/home/ubuntu/fs3m/backend/openapi_schema.yaml)

### 3.2. Documentação Interativa (Redoc)

Para uma visualização mais amigável e interativa da API, foi gerado um arquivo HTML estático utilizando o Redoc. Este arquivo (`redoc-static.html`) apresenta a documentação da API de forma clara e navegável, com exemplos de requisições e respostas, facilitando o entendimento e o uso da API por desenvolvedores.

[Visualizar Documentação Interativa (Redoc)](/home/ubuntu/fs3m/backend/redoc-static.html)

### 3.3. Principais Endpoints e Funcionalidades

A API é organizada por módulos, refletindo as aplicações Django do backend. Abaixo, uma visão geral dos principais grupos de endpoints:

-   **/api/auth/**: Endpoints relacionados à autenticação de usuários, incluindo login (`/api/auth/token/`), refresh de token (`/api/auth/token/refresh/`), verificação de token (`/api/auth/token/verify/`), logout (`/api/auth/logout/`) e gerenciamento do perfil do usuário logado (`/api/auth/me/`).

-   **/api/users/**: Gerenciamento de usuários, permitindo listar, criar, recuperar, atualizar e deletar usuários, além de ativar/desativar contas.

-   **/api/frameworks/**: Gerenciamento de estruturas de avaliação, domínios, controles, questões, modelos de pontuação e templates de formulário. Inclui endpoints para:
    -   `/api/frameworks/frameworks/`: Operações CRUD para Frameworks.
    -   `/api/frameworks/domains/`: Operações CRUD para Domínios.
    -   `/api/frameworks/controls/`: Operações CRUD para Controles.
    -   `/api/frameworks/questions/`: Operações CRUD para Questões.
    -   `/api/frameworks/scoring-models/`: Operações CRUD para Modelos de Pontuação.
    -   `/api/frameworks/templates/`: Operações CRUD para Templates de Formulário.
    -   `/api/frameworks/control-mappings/`: Operações CRUD para Mapeamentos de Controle.

-   **/api/assessments/**: Endpoints relacionados à execução de avaliações, como `/api/assessments/run/{submission_id}/` para iniciar uma avaliação.

-   **/api/responses/**: Gerenciamento de submissões de avaliações e respostas individuais. Inclui endpoints para:
    -   `/api/responses/submissions/`: Operações CRUD para Submissões.
    -   `/api/responses/answers/`: Operações CRUD para Respostas.

-   **/api/planos/**: Gerenciamento de planos de ação, com operações CRUD para criar, listar, recuperar, atualizar e deletar planos.

-   **/api/recommendations/**: Gerenciamento de recomendações, com operações CRUD para criar, listar, recuperar, atualizar e deletar recomendações.

Esta documentação será entregue ao final do processo.

