# Evermat — Balanço de Massa & Energia V4

Versão focada no motor interativo Milho → Beer.

## Mudança principal
Em **Simulação física**, a vazão de Beer deixa de ser independente. Ela é calculada a partir de:
- moagem;
- umidade do milho;
- amido em base seca;
- conversão;
- eficiência fermentativa;
- sólidos alvo na Beer;
- densidade da Beer.

Em **Operação Real**, Beer e sólidos continuam como medições independentes para permitir verificar o fechamento real.

## Atualização no Streamlit
Suba a pasta `evermat_balance_v4_web` no mesmo repositório e altere Main file path para:
`evermat_balance_v4_web/app.py`

## Limites atuais
Proteína, fibra, óleo e cinzas ainda estão agregados em sólidos residuais. Não são inventadas correntes faltantes.
