from contextlib import closing

from app.database.connection import Database
from app.database.catalog_migration import migrate_catalog


def run_migrations(database: Database) -> None:
    """Cria estruturas ausentes sem apagar dados existentes."""
    with closing(database.connect()) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    usuario TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1
                )
            """)
            # Esta migração é aditiva: preserva todas as tabelas e linhas existentes.
            connection.execute("""
                CREATE TABLE IF NOT EXISTS artigos_conhecimento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    problema TEXT NOT NULL,
                    solucao TEXT NOT NULL,
                    categoria TEXT NOT NULL DEFAULT 'Geral',
                    criado_por INTEGER NOT NULL,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
                )
            """)
            # ALTER TABLE só é executado quando a coluna ainda não existe.
            # Isso mantém bancos criados por versões anteriores compatíveis.
            article_columns = {
                row["name"] for row in connection.execute(
                    "PRAGMA table_info(artigos_conhecimento)"
                ).fetchall()
            }
            if "observacao" not in article_columns:
                connection.execute(
                    "ALTER TABLE artigos_conhecimento ADD COLUMN observacao TEXT NOT NULL DEFAULT ''"
                )
            user_columns = {
                row["name"] for row in connection.execute(
                    "PRAGMA table_info(usuarios)"
                ).fetchall()
            }
            if "cargo" not in user_columns:
                connection.execute(
                    "ALTER TABLE usuarios ADD COLUMN cargo TEXT NOT NULL DEFAULT ''"
                )

            connection.executescript("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS artigo_categorias (
                    artigo_id INTEGER NOT NULL,
                    categoria_id INTEGER NOT NULL,
                    PRIMARY KEY (artigo_id, categoria_id),
                    FOREIGN KEY (artigo_id) REFERENCES artigos_conhecimento(id) ON DELETE CASCADE,
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS artigo_marcacoes (
                    artigo_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL CHECK (tipo IN ('favorito','contato','cofre')),
                    PRIMARY KEY (artigo_id, usuario_id, tipo),
                    FOREIGN KEY (artigo_id) REFERENCES artigos_conhecimento(id) ON DELETE CASCADE,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS cofres_usuario (
                    usuario_id INTEGER PRIMARY KEY,
                    senha_hash TEXT,
                    recuperacao_status TEXT NOT NULL DEFAULT 'nenhuma'
                        CHECK (recuperacao_status IN ('nenhuma','aguardando','aprovado')),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS recuperacoes_login (
                    usuario_id INTEGER PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'aguardando'
                        CHECK (status IN ('aguardando','aprovado')),
                    solicitado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS artigos_recentes (
                    artigo_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    acessado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (artigo_id, usuario_id),
                    FOREIGN KEY (artigo_id) REFERENCES artigos_conhecimento(id) ON DELETE CASCADE,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS usuarios_sapiens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    numero TEXT NOT NULL DEFAULT '',
                    setor TEXT NOT NULL DEFAULT '',
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS categorias_modulo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    modulo TEXT NOT NULL CHECK (modulo IN ('relatorio','banco','regra')),
                    nome TEXT NOT NULL COLLATE NOCASE,
                    UNIQUE (modulo,nome)
                );

                CREATE TABLE IF NOT EXISTS registros_modulo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    modulo TEXT NOT NULL CHECK (modulo IN ('relatorio','banco','regra')),
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL DEFAULT '',
                    finalidade TEXT NOT NULL DEFAULT '',
                    observacao TEXT NOT NULL DEFAULT '',
                    categoria_id INTEGER,
                    criado_por INTEGER NOT NULL,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (categoria_id) REFERENCES categorias_modulo(id),
                    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
                );

                CREATE TABLE IF NOT EXISTS campos_banco (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registro_id INTEGER NOT NULL,
                    nome TEXT NOT NULL,
                    descricao TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (registro_id) REFERENCES registros_modulo(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_artigos_titulo
                    ON artigos_conhecimento(titulo);
                CREATE INDEX IF NOT EXISTS idx_categorias_nome
                    ON categorias(nome);
                CREATE INDEX IF NOT EXISTS idx_recentes_usuario_data
                    ON artigos_recentes(usuario_id, acessado_em DESC);
            """)

            # Converte categorias antigas de texto para a nova relação muitos-para-muitos.
            connection.execute("""
                INSERT OR IGNORE INTO categorias(nome)
                SELECT DISTINCT categoria FROM artigos_conhecimento
                WHERE TRIM(categoria) <> ''
            """)
            connection.execute("""
                INSERT OR IGNORE INTO artigo_categorias(artigo_id,categoria_id)
                SELECT a.id,c.id
                FROM artigos_conhecimento a
                JOIN categorias c ON c.nome=a.categoria COLLATE NOCASE
            """)
    migrate_catalog(database)
