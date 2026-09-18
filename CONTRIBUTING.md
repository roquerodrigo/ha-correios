# Diretrizes de contribuição

Contribuir com este projeto deve ser o mais fácil e transparente possível, seja para:

- Reportar um bug
- Discutir o estado atual do código
- Enviar uma correção
- Propor novas funcionalidades

## O GitHub é usado para tudo

O GitHub é usado para hospedar o código, acompanhar issues e pedidos de funcionalidade e receber pull requests.

Pull requests são a melhor forma de propor mudanças no código.

1. Faça um fork do repositório e crie a sua branch a partir da `main`.
2. Se você alterou algo, atualize a documentação.
3. Garanta que o código passa no lint (execute `uv run ruff format --check .`, `uv run ruff check .` e `uv run mypy custom_components/correios`).
4. Teste a sua contribuição.
5. Abra o pull request!

## Idioma

O idioma do repositório é o **português do Brasil**: documentação, docstrings, comentários, mensagens de commit, pull requests e issues. O código (identificadores, nomes de arquivo e de branch, mensagens de log, tipo e escopo do Conventional Commit) fica em inglês, e os termos nativos do domínio (CPF, CNPJ, CEP, idCorreios) nunca são traduzidos. A regra completa está na seção "Idioma" do [`CODE_STYLE.md`](./CODE_STYLE.md).

## Toda contribuição fica sob a licença MIT

Em resumo, ao enviar alterações de código, entende-se que elas ficam sob a mesma [licença MIT](http://choosealicense.com/licenses/mit/) que cobre o projeto. Entre em contato com os mantenedores se isso for uma preocupação.

## Reporte bugs pelas [issues](../../issues) do GitHub

As issues do GitHub são usadas para acompanhar os bugs públicos.
Reporte um bug [abrindo uma nova issue](../../issues/new/choose); é simples assim!

## Escreva relatos de bug com detalhes, contexto e código de exemplo

**Bons relatos de bug** costumam ter:

- Um resumo rápido e/ou o contexto
- Passos para reproduzir
  - Seja específico!
  - Forneça código de exemplo, se puder.
- O que você esperava que acontecesse
- O que acontece de fato
- Observações (incluindo, se possível, por que você acha que isso acontece ou o que você tentou e não funcionou)

## Use um estilo de código consistente

O projeto usa o [ruff](https://docs.astral.sh/ruff/) (configuração no `pyproject.toml`). Execute `uv run ruff format --check .`, `uv run ruff check .` e `uv run mypy custom_components/correios` antes de enviar um PR.

## Teste a sua alteração

Este projeto é baseado no [ha-integration-blueprint](https://github.com/roquerodrigo/ha-integration-blueprint).

Execute `scripts/setup` uma vez para criar o ambiente virtual gerenciado pelo `uv` e, em seguida, `scripts/develop` para iniciar uma instância independente do Home Assistant em modo debug, com a integração carregada e o arquivo [`configuration.yaml`](./config/configuration.yaml) incluído.

## Licença

Ao contribuir, você concorda que as suas contribuições serão licenciadas sob a licença MIT do projeto.
