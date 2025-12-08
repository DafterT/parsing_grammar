from file_parser_to_graph import (
    parse_cli,
    analyze_files,
    render_call_graph,
    write_errors_report,
)
from types_generator import process_type
from type_checker import render_all_typed_cfgs
from pathlib import Path

def main():
    grammar_dir, lang_name, file_paths, out_dir, lib_path = parse_cli()
    result = analyze_files(file_paths, lib_path, lang_name, grammar_dir, out_dir=out_dir)
    
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    call_graph_base = out_dir_path / "call_graph"
    render_call_graph(result, filename=str(call_graph_base), fmt="svg")

    errors_report_path = call_graph_base.with_suffix(".errors.txt")
    ready_assemble = write_errors_report(result, filename=str(errors_report_path))
    if ready_assemble:
        return
    
    # process_type возвращает typed_data - та же структура, но с типами в node.type
    typed_data, errors = process_type(result)
    
    if errors:
        # Записываем ошибки типизации
        type_errors_path = out_dir_path / "type_errors.txt"
        with open(type_errors_path, "w", encoding="utf-8") as f:
            for func_name, err_list in errors.items():
                f.write(f"=== {func_name} ===\n")
                for err in err_list:
                    f.write(f"{err}\n")
                f.write("\n")
        print(f"Ошибки типизации записаны в {type_errors_path}")
        return
    
    # Создаём типизированные графы
    if typed_data:
        typed_graph_dir = out_dir_path / "typed_graph"
        # Теперь render_all_typed_cfgs просто читает типы из node.type
        render_all_typed_cfgs(typed_data, str(typed_graph_dir), fmt="svg")
        print(f"Типизированные графы сохранены в {typed_graph_dir}")


if __name__ == "__main__":
    main()
