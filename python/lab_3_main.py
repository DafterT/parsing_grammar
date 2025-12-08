from file_parser_to_graph import (
    parse_cli,
    analyze_files,
    render_call_graph,
    write_errors_report,
)
from types_generator import process_type
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
    typed_result, errors = process_type(result)
    print(typed_result, errors)


if __name__ == "__main__":
    main()
