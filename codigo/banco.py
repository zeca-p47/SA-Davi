
import sqlite3
from pathlib import Path

# Caminho absoluto do banco de dados
BASE_DIR = Path(__file__).resolve().parent
CAMINHO_BANCO = BASE_DIR / "choco.db"


def conectar():
    try:
        conexao = sqlite3.connect(
            CAMINHO_BANCO,
            timeout=10
        )

        # Permite acessar as colunas pelo nome
        conexao.row_factory = sqlite3.Row

        # Ativa a verificação das chaves estrangeiras
        conexao.execute("PRAGMA foreign_keys = ON")

        return conexao

    except sqlite3.Error as erro:
        print("Erro ao conectar ao banco:", erro)
        raise


def criar_banco():
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            unidade TEXT NOT NULL,
            quantidade REAL NOT NULL DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cargo TEXT NOT NULL,
            telefone TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS producao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (produto_id)
                REFERENCES produtos(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (cliente_id)
                REFERENCES clientes(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (venda_id)
                REFERENCES vendas(id),
            FOREIGN KEY (produto_id)
                REFERENCES produtos(id)
        )
        """)

        conexao.commit()
        print("Banco de dados conectado e tabelas verificadas!")

    except sqlite3.Error as erro:
        conexao.rollback()
        print("Erro ao criar tabelas:", erro)
        raise

    finally:
        conexao.close()
