# Evermat — Balanço de Massa & Energia V2.1 Web

Versão pronta para uso no navegador via Streamlit Community Cloud.

## Publicar sem instalar nada no computador
1. Crie uma conta no GitHub: https://github.com/
2. Crie um repositório **Private**, por exemplo `evermat-balanco`.
3. Envie `app.py`, `requirements.txt`, `defaults.json` e a pasta `.streamlit` (somente `config.toml`; não publique senha real).
4. Acesse https://streamlit.io/cloud e entre com GitHub.
5. Crie um app apontando para o repositório, branch `main`, arquivo `app.py`.
6. Em **Settings > Secrets**, configure:

```toml
APP_PASSWORD = "sua-senha-forte-aqui"
```

7. Abra o endereço `*.streamlit.app` gerado.

## Segurança
O login desta versão é uma senha única de aplicação. Para uso corporativo mais amplo, o ideal é evoluir para autenticação individual/SSO e política de acesso da empresa.

## Novidades da V2.1
- Login por senha via Secrets.
- Pronto para Streamlit Cloud.
- Exportação de snapshot CSV.
- Mantém PFD, balanços, cenários e qualidade dos dados.
