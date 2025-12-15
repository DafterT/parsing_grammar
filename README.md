# Практическое задание 1

## О работе
- Курс: «Языки программирования», практическое задание №1 (вариант 2).
- Студент: Д. Л. Симоновский, группа P4119.
- Руководитель: Ю. Д. Кореньков.
- Отчёт: `report/ЯП_1_лаба_Р4119_Симоновский.pdf`.

## Содержание

Грамматика и парсер для варианта 2 на базе **tree-sitter**. В репозитории есть:
- исходная грамматика (`grammar.js`, `src/grammar.json`);
- сгенерированный C-парсер (`src/parser.c`, `parser.dll`);
- Python-утилита (`python/main.py` + `get_parse_tree.py`) для сборки парсера и вывода дерева разбора в файл;
- отчёт в `report/`.

## Требования
- Python 3.10+;
- Node.js (для `tree-sitter` CLI);
- установленный `tree-sitter` CLI (`npm i -g tree-sitter-cli`).

## Установка Python-зависимостей
Рекомендуется виртуальное окружение:
```
python -m venv .venv
.venv\Scripts\activate      # PowerShell/cmd
pip install -r requirements.txt
```

`requirements.txt` содержит единственный обязательный пакет: `tree-sitter>=0.24.0`.

## Сборка парсера tree-sitter вручную
CLI-команды исполняются в корне проекта:
```
tree-sitter g
tree-sitter b # собрать shared-библиотеку (Windows DLL)
```
Готовая библиотека появляется в корне `parser.dll` 

## Запуск Python-утилиты
Скрипт `python/main.py` работает в двух режимах и всегда принимает путь к входному файлу и путь для вывода дерева.

### Режим 1. Использовать уже собранную библиотеку
```
python python/main.py --lib parser.dll --lang var2 examples/functions examples/functions.txt
```
- `--lib PATH` — путь к готовой библиотеке (`.dll/.so/.dylib`);
- `--lang NAME` — имя языка (функция `tree_sitter_<NAME>` внутри библиотеки). Если флаг не указан, имя извлекается из файла (например, `var2.dll` → `var2`).

### Режим 2. Собрать парсер из грамматики на лету
Скрипт сам вызовет `tree-sitter generate/build`; нужен установленный `tree-sitter` CLI.
```
python python/main.py . var2 examples/functions examples/functions.txt
```
- позиционные аргументы: `grammar_dir` (папка с `grammar.js`), `lang_name`, `file_path`, `out_file_path`.

### Правила использования
- Нельзя одновременно задавать `--lib` и позиционные `grammar_dir/lang_name`.
- Вывод — текстовое дерево в стиле `tree`, сохраняется в `out_file_path`. Ошибки разбора и отсутствующие узлы логируются в stderr.

## Полезное
- Примеры входных файлов лежат в `examples/` (соответствующие эталонные деревья — `*.txt`).
- Отчёт по заданию: `report/ЯП_1_лаба_Р4119_Симоновский.pdf`.