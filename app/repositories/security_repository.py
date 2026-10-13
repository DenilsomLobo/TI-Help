from contextlib import closing

from app.database.connection import Database


class SecurityRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save_vault_password(self, user_id: int, password_hash: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    """INSERT INTO cofres_usuario(usuario_id,senha_hash,recuperacao_status)
                       VALUES(?,?,'nenhuma')
                       ON CONFLICT(usuario_id) DO UPDATE SET
                           senha_hash=excluded.senha_hash, recuperacao_status='nenhuma'""",
                    (user_id, password_hash))

    def vault_data(self, user_id: int):
        with closing(self.database.connect()) as connection:
            return connection.execute(
                "SELECT senha_hash,recuperacao_status FROM cofres_usuario WHERE usuario_id=?",
                (user_id,)).fetchone()

    def request_vault_recovery(self, user_id: int) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    """INSERT INTO cofres_usuario(usuario_id,recuperacao_status)
                       VALUES(?,'aguardando') ON CONFLICT(usuario_id) DO UPDATE SET
                       recuperacao_status='aguardando'""", (user_id,))

    def pending_requests(self) -> list[dict]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                """SELECT u.id,u.nome,u.usuario,'cofre' origem,c.recuperacao_status status
                   FROM cofres_usuario c JOIN usuarios u ON u.id=c.usuario_id
                   WHERE c.recuperacao_status='aguardando'
                   UNION ALL
                   SELECT u.id,u.nome,u.usuario,'login' origem,r.status
                   FROM recuperacoes_login r JOIN usuarios u ON u.id=r.usuario_id
                   WHERE r.status='aguardando'""").fetchall()
        return [dict(row) for row in rows]

    def approve(self, user_id: int, origin: str) -> None:
        table = "cofres_usuario" if origin == "cofre" else "recuperacoes_login"
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(f"UPDATE {table} SET recuperacao_status='aprovado' WHERE usuario_id=?"
                                   if origin == "cofre" else
                                   f"UPDATE {table} SET status='aprovado' WHERE usuario_id=?",
                                   (user_id,))
