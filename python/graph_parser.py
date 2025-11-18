from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
from tree_parser import TreeViewNode, tree_view_to_str
from graphviz import Digraph
from ast_generator import parse_expr

#######################################################################
# DATA STRUCT
#######################################################################

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
    tree: TreeViewNode = field(default=None)
    succs: List[Tuple[int, Optional[str]]] = field(default_factory=list)


@dataclass
class CFG:
    """
    Весь граф потока управления.
    """
    blocks: Dict[int, Block] = field(default_factory=dict)
    next_id: int = 0  # счётчик для выдачи свежих id

    def new_block(self, label: str, tree: TreeViewNode = None) -> Block:
        """
        Создаёт новый блок с данным текстом.
        """
        b = Block(self.next_id, label, tree)
        self.blocks[b.id] = b
        self.next_id += 1
        return b

    def add_edge(self, src: Block, dst: Block, label: Optional[str] = None):
        """
        Добавляет ребро src -> dst.
        label используется для подписей вроде True/False.
        """
        if dst is not None and src is not None:
            src.succs.append((dst.id, label))
            
    def remove_dangling_blocks(self, entry_id: int = 0, exit_id: int = 1) -> None:
        """Удаляет все блоки, недостижимые из entry_id, оставляя entry/exit."""
        reachable = set()
        stack = [entry_id]

        # DFS/BFS от входного блока
        while stack:
            b_id = stack.pop()
            if b_id in reachable:
                continue
            block = self.blocks.get(b_id)
            if block is None:
                continue
            reachable.add(b_id)
            for succ_id, _ in block.succs:
                if succ_id not in reachable:
                    stack.append(succ_id)

        # гарантируем, что выходной блок не потеряем
        if exit_id in self.blocks:
            reachable.add(exit_id)

        # удаляем все недостижимые блоки
        for b_id in list(self.blocks.keys()):
            if b_id not in reachable:
                del self.blocks[b_id]

        # подчистим succs от ссылок на удалённые блоки
        for block in self.blocks.values():
            block.succs = [
                (dst_id, lbl)
                for (dst_id, lbl) in block.succs
                if dst_id in self.blocks
            ]

#######################################################################
# PARCER
#######################################################################

def parce_block(tree: TreeViewNode, graph: CFG, before: Block, label: str = None, end_cycle: Block = None):
    """
    [0] 'begin'
    [1->-2] statment*
    [-2] 'end'
    [-1] ';'
    """
    begin_id = graph.new_block("begin")
    end_id = graph.new_block("end") # Создали конец
    if before: # Подсоединили предыдущий к себе
        graph.add_edge(before, begin_id, label) 
    statment_id = begin_id
    for i in tree.children[1:-2]:
        statment_id = parce_statment(i, graph, statment_id, None, end_cycle)
    graph.add_edge(statment_id, end_id) # Подсоединили предыдущий к концу
    return end_id


def parce_expression(tree: TreeViewNode, graph: CFG, before: Block, label: str = None):
    if tree.label == 'expr':
        updated_tree = parse_expr(tree)
    else:
        updated_tree = parse_expr(tree.children[0])
    expr_id = graph.new_block(tree_view_to_str(updated_tree), updated_tree) # TODO: Изменить деревья
    
    graph.add_edge(before, expr_id, label) # Подсоединили
    return expr_id

def parce_if(tree: TreeViewNode, graph: CFG, before: Block, label: str = None, end_cycle: Block = None):
    """
    [0] 'if'
    [1] expr
    [2] 'then'
    [3] statment
    ???
    [4] 'else'
    [5] statment
    """
    expr_id = parce_expression(tree.children[1], graph, before, label)
    statment_id = parce_statment(tree.children[3], graph, expr_id, 'True', end_cycle)
    end_if = graph.new_block('end_if')
    graph.add_edge(statment_id, end_if)
    if len(tree.children) == 4:
        graph.add_edge(expr_id, end_if, 'False') # End if
    else:
        statment_id = parce_statment(tree.children[5], graph, expr_id, 'False', end_cycle)
        graph.add_edge(statment_id, end_if) # End if
    return end_if
    
