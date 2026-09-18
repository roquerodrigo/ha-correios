## Resumo

<!-- 1 a 3 itens descrevendo o que mudou e por quê. -->

## Tipo de mudança

- [ ] Correção de bug
- [ ] Nova funcionalidade
- [ ] Refatoração / limpeza
- [ ] Documentação
- [ ] Ferramentas / CI

## Plano de testes

- [ ] `uv run ruff format --check .`, `uv run ruff check .` e `uv run mypy custom_components/correios` passam
- [ ] O `pytest` passa com o gate de cobertura de 90 %
- [ ] Todos os locales de tradução atualizados (se strings voltadas ao usuário mudaram)

## Checklist

- [ ] O código está em inglês; documentação, docstrings e comentários estão em português do Brasil
- [ ] Uma classe de nível superior por arquivo
- [ ] CLAUDE.md / README atualizados se a arquitetura ou o fluxo de trabalho mudou
- [ ] Versão do `manifest.json` incrementada, se for um release
