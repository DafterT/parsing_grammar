package tree_sitter_var2_test

import (
	"testing"

	tree_sitter "github.com/tree-sitter/go-tree-sitter"
	tree_sitter_var2 "github.com/daftert/parsing_grammar/bindings/go"
)

func TestCanLoadGrammar(t *testing.T) {
	language := tree_sitter.NewLanguage(tree_sitter_var2.Language())
	if language == nil {
		t.Errorf("Error loading Var2 grammar")
	}
}