def parce_while(tree: TreeViewNode, graph: CFG, before: Block, label: str = None):
    """
    [0] 'while'
    [1] expr
    [2] 'do'
    [3] statment
    [4] ';'
    """
    expr_id = parce_expression(tree.children[1], graph, before, label)
    end_while = graph.new_block('end_while')
    statment_id = parce_statment(tree.children[3], graph, expr_id, 'True', end_while)
    
    graph.add_edge(statment_id, expr_id) 
    graph.add_edge(expr_id, end_while, 'false') 
    return end_while

def parce_do(tree: TreeViewNode, graph: CFG, before: Block, label: str = None):
    """
    [0] 'repeat'
    [1] statment
    [2] 'while' / 'untill'
    [3] expr
    [4] ';'
    """
    start_repeat = graph.new_block('start_repeat')
    end_repeat = graph.new_block('end_repeat')
    statment_id = parce_statment(tree.children[1], graph, start_repeat, label, end_repeat)
    expr_id = parce_expression(tree.children[3], graph, statment_id)
    
    graph.add_edge(before, start_repeat) 
    graph.add_edge(expr_id, start_repeat, 'true' if tree.children[2] == 'while' else 'false') 
    graph.add_edge(expr_id, end_repeat, 'true' if tree.children[2] != 'while' else 'false') 
    return end_repeat

def parce_break(tree: TreeViewNode, graph: CFG, before: Block, label: str = None, end_cycle: Block = None):
    break_id = graph.new_block('break')
    graph.add_edge(break_id, end_cycle)
    graph.add_edge(before, break_id, label)
    if end_cycle == None:
        raise SyntaxError(f"Error: break without cycle at {tree.node.end_point}")
    return None
    
def parce_statment(tree: TreeViewNode, graph: CFG, before: Block, label: str = None, end_cycle: Block = None):
    tree = tree.children[0]
    match tree.label:
        case 'block':
            return parce_block(tree, graph, before, label, end_cycle)
        case 'expression':
            return parce_expression(tree, graph, before, label)
        case 'if':
            return parce_if(tree, graph, before, label, end_cycle)
        case 'while':
            return parce_while(tree, graph, before, label)
        case 'do':
            return parce_do(tree, graph, before, label)
        case 'break':
            return parce_break(tree, graph, before, label, end_cycle)
        case _:
            print(tree.label)
            raise "Такого блока нет"

def build_graph(tree: TreeViewNode):
    cfg = CFG()
    body = tree.children[0].children[-1]
    if body.label != 'body':
        return None
    parce_block(body.children[0], cfg, None)
    return cfg

#######################################################################
# RENDER
#######################################################################

def cfg_to_graphviz(cfg: CFG,
                    graph_name: str = "CFG",
                    node_shape: str = "box") -> Digraph:
    """
    Строит объект graphviz.Digraph по CFG.

    - Каждый блок рисуется прямоугольником (shape=node_shape) с label.
    - На рёбрах при наличии подписей используется label.
    """
    dot = Digraph(name=graph_name)
    dot.attr("node", shape=node_shape)

    # Сначала добавляем все вершины
    for block in cfg.blocks.values():
        # Можно добавить id в label, чтобы проще ориентироваться
        node_label = f"{block.label}"
        if block.tree is not None:
            lines = str(block.label).splitlines()
            node_label = ""
            for line in lines:
                node_label += line + "\\l" 
        dot.node(str(block.id), label=node_label)

    # Затем добавляем рёбра
    for block in cfg.blocks.values():
        for succ_id, edge_label in block.succs:
            # На всякий случай проверим, что целевой блок существует
            if succ_id not in cfg.blocks:
                continue  # либо raise ValueError(...)
            edge_kwargs = {}
            if edge_label is not None:
                edge_kwargs["label"] = edge_label
            dot.edge(str(block.id), str(succ_id), **edge_kwargs)

    return dot


def render_cfg(cfg: CFG,
               filename: str = "cfg",
               fmt: str = "svg") -> None:
    """
    Рисует CFG в файл (по умолчанию cfg.png) с помощью graphviz.

    :param cfg: объект CFG
    :param filename: имя файла без расширения
    :param fmt: формат (png, pdf, svg, ...)
    """
    if cfg == None:
        return
    dot = cfg_to_graphviz(cfg)
    dot.render(filename, format=fmt, cleanup=True)
