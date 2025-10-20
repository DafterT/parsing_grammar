/**
 * @file Парсер для 2 варианта
 * @author Dafter
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check
const PREC = {
  PAREN_DECLARATOR: -10,
  ASSIGNMENT: -2,
  CONDITIONAL: -1,
  DEFAULT: 0,
  LOGICAL_OR: 1,
  LOGICAL_AND: 2,
  INCLUSIVE_OR: 3,
  EXCLUSIVE_OR: 4,
  BITWISE_AND: 5,
  EQUAL: 6,
  RELATIONAL: 7,
  OFFSETOF: 8,
  SHIFT: 9,
  ADD: 10,
  MULTIPLY: 11,
  CAST: 12,
  SIZEOF: 13,
  UNARY: 14,
  CALL: 15,
  FIELD: 16,
  SUBSCRIPT: 17,
};

module.exports = grammar({
  name: "var2",

  word: $ => $.identifier,
  
  rules: {
    source: $ => repeat(
      field('sourceItem', $.sourceItem),
    ),
    sourceItem: $ => field('funcDef', $.funcDef),

    funcDef: $ => seq(
      'method',
      field('funcSignature', $.funcSignature),
      choice(
        field('body', $.body),
        ';',
      )
    ),

    body: $ => seq(
      optional(seq(
        'var',
        repeat(seq(
          field('list_identifier', $.list_identifier),
          optional(seq(
            ':',
            field('typeRef', $.typeRef)
          )),
          ';'
        ))
      )),
      field('statment_block', $.block_content)
    ),

    list_identifier: $ => seq(
      field('identifier', $.identifier),
      repeat(seq(',', field('identifier', $.identifier)))
    )),

    funcSignature: $ => seq(
      field('identifier', $.identifier),
      '(',
      field('list_argDef', $.list_argDef),
      ')',
      optional(seq(
        ':',
        field('typeRef', $.typeRef),
      ))
    ),

    list_argDef: $ => seq(
      field('argDef', $.argDef),
      repeat(seq(',', field('argDef', $.argDef)))
    ),

    argDef: $ => seq(
      field('identifier', $.identifier),
      optional(seq(
        ':',
        field('typeRef', $.typeRef)
      ))
    ),

    typeRef: $ => choice(
      alias(choice(
        'bool',
        'byte',
        'int',
        'uint',
        'long',
        'ulong',
        'char',
        'string',
      ), 'builtin'),
      field('custom', $.identifier),
      field('array', $.array)
    ),

    array: $ => seq(
      'array',
      '[',
      repeat(','),
      ']',
      'of',
      $.typeRef,
    ),

    statement: $ => choice(
      field('if', $.if_statement),
      field('block', $.block_content),
      field('while', $.while_content),
      field('do', $.do_content),
      field('break', $.break_content),
      field('expression', $.expression_content),
    ),

    break_content: $ => seq('break', ';'),

    expression_content: $ => field('expr', seq($.expression, ';')),

    do_content: $ => seq(
      'repeat',
      field('statement', $.statement),
      choice('while', 'until'),
      field('expr', $.expression),
      ';'
    ),

    while_content: $ => seq(
      'while',
      field('expr', $.expression),
      'do',
      field('statement', $.statement),
    ),

    block_content: $ => seq(
      'begin', 
      repeat(field('statement', $.statement)), 
      'end', 
      ';'
    ),

    if_statement: $ => prec.right(seq(
      'if',
      field('expr', $.expression),
      'then',
      field('statement', $.statement),
      optional(seq('else', field('statement', $.statement))),
    )),

    expression: $ => choice(
      field('unary', $.unary_expression),
      field('binary', $.binary_expression),
      field('braces', $.braces_expression),
      field('call', $.call_expression),
      field('indexer', $.indexer),
      field('place', $.identifier),
      field('literal', $.literal),
    ),

    braces_expression: $ => seq(
      '(', 
      field('expr', $.expression), 
      ')'
    ),

    literal: $ => choice($.bool, $.str, $.char, $.hex, $.bits, $.dec),

    indexer: $ => prec(PREC.SUBSCRIPT, seq(
      field('expr', $.expression),
      seq('[', field('listExpr', $.list_expr), ']')
    )),

    call_expression: $ => prec(PREC.CALL, seq(
      field('expr', $.expression),
      seq('(', field('listExpr', $.list_expr), ')')
    )),

    list_expr: $ => seq(
      field('expr', $.expression),
      repeat(seq(',', field('expr', $.expression)))
    ),

    unary_expression: $ => prec.left(PREC.UNARY, seq(
      field('unOp', alias(choice('!', '~'), $.un_op)),
      field('expr', $.expression),
    )),

    binary_expression: $ => {
      const table = [
        [':=', PREC.ASSIGNMENT],
        ['+', PREC.ADD],
        ['-', PREC.ADD],
        ['*', PREC.MULTIPLY],
        ['/', PREC.MULTIPLY],
        ['%', PREC.MULTIPLY],
        ['||', PREC.LOGICAL_OR],
        ['&&', PREC.LOGICAL_AND],
        ['|', PREC.INCLUSIVE_OR],
        ['^', PREC.EXCLUSIVE_OR],
        ['&', PREC.BITWISE_AND],
        ['=', PREC.EQUAL],
        ['!=', PREC.EQUAL],
        ['>', PREC.RELATIONAL],
        ['>=', PREC.RELATIONAL],
        ['<=', PREC.RELATIONAL],
        ['<', PREC.RELATIONAL],
        ['<<', PREC.SHIFT],
        ['>>', PREC.SHIFT],
      ];

      return choice(...table.map(([operator, precedence]) => {
        return prec.right(precedence, seq(
          field('expr', $.expression),
          // @ts-ignore
          field('binOp', alias(operator, $.bin_op)),
          field('expr', $.expression),
        ));
      }));
    },


    identifier: _ => /[a-zA-Z_][a-zA-Z_0-9]*/,
    str: _ => /\"[^\"\\]*(?:\\.[^\"\\]*)*\"/,
    char: _ => /\'[^\']\'/,
    hex: _ => /0[xX][0-9A-Fa-f]+/,
    bits: _ => /0[bB][01]+/,
    dec: _ => /[0-9]+/,

    _true: _ => token('true'),
    _false: _ => token('false'),
    bool: $ => choice($._true, $._false),
  }
});
