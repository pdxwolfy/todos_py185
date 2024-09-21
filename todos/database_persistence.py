import os
import logging
import psycopg2
from psycopg2.extras import DictCursor

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    def __init__(self):
        if os.environ.get('FLASK_ENV') == 'production':
            self.connection = psycopg2.connect(os.environ['DATABASE_URL'])
            self._setup_schema()
        else:
            self.connection = psycopg2.connect(dbname="todos")
            self._setup_schema()

    def all_lists(self):
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM lists"
            cursor.execute(query)
            logger.info("Executing query: %s", query)

            results = cursor.fetchall()
            lists = [dict(result) for result in results]
            for lst in lists:
                todos = self._find_todos_for_list(lst['id'])
                lst.setdefault('todos', todos)

            return lists

    def find_list(self, list_id):
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM lists WHERE id = %s"
            cursor.execute(query, (list_id,))
            logger.info("Executing query: %s with list_id: %s",
                        query, list_id)

            lst = dict(cursor.fetchone())
            todos = self._find_todos_for_list(list_id)
            lst.setdefault('todos', todos)
            return lst

    def create_new_list(self, title):
        with self.connection.cursor() as cursor:
            query = "INSERT INTO lists (title) VALUES (%s)"
            cursor.execute(query, (title,))
            logger.info("Executing query: %s with title: %s", query, title)

            self.connection.commit()

    def update_list_by_id(self, list_id, new_title):
        with self.connection.cursor() as cursor:
            query = "UPDATE lists SET title = %s WHERE id = %s"
            cursor.execute(query, (new_title, list_id,))
            logger.info("Executing query: %s with new_title: %s and id: %s",
                        query, new_title, list_id)

            self.connection.commit()

    def delete_list(self, list_id):
        with self.connection.cursor() as cursor:
            query = "DELETE FROM lists WHERE id = %s"
            cursor.execute(query, (list_id,))
            logger.info("Executing query: %s with list_id: %s",
                        query, list_id)

            self.connection.commit()

    def create_new_todo(self, list_id, todo_title):
        with self.connection.cursor() as cursor:
            query = "INSERT INTO todos (list_id, title) VALUES(%s, %s)"
            cursor.execute(query, (list_id, todo_title,))
            logger.info("Executing query: %s with list_id: %s and title %s",
                        query, list_id, todo_title)

            self.connection.commit()

    def delete_todo_from_list(self, list_id, todo_id):
        with self.connection.cursor() as cursor:
            query = "DELETE FROM todos WHERE list_id = %s AND id = %s"
            cursor.execute(query, (list_id, todo_id,))
            logger.info("Executing query: %s with list_id: %s and id: %s",
                        query, list_id, todo_id)

            self.connection.commit()

    def update_todo_status(self, list_id, todo_id, new_status):
        with self.connection.cursor() as cursor:
            query = """
                UPDATE todos SET completed = %s
                WHERE list_id = %s AND id = %s
            """
            cursor.execute(query, (new_status, list_id, todo_id,))
            logger.info("Executing query: %s with new status: %s, "
                        "list_id: %s, and id: %s",
                        query, new_status, list_id, todo_id)

            self.connection.commit()

    def mark_all_todos_completed(self, list_id):
        with self.connection.cursor() as cursor:
            query = "UPDATE todos SET completed = True WHERE list_id = %s "
            cursor.execute(query, (list_id,))
            logger.info("Executing query: %s with list_id: %s",
                        query, list_id)

            self.connection.commit()

    def _find_todos_for_list(self, list_id):
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM todos WHERE list_id = %s"
            cursor.execute(query, (list_id,))
            logger.info("Executing query: %s with list_id: %s", query, list_id)

            return cursor.fetchall()

    def _setup_schema(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'lists';
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE lists (
                        id serial PRIMARY KEY,
                        title text NOT NULL UNIQUE
                    );
                """)

            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'todos';
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE todos (
                        id serial PRIMARY KEY,
                        title text NOT NULL,
                        completed boolean NOT NULL DEFAULT false,
                        list_id integer NOT NULL
                                        ON DELETE CASCADE
                                        REFERENCES lists (id)
                    );
                """)

            self.connection.commit()
