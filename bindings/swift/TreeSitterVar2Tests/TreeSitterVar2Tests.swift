import XCTest
import SwiftTreeSitter
import TreeSitterVar2

final class TreeSitterVar2Tests: XCTestCase {
    func testCanLoadGrammar() throws {
        let parser = Parser()
        let language = Language(language: tree_sitter_var2())
        XCTAssertNoThrow(try parser.setLanguage(language),
                         "Error loading Var2 grammar")
    }
}
