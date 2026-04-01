"""Minimal JSON-first deterministic rule evaluator scaffold.

This intentionally starts small. It supports a useful subset of JSONLogic-like
operators needed for early Vellum prototyping and can later be swapped for a
full evaluator library without changing the rule contract shape.
"""

from __future__ import annotations

from typing import Any, Dict, List


class JsonLogicEvaluationError(Exception):
    pass


class JsonLogicEvaluator:
    def evaluate(self, expression: Any, data: Dict[str, Any]) -> Any:
        if isinstance(expression, (str, int, float, bool)) or expression is None:
            return expression

        if isinstance(expression, list):
            return [self.evaluate(item, data) for item in expression]

        if not isinstance(expression, dict):
            raise JsonLogicEvaluationError(f'Unsupported expression type: {type(expression)}')

        if len(expression) != 1:
            return {key: self.evaluate(value, data) for key, value in expression.items()}

        operator, operand = next(iter(expression.items()))

        if operator == 'var':
            return self._resolve_var(operand, data)
        if operator == '==':
            left, right = self._eval_pair(operand, data)
            return left == right
        if operator == '!=':
            left, right = self._eval_pair(operand, data)
            return left != right
        if operator == '>':
            left, right = self._eval_pair(operand, data)
            return left > right
        if operator == '>=':
            left, right = self._eval_pair(operand, data)
            return left >= right
        if operator == '<':
            left, right = self._eval_pair(operand, data)
            return left < right
        if operator == '<=':
            left, right = self._eval_pair(operand, data)
            return left <= right
        if operator == 'and':
            return all(self.evaluate(item, data) for item in self._ensure_list(operand))
        if operator == 'or':
            return any(self.evaluate(item, data) for item in self._ensure_list(operand))
        if operator == '!':
            return not self.evaluate(operand, data)
        if operator == 'in':
            needle, haystack = self._eval_pair(operand, data)
            return needle in haystack
        if operator == '+':
            return sum(self.evaluate(item, data) for item in self._ensure_list(operand))
        if operator == '-':
            values = [self.evaluate(item, data) for item in self._ensure_list(operand)]
            if not values:
                return 0
            if len(values) == 1:
                return -values[0]
            first, *rest = values
            for item in rest:
                first -= item
            return first

        raise JsonLogicEvaluationError(f'Unsupported operator: {operator}')

    def _resolve_var(self, operand: Any, data: Dict[str, Any]) -> Any:
        if isinstance(operand, list):
            path = operand[0] if operand else None
            default = operand[1] if len(operand) > 1 else None
        else:
            path = operand
            default = None

        if not path:
            return data

        current: Any = data
        for part in str(path).split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def _eval_pair(self, operand: Any, data: Dict[str, Any]):
        values = self._ensure_list(operand)
        if len(values) != 2:
            raise JsonLogicEvaluationError('Expected exactly two operands')
        return self.evaluate(values[0], data), self.evaluate(values[1], data)

    @staticmethod
    def _ensure_list(value: Any) -> List[Any]:
        if isinstance(value, list):
            return value
        return [value]
