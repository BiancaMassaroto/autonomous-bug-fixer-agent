# test_calculadora.py
import pytest
from calculadora import dividir

def test_divisao_normal():
    assert dividir(10, 2) == 5

def test_divisao_por_zero():
    # O teste espera que dividir por zero retorne 0 de forma amigável
    assert dividir(10, 0) == 0