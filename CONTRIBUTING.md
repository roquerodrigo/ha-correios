# Contribuindo

Relatos de bug, ideias e pull requests são bem-vindos.

## Relatando um bug

Abra uma [issue](https://github.com/roquerodrigo/ha-correios/issues/new/choose)
com:

- a versão do Home Assistant e a versão da integração;
- o que você fez, o que esperava e o que aconteceu;
- os diagnósticos baixados no menu da integração (o usuário, a senha e os
  códigos de rastreamento são removidos) e as linhas relevantes do log.

## Ambiente de desenvolvimento

O projeto usa o [uv](https://docs.astral.sh/uv/) e o Node.js, este só para
conferir a sintaxe do card.

```bash
scripts/setup      # instala as dependências no .venv
scripts/develop    # executa o Home Assistant em http://localhost:8123 com esta integração carregada
```

O `scripts/develop` usa a configuração em [`config/`](config/), com log de
depuração para a integração.

## Verificações

Execute-as antes de abrir um pull request. O CI executa as mesmas, e o
`scripts/lint` executa todas em sequência. Depois de `pre-commit install`, as
três primeiras rodam a cada commit.

```bash
uv run ruff format .                                          # formatação
uv run ruff check . --fix                                     # lint
uv run mypy custom_components/correios                        # tipos
uv run pytest                                                 # testes, a cobertura precisa ficar em 90 % ou mais
node --check custom_components/correios/www/correios-card.js  # sintaxe do card
```

Leia o [CODE_STYLE.md](CODE_STYLE.md) antes de adicionar ou reestruturar
código.

## Idioma

O repositório é escrito em português do Brasil: documentação, docstrings,
comentários, mensagens de commit, pull requests e issues. O código fica em
inglês (identificadores, nomes de arquivo e de branch, mensagens de log, tipo e
escopo do Conventional Commit), e os termos do domínio (CPF, CNPJ, CEP,
idCorreios) não são traduzidos. A regra completa está na seção "Idioma" do
[CODE_STYLE.md](CODE_STYLE.md).

## Pull requests

1. Faça um fork do repositório e crie a sua branch a partir da `main`.
2. Escreva as mensagens de commit no formato
   [Conventional Commits](https://www.conventionalcommits.org/), por exemplo
   `fix(sensor): corrige a previsão de entrega`. As releases e as notas delas
   são geradas a partir desses commits. Marque as mudanças que quebram
   compatibilidade com `!` ou com o rodapé `BREAKING CHANGE:`.
3. Atualize `translations/en.json` e `translations/pt-BR.json` juntos quando
   mudar textos exibidos ao usuário. As traduções do card ficam no próprio
   `www/correios-card.js`.
4. Atualize o README quando o comportamento, a configuração, as entidades ou o
   card mudarem.
5. Preencha o template de pull request.

## Licença

As contribuições são publicadas sob a [licença MIT](LICENSE) do projeto.
