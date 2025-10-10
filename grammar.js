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

  rules: {
    source_file: $ => repeat(choice(
      field('expr', $.expression),
    )),
    
    expression: $ => choice(
      field('unary', $.unary_expression),
      field('binary', $.binary_expression),
      field('place', $.identifier),
    ),

    unary_expression: $ => prec.left(PREC.UNARY, seq(
      field('operator', choice('!', '~', '-', '+')),
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
        ['==', PREC.EQUAL],
        ['!=', PREC.EQUAL],
        ['>', PREC.RELATIONAL],
        ['>=', PREC.RELATIONAL],
        ['<=', PREC.RELATIONAL],
        ['<', PREC.RELATIONAL],
        ['<<', PREC.SHIFT],
        ['>>', PREC.SHIFT],
      ];

      return choice(...table.map(([operator, precedence]) => {
        return prec.left(precedence, seq(
          field('expr', $.expression),
          // @ts-ignore
          field('binOp', operator),
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

    /*
    list: $ => seq(
      '(',
      $.bool,
      repeat(seq(',', $.bool)),
      ')'
    ),
    */
  }
});
