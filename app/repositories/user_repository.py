from contextlib import closing
from dataclasses import dataclass
from app.database.connection import Database
from app.models.user import User


@dataclass(frozen=True, slots=True)
class UserCredentials:
    user: User
    password_hash: str


class UserRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def count(self) -> int:
        with closing(self.database.connect()) as connection:
            row = connection.execute("SELECT COUNT(*) total FROM usuarios").fetchone()
        return int(row["total"])

    def find_credentials(self, username: str) -> UserCredentials | None:
        with closing(self.database.connect()) as connection:
            row = connection.execute(
                "SELECT id,nome,usuario,senha,tipo,ativo,cargo FROM usuarios WHERE usuario=? COLLATE NOCASE",
                (username,),
            ).fetchone()
        if row is None:
            return None
        user = User(row["id"], row["nome"], row["usuario"], row["tipo"],
                    bool(row["ativo"]), row["cargo"])
        return UserCredentials(user, row["senha"])

    def create_admin(self, name: str, username: str, password_hash: str) -> User:
        return self.create(name, username, password_hash, "Administrador")

    def create(self, name: str, username: str, password_hash: str,
               role: str = "Usuário") -> User:
        with closing(self.database.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO usuarios(nome,usuario,senha,tipo,ativo) VALUES(?,?,?,?,1)",
                    (name, username, password_hash, role),
                )
                user_id = int(cursor.lastrowid)
        return User(user_id, name, username, role, True)

    def update_password(self, user_id: int, password_hash: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("UPDATE usuarios SET senha=? WHERE id=?", (password_hash, user_id))

    def request_login_recovery(self, username: str) -> bool:
        with closing(self.database.connect()) as connection:
            with connection:
                row = connection.execute(
                    "SELECT id FROM usuarios WHERE usuario=? COLLATE NOCASE AND ativo=1",
                    (username,),
                ).fetchone()
                if row is None:
                    return False
                connection.execute(
                    """INSERT INTO recuperacoes_login(usuario_id,status)
                       VALUES(?,'aguardando')
                       ON CONFLICT(usuario_id) DO UPDATE SET
                           status='aguardando', solicitado_em=CURRENT_TIMESTAMP""",
                    (row["id"],),
                )
        return True

    def reset_password_if_approved(self, username: str, password_hash: str) -> bool:
        with closing(self.database.connect()) as connection:
            with connection:
                row = connection.execute(
                    """SELECT u.id FROM usuarios u JOIN recuperacoes_login r ON r.usuario_id=u.id
                       WHERE u.usuario=? COLLATE NOCASE AND r.status='aprovado'""",
                    (username,)).fetchone()
                if row is None:
                    return False
                connection.execute("UPDATE usuarios SET senha=? WHERE id=?", (password_hash, row["id"]))
                connection.execute("DELETE FROM recuperacoes_login WHERE usuario_id=?", (row["id"],))
        return True

    def list_all(self) -> list[User]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT id,nome,usuario,tipo,ativo,cargo FROM usuarios ORDER BY nome COLLATE NOCASE"
            ).fetchall()
        return [User(row["id"], row["nome"], row["usuario"], row["tipo"],
                     bool(row["ativo"]), row["cargo"])
                for row in rows]

    def update_user(self, user_id: int, name: str, username: str,
                    password_hash: str | None = None,
                    role: str | None = None) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    "UPDATE usuarios SET nome=?,usuario=? WHERE id=?",
                    (name, username, user_id))
                if role is not None:
                    connection.execute(
                        "UPDATE usuarios SET tipo=? WHERE id=?", (role, user_id))
                if password_hash:
                    connection.execute(
                        "UPDATE usuarios SET senha=? WHERE id=?", (password_hash, user_id))

    def set_active(self, user_id: int, active: bool) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("UPDATE usuarios SET ativo=? WHERE id=?", (int(active), user_id))

    def update_profile(self, user_id: int, name: str, job: str,
                       password_hash: str | None = None) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    "UPDATE usuarios SET nome=?,cargo=? WHERE id=?", (name, job, user_id))
                if password_hash is not None:
                    connection.execute("UPDATE usuarios SET senha=? WHERE id=?",
                                       (password_hash, user_id))
