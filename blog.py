#!/usr/bin/env python
# blog.py
import logging
import socket
import sqlite3

__version__ = '0.1.0'

conn = sqlite3.connect('blog.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS posts
         (title text, body text)''')


def read_index():
    f = open('site/index.html', 'r')
    b = f.readlines()
    f.close()
    return ''.join(b)


def catch_interrupt(func):
    def catcher():
        try:
            func()
        except KeyboardInterrupt:
            logging.info('Shutting down.')
        except Exception as e:
            logging.error(f'Unexpected error: {e}')

    return catcher


def generate_posts_body(rows):
    b = ''
    for row in rows:
        title = row[0]
        body = row[1]

        post = ''
        post += f'<h2>{title}</h2>'
        post += body

        b = post + b

    return b


def replace_tags(site):
    rows = c.execute('SELECT * FROM posts')
    post_count = len(rows.fetchall())
    posts_body = generate_posts_body(c.execute('SELECT * FROM posts'))

    site = site.replace('%POST_COUNT%', f'{post_count}')
    site = site.replace('%POSTS%', f'{posts_body}')
    return site


class BlogServer:
    def __init__(self, port=8000, host='0.0.0.0'):
        self.port = port
        self.host = host
        self.socket = self.make_socket()

    def make_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(1)
        return s

    def __enter__(self):
        return self

    def run(self):
        logging.info(f"Listening on port {self.port}...")

        while True:
            client_connection, client_address = self.socket.accept()
            # request = client_connection.recv(1024).decode()
            site = read_index()
            site = replace_tags(site)
            response = f'HTTP/1.0 200 OK\n\n{site}'
            client_connection.sendall(response.encode())
            client_connection.close()

    def __exit__(self, exc_type, exc_value, traceback):
        logging.info('Closing server socket.')
        self.socket.close()


@catch_interrupt
def main():
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.info(f"Blog Engine v{__version__} starting!")

    with BlogServer() as server:
        server.run()

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
