# -*- coding: utf-8 -*-
"""
Простой пример построения графа потока управления (CFG)
для конструкций вида:
    - присваивание:   x = 1
    - if / else

Идея:
    - Каждый прямоугольник в графе = Block.
    - Внутри Block лежит текст (или ссылка на дерево операций).
    - Рёбра между Block задают поток управления.
    - Для каждого оператора мы строим Fragment(entry, exits),
      чтобы фрагменты легко склеивать.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union


# ==========================
# 1. БАЗОВЫЕ СТРУКТУРЫ CFG
# ==========================

@dataclass
class Block:
    """
    Один блок графа (будущий прямоугольник на картинке).

    id      - уникальный номер блока
    label   - текст внутри блока (или можно класть сюда указатель на дерево операций)
    succs   - список исходящих рёбер вида (id_следующего_блока, метка_ребра)
              метка_ребра, например, "True"/"False" для if.
    """
    id: int
    label: str
    succs: List[Tuple[int, Optional[str]]] = field(default_factory=list)


@dataclass
class CFG:
    """
    Весь граф потока управления.
    """
    blocks: Dict[int, Block] = field(default_factory=dict)
    next_id: int = 0  # счётчик для выдачи свежих id

    def new_block(self, label: str) -> Block:
        """
        Создаёт новый блок с данным текстом.
        """
        b = Block(self.next_id, label)
        self.blocks[b.id] = b
        self.next_id += 1
        return b

    def add_edge(self, src: Block, dst: Block, label: Optional[str] = None):
        """
        Добавляет ребро src -> dst.
        label используется для подписей вроде True/False.
        """
        src.succs.append((dst.id, label))


# ==========================
# 2. ПРОСТЕЙШИЙ "AST"
# ==========================

@dataclass
class Assign:
    """
    Присваивание, например:
        c = 2
    Для простоты просто храним строку.
    В реале тут может быть ссылочка на дерево выражения.
    """
    text: str


@dataclass
class If:
    """
    Оператор if / else.

    cond      - условие (строкой; в реале — дерево выражения).
    then_body - список операторов для ветки then.
    else_body - список операторов для ветки else или None.
    """
    cond: str
    then_body: List["Stmt"]
    else_body: Optional[List["Stmt"]] = None


# Stmt может быть либо Assign, либо If
Stmt = Union[Assign, If]


# ==========================
# 3. ФРАГМЕНТ ГРАФА
# ==========================

@dataclass
class Fragment:
    """
    Фрагмент графа.

    entry - блок, с которого начинается этот фрагмент
    exits - список блоков, из которых поток "выходит наружу"
            (к ним позже приклеим следующий код)
    """
    entry: Block
    exits: List[Block]


# ==========================
# 4. ПОСТРОЕНИЕ CFG ДЛЯ ОПЕРАТОРОВ
# ==========================

def build_assign(cfg: CFG, node: Assign) -> Fragment:
    """
    Простой оператор (присваивание).
    Делает один блок с текстом присваивания.
    Вход = этот блок, выход = тоже этот блок.
    """
    block = cfg.new_block(node.text)
    return Fragment(entry=block, exits=[block])


def build_seq(cfg: CFG, stmts: List[Stmt]) -> Fragment:
    """
    Последовательность операторов (как внутри begin ... end).

    Пример:
        s1;
        s2;
        s3;

    Строим фрагмент для s1 (f1), потом для s2 (f2) и т.п.,
    и "хвосты" предыдущего фрагмента ведём в entry следующего.
    """
    assert stmts, "Пустую последовательность здесь не обрабатываем для простоты"

    # Строим фрагмент для первого оператора
    frag = build_stmt(cfg, stmts[0])
    entry = frag.entry
    exits = frag.exits

    # Последовательно приклеиваем остальные
    for stmt in stmts[1:]:
        next_frag = build_stmt(cfg, stmt)

        # Все выходы предыдущего фрагмента ведём в вход следующего
        for e in exits:
            cfg.add_edge(e, next_frag.entry)

        # Новыми "хвостами" становятся выходы следующего фрагмента
        exits = next_frag.exits

    return Fragment(entry=entry, exits=exits)


def build_if(cfg: CFG, node: If) -> Fragment:
    """
    Построение фрагмента для if / else.

    Логика:

        [cond_block] --True--> [then_body...]
                     --False-> [else_body...] или сразу join

        из концов then и else всё идёт в общий join-блок.

    Возвращаем Fragment:
        entry = cond_block
        exits = [join_block]
    """
    # 1. Блок с условием
    cond_block = cfg.new_block(f"if ({node.cond})")

    # 2. then-ветка (если пустая — считаем, что она просто ничего не делает)
    if node.then_body:
        then_frag = build_seq(cfg, node.then_body)
    else:
        # пустая then-ветка: вход и выход один и тот же блок cond
        then_frag = Fragment(entry=cond_block, exits=[cond_block])

    # 3. else-ветка (может отсутствовать)
    if node.else_body:
        else_frag = build_seq(cfg, node.else_body)
    else:
        else_frag = None

    # 4. Общий блок слияния (join)
    join_block = cfg.new_block("join")

    # 5. Рёбра от cond к then и else
    cfg.add_edge(cond_block, then_frag.entry, "True")
    if else_frag is not None:
        cfg.add_edge(cond_block, else_frag.entry, "False")
    else:
        # Нет else: False идёт сразу в join
        cfg.add_edge(cond_block, join_block, "False")

    # 6. Хвосты then-ветки идёт в join
    for e in then_frag.exits:
        cfg.add_edge(e, join_block)

    # 7. Хвосты else-ветки тоже в join (если она есть)
    if else_frag is not None:
        for e in else_frag.exits:
            cfg.add_edge(e, join_block)

    # 8. Возвращаем фрагмент if-а
    return Fragment(entry=cond_block, exits=[join_block])


def build_stmt(cfg: CFG, stmt: Stmt) -> Fragment:
    """
    Диспетчер по типу оператора.
    """
    if isinstance(stmt, Assign):
        return build_assign(cfg, stmt)
    elif isinstance(stmt, If):
        return build_if(cfg, stmt)
    else:
        raise TypeError(f"Неизвестный тип узла: {stmt!r}")


# ==========================
# 5. ПОСТРОЕНИЕ ВЕСЬ ФУНКЦИИ
# ==========================

def build_function_cfg(stmts: List[Stmt]) -> CFG:
    """
    Строим CFG для всей "функции":
        BEGIN -> тело -> END

    BEGIN и END делаем отдельными блоками.
    """
    cfg = CFG()

    # начало и конец
    begin = cfg.new_block("BEGIN")
    end = cfg.new_block("END")

    # фрагмент для тела
    body_frag = build_seq(cfg, stmts)

    # вход: BEGIN -> entry тела
    cfg.add_edge(begin, body_frag.entry)

    # все выходы тела ведём в END
    for e in body_frag.exits:
        cfg.add_edge(e, end)

    return cfg


# ==========================
# 6. УТИЛИТЫ ДЛЯ ОТЛАДКИ / ВЫВОДА
# ==========================

def print_cfg(cfg: CFG):
    """
    Печать CFG в текстовом виде:
        Block id: label
          --label--> Block id
          -----> Block id
    """
    for bid in sorted(cfg.blocks):
        b = cfg.blocks[bid]
        print(f"Block {b.id}: {b.label}")
        for dst, lab in b.succs:
            if lab:
                print(f"  --{lab}--> Block {dst}")
            else:
                print(f"  -----> Block {dst}")


def to_dot(cfg: CFG) -> str:
    """
    Генерация текста в формате DOT для Graphviz.
    Можно сохранить в файл и отрисовать командой:
        dot -Tpng cfg.dot -o cfg.png
    """
    lines = [
        "digraph CFG {",
        "  rankdir=TB;",  # TB = top-bottom, можно LR для слева-направо
        '  node [shape=box, style="rounded,filled", fillcolor="lightgray"];'
    ]

    # Узлы
    for bid in sorted(cfg.blocks):
        label = cfg.blocks[bid].label.replace('"', '\\"')
        lines.append(f'  {bid} [label="{label}"];')

    # Рёбра
    for b in cfg.blocks.values():
        for dst, lab in b.succs:
            if lab:
                lines.append(f'  {b.id} -> {dst} [label="{lab}"];')
            else:
                lines.append(f"  {b.id} -> {dst};")

    lines.append("}")
    return "\n".join(lines)


# ==========================
# 7. ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ==========================

if __name__ == "__main__":
    # Твой пример:
    #
    # if (a == b) begin
    #   c = 2;
    # end else begin
    #   if (p == 3) begin
    #     a = b+2;
    #   end
    # end

    inner_if = If(
        cond="p == 3",
        then_body=[
            Assign("a = b + 2"),
        ],
        else_body=[]  # пустой else, можно и None
    )

    outer_if = If(
        cond="a == b",
        then_body=[
            Assign("c = 2"),
        ],
        else_body=[
            inner_if
        ]
    )

    # Строим CFG для "функции", внутри которой только этот if
    cfg = build_function_cfg([outer_if])

    print("=== ТЕКСТОВЫЙ ВЫВОД CFG ===")
    print_cfg(cfg)

    print("\n=== DOT ДЛЯ GRAPHVIZ ===")
    dot_text = to_dot(cfg)
    print(dot_text)
