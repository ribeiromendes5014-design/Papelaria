# Papelaria Papelaria (Tenant como perfil)

Essa base agora replica o modelo do sistema de agendamentos: cada papelaria (tenant) é um perfil atrelado a um único usuário (`tenants.TenantProfile`), todos os dados ficam em um único schema e o middleware `TenantMiddleware` popula `request.tenant` automaticamente.

## Configuração inicial
1. Crie um virtualenv: `python -m venv .venv`
2. Ative e instale as dependências: `pip install -r requirements.txt`
3. Configure o PostgreSQL no `papelaria_multi/settings.py` com o host/usuário/senha desejado.
4. Ajuste `SECRET_KEY` e mantenha `DEBUG = True` apenas no desenvolvimento.
5. Rode `python manage.py migrate` para criar todas as tabelas, incluindo `TenantProfile`.
6. Use `python manage.py createsuperuser` (se ainda não existir) para gerenciar tenants pelo admin.

## Workflow do tenant
- Crie um usuário (ou use um existente) e vincule um `TenantProfile` via `/admin/tenants/tenantprofile/`.
- Preencha slug, nome da papelaria e WhatsApp no perfil. Esse slug pode ser usado para distinguir visualmente cada tenant. O tenant pode ser ativado/desativado pela data de expiração (`access_end_date`).
- O login funciona normalmente em `/login/`; o backend aceita o email do usuário pelo campo “E-mail”.
- O middleware garante que, ao navegar, `request.tenant` esteja disponível para todas as views e templates.
- Os apps `pedidos`, `produtos` e `catalogo` já filtram dados usando o `tenant` corrente.

## Estrutura dos apps
- **core**: Onboarding e tela de boas-vindas (atualiza nome e WhatsApp do tenant).
- **pedidos**: Tela principal de pedidos (apenas os do tenant logado).
- **produtos**: CRUD de produtos/categorias da papelaria atual.
- **catalogo**: Vitrine filtrada pelo tenant, com carrinho e checkout placeholders.

## Performance
- Prefetchs em catálogo/listas para evitar N+1 (variacoes__categoria, imagens, categoria/subcategoria).
- Cache de 30s na lista pública do catálogo por tenant.
- Índices extras: Produto (tenant+ativo, categoria, subcategoria), Variacao (produto), Categoria/Subcategoria (tenant).

## Próximos passos
1. Implementar rotas públicas que exibem o catálogo do tenant com base no slug.
2. Criar testes automatizados que garantam que o isolamento por `tenant` funciona no mesmo banco.
3. Estender o onboarding com notificações, lembretes ou integração com ferramentas externas (WebPush, WhatsApp, etc.).
