"""Ponte de compatibilidade com a primeira versão do projeto."""
from app.database.connection import Database
from app.database.migrations import run_migrations


def conectar():
    return Database().connect()


def criar_tabelas() -> None:
    run_migrations(Database())


def criar_usuario_inicial() -> None:
    """O primeiro administrador agora é cadastrado pela interface."""
    criar_tabelas()
