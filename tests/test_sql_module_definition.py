"""Portable regression for SQL Server's observed CREATE-three-spaces header."""
import unittest

from scripts.sql_module_definition import same_procedure_definition


class ProcedureDefinitionTests(unittest.TestCase):
    BODY = "dbo.Example @Value int\nAS\nBEGIN\n SELECT 'a  b'; -- keep  spaces\nEND;"

    def test_all_supported_headers_and_keyword_whitespace(self):
        expected = "CREATE OR ALTER PROCEDURE " + self.BODY
        for header in ("CREATE PROCEDURE ", "CREATE   PROCEDURE ", "ALTER PROCEDURE ",
                       "CREATE OR ALTER PROCEDURE ", "create\tOr\r\nAlter\tprocedure\t"):
            with self.subTest(header=header):
                self.assertTrue(same_procedure_definition(expected, header + self.BODY))

    def test_body_name_signature_comments_and_literals_are_not_normalized(self):
        expected = "CREATE OR ALTER PROCEDURE " + self.BODY
        for body in (self.BODY.replace('Example', 'Other'), self.BODY.replace('int', 'bigint'),
                     self.BODY.replace("'a  b'", "'a b'"), self.BODY.replace('keep  spaces', 'keep spaces'),
                     self.BODY.replace('SELECT', 'DELETE'), self.BODY + '\n',
                     self.BODY.replace('\n', '\r\n')):
            with self.subTest(body=body):
                self.assertFalse(same_procedure_definition(expected, "CREATE   PROCEDURE " + body))

    def test_missing_encrypted_or_unparsed_text_refuses(self):
        for value in (None, '', 'CREATE VIEW dbo.Example AS SELECT 1',
                      '-- prefix\nCREATE PROCEDURE ' + self.BODY, 'CREATE PROCEDURE '):
            with self.subTest(value=value), self.assertRaises(ValueError):
                same_procedure_definition('CREATE PROCEDURE ' + self.BODY, value)


if __name__ == '__main__':
    unittest.main()
