import pymysql
import re
from contextlib import contextmanager
import hashlib

class DatabaseManager:
    def __init__(self):
        self.connection_params = {
            'host': "127.0.0.1",
            'user': "",
            'password': "",
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self.init_databases()

    @contextmanager
    def get_connection(self, database_name):
        connection = None
        try:
            params = self.connection_params.copy()
            params['database'] = database_name
            connection = pymysql.connect(**params)
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.commit()
                connection.close()

    def init_databases(self):
        try:
            with pymysql.connect(**self.connection_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("CREATE DATABASE IF NOT EXISTS users")
                    cursor.execute("CREATE DATABASE IF NOT EXISTS courses")

            with self.get_connection('users') as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS customers (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password VARCHAR(255) NOT NULL,
                            image_path VARCHAR(255),
                            security_question TEXT,
                            security_answer VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_courses (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(255),
                            course_title VARCHAR(255),
                            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (username) REFERENCES customers(username) ON DELETE CASCADE,
                            UNIQUE KEY unique_enrollment (username, course_title)
                        )
                    """)

            with self.get_connection('courses') as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS courseinfo (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            title VARCHAR(255) UNIQUE NOT NULL,
                            description MEDIUMTEXT,
                            photo_path VARCHAR(255),
                            watch_hours INT,
                            class_day VARCHAR(20),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
        except Exception as e:
            print(f"Error during database initialization: {e}")

class UserManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def _validate_username(self, username):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,19}$', username):
            return False, "Username must be 4-20 characters long, start with a letter, and contain only letters, numbers, or underscores."
        return True, "Valid"

    def _validate_email(self, email):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format."
        return True, "Valid"

    def _validate_password(self, password):
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password):
            return False, "Password must be at least 8 characters long and contain uppercase, lowercase, and numbers."
        return True, "Valid"

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, email, password, confirm_password, image_path, security_question, security_answer):
        is_valid_user, _ = self._validate_username(username)
        if not is_valid_user:
            return False, "Invalid username."

        is_valid_email, _ = self._validate_email(email)
        if not is_valid_email:
            return False, "Invalid email."

        if password != confirm_password:
            return False, "Passwords do not match."

        is_valid_pass, _ = self._validate_password(password)
        if not is_valid_pass:
            return False, "Weak password."

        hashed_password = self._hash_password(password)

        try:
            with self.db_manager.get_connection('users') as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO customers (username, email, password, image_path, security_question, security_answer)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (username, email, hashed_password, image_path, security_question, security_answer))
            return True, "User created."
        except pymysql.err.IntegrityError as e:
            if 'username' in str(e):
                return False, "Username already taken."
            if 'email' in str(e):
                return False, "Email already in use."
            return False, "Database error."

    def check_credentials(self, username, password):
        hashed = self._hash_password(password)
        user = self.get_user(username)
        return user and user['password'] == hashed

    def get_user(self, username):
        with self.db_manager.get_connection('users') as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM customers WHERE username = %s", (username,))
                return cursor.fetchone()

    def get_all_users(self):
        with self.db_manager.get_connection('users') as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email, image_path, created_at FROM customers")
                return cursor.fetchall()

    def reset_password(self, username, security_answer, new_password):
        user = self.get_user(username)
        if not user or user['security_answer'] != security_answer:
            return False, "Invalid security answer."
        is_valid, _ = self._validate_password(new_password)
        if not is_valid:
            return False, "Weak password."
        hashed = self._hash_password(new_password)
        with self.db_manager.get_connection('users') as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE customers SET password = %s WHERE username = %s", (hashed, username))
        return True, "Password reset."

    def update_user(self, username, email, password, image_path):
        is_valid_email, _ = self._validate_email(email)
        if not is_valid_email:
            raise ValueError("Invalid email.")
        params = [email]
        sql = "UPDATE customers SET email=%s"
        if password:
            is_valid, _ = self._validate_password(password)
            if not is_valid:
                raise ValueError("Weak password.")
            hashed = self._hash_password(password)
            sql += ", password=%s"
            params.append(hashed)
        if image_path:
            sql += ", image_path=%s"
            params.append(image_path)
        sql += " WHERE username=%s"
        params.append(username)
        with self.db_manager.get_connection('users') as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, tuple(params))
                except pymysql.err.IntegrityError:
                    raise ValueError("Email already exists.")

    def add_course_to_user(self, username, course_title):
        with self.db_manager.get_connection('users') as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("INSERT INTO user_courses (username, course_title) VALUES (%s, %s)", (username, course_title))
                except pymysql.err.IntegrityError:
                    pass

    def get_user_courses(self, username):
        with self.db_manager.get_connection('users') as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT course_title FROM user_courses WHERE username = %s", (username,))
                return cursor.fetchall()

class CourseManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def create_course(self, title, description, photo_path, watch_hours, class_day):
        with self.db_manager.get_connection('courses') as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO courseinfo (title, description, photo_path, watch_hours, class_day)
                    VALUES (%s, %s, %s, %s, %s)
                """, (title, description, photo_path, watch_hours, class_day))

    def get_course(self, title):
        with self.db_manager.get_connection('courses') as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM courseinfo WHERE title = %s", (title,))
                return cursor.fetchone()

    def get_all_courses(self):
        with self.db_manager.get_connection('courses') as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM courseinfo")
                return cursor.fetchall()

    def update_course(self, title, description, photo_path, watch_hours, class_day):
        with self.db_manager.get_connection('courses') as conn:
            with conn.cursor() as cursor:
                if photo_path:
                    sql = "UPDATE courseinfo SET description = %s, photo_path = %s, watch_hours = %s, class_day = %s WHERE title = %s"
                    params = (description, photo_path, watch_hours, class_day, title)
                else:
                    sql = "UPDATE courseinfo SET description = %s, watch_hours = %s, class_day = %s WHERE title = %s"
                    params = (description, watch_hours, class_day, title)
                cursor.execute(sql, params)

    def delete_course(self, title):
        with self.db_manager.get_connection('courses') as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM courseinfo WHERE title = %s", (title,))


if __name__ == "__main__":
    print("Attempting to initialize databases...")
    db_manager = DatabaseManager()
    print("Database initialization process finished.")