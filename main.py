import re
import yaml
import argparse
from typing import Any, Dict, List



class Lexer:
    TOKENS = [
        (r"\s+", None),
        (r"var", "VAR"),
        (r"\^", "EVAL"),
        (r"\*", "MULTIPLY"),
        (r"@{", "DICT_START"),
        (r"}", "DICT_END"),
        (r"/", "DIVIDE"),
        (r"\(", "ARRAY_START"),
        (r"\)", "ARRAY_END"),
        (r",", "COMMA"),
        (r"=", "EQUALS"),
        (r"true|false", "BOOLEAN"),
        (r"[0-9]+", "NUMBER"),
        (r'"[^"]*"', "STRING"),
        (r"[_A-Za-z][_a-zA-Z0-9]*", "IDENTIFIER"),
        (r";", "SEMICOLON"),
        (r"\+", "PLUS"),
        (r"-", "MINUS"),
    ]

    def __init__(self, text: str):
        self.text = text
        self.tokens = []
        self.position = 0
        self.tokenize()

    def tokenize(self):
        while self.position < len(self.text):
            match = None
            for regex, token_type in self.TOKENS:
                regex_match = re.match(regex, self.text[self.position:])
                if regex_match:
                    match = regex_match.group(0)
                    if token_type:
                        self.tokens.append((token_type, match, self.position))
                    break
            if not match:
                raise SyntaxError(f"Неожиданный символ: '{self.text[self.position]}'")
            self.position += len(match)

    def peek(self):
        return self.tokens[0] if self.tokens else None

    def next_token(self):
        return self.tokens.pop(0) if self.tokens else None



class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.variables = {}

    def parse(self) -> Any:
        result = []
        while self.lexer.peek():
            result.append(self.statement())
        return result if len(result) > 1 else result[0]

    def statement(self) -> Any:
        token = self.lexer.peek()
        if token[0] == "VAR":
            return self.parse_var()
        elif token[0] == "DICT_START":
            return self.parse_dict()
        elif token[0] == "ARRAY_START":
            return self.parse_array()
        raise SyntaxError(f"Неожиданный токен: {token}")

    def parse_var(self) -> Any:
        self.lexer.next_token()
        identifier = self.lexer.next_token()
        if identifier[0] != "IDENTIFIER":
            raise SyntaxError(f"Ожидался идентификатор после 'var'")
        self.expect("EQUALS")
        value = self.parse_value()
        self.variables[identifier[1]] = value
        return {identifier[1]: value}

    def parse_value(self) -> Any:
        token = self.lexer.peek()
        if token[0] == "NUMBER":
            return int(self.lexer.next_token()[1])
        elif token[0] == "STRING":
            return self.lexer.next_token()[1].strip('"')
        elif token[0] == "BOOLEAN":
            return self.lexer.next_token()[1] == "true"
        elif token[0] == "ARRAY_START":
            return self.parse_array()
        elif token[0] == "DICT_START":
            return self.parse_dict()
        elif token[0] == "EVAL":
            return self.parse_eval()
        raise SyntaxError(f"Неожиданное значение: {token}")

    def parse_array(self) -> List[Any]:
        self.lexer.next_token()
        array = []
        while self.lexer.peek() and self.lexer.peek()[0] != "ARRAY_END":
            array.append(self.parse_value())
            if self.lexer.peek()[0] == "COMMA":
                self.lexer.next_token()
        self.expect("ARRAY_END")
        return array

    def parse_dict(self) -> Dict[str, Any]:
        self.lexer.next_token()
        dictionary = {}
        while self.lexer.peek() and self.lexer.peek()[0] != "DICT_END":
            key = self.lexer.next_token()
            if key[0] != "IDENTIFIER":
                raise SyntaxError(f"Ожидался идентификатор в качестве ключа")
            self.expect("EQUALS")
            value = self.parse_value()
            dictionary[key[1]] = value
            if self.lexer.peek()[0] == "SEMICOLON":
                self.lexer.next_token()
        self.expect("DICT_END")
        return dictionary

    def parse_eval(self) -> Any:
        self.lexer.next_token()
        identifier = self.lexer.next_token()
        if identifier[0] != "IDENTIFIER":
            raise SyntaxError(f"Ожидался идентификатор после '^'")
        if identifier[1] not in self.variables:
            raise ValueError(f"Неопределённая переменная: {identifier[1]}")


        value = self.variables[identifier[1]]


        token = self.lexer.peek()
        if token and token[0] in ["PLUS", "MINUS", "MULTIPLY", "DIVIDE"]:
            operator = self.lexer.next_token()[0]
            right_value = self.parse_value()
            if operator == "PLUS":
                value += right_value
            elif operator == "MINUS":
                value -= right_value
            elif operator == "MULTIPLY":
                value *= right_value
            elif operator == "DIVIDE":
                if right_value == 0:
                    raise ZeroDivisionError(f"Ошибка: Деление на ноль")
                value /= right_value
        return value

    def expect(self, token_type: str):
        token = self.lexer.next_token()
        if not token or token[0] != token_type:
            position = token[2] if token else "EOF"
            raise SyntaxError(f"Ожидался токен {token_type}, но получен {token}")


# Конвертер в YAML
def convert_to_yaml(data: Any) -> str:
    return yaml.dump(data, allow_unicode=True, default_flow_style=False)


# CLI-интерфейс
def main():
    parser = argparse.ArgumentParser(description="Учебный конфигурационный язык в YAML.")
    parser.add_argument("input_file", help="Путь к входному файлу")
    parser.add_argument("output_file", help="Путь к выходному файлу")
    args = parser.parse_args()

    try:
        with open(args.input_file, "r", encoding="utf-8") as file:
            text = file.read()

        lexer = Lexer(text)
        parsed_data = Parser(lexer).parse()
        yaml_data = convert_to_yaml(parsed_data)

        with open(args.output_file, "w", encoding="utf-8") as file:
            file.write(yaml_data)

    except SyntaxError as e:
        print(f"Синтаксическая ошибка: {e}")
    except ValueError as e:
        print(f"Ошибка: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()
