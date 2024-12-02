from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
import os
import dill
import logging

app = Flask(__name__)
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)
UPLOAD_FOLDER = './uploads'  # Folder untuk menyimpan file yang diunggah
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Konfigurasi koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",      # Ganti dengan username MySQL Anda
    password="",      # Ganti dengan password MySQL Anda
    database="saffco"
)

# Cursor untuk database
cursor = db.cursor(dictionary=True)

logging.basicConfig(level=logging.DEBUG)

class Recommender:
    def __init__(self, model_data):
        self.model_data = model_data

    def recommend(self, user_data):
        return self.model_data

    def to_dict(self):
        return {
            "model_data": self.model_data
        }

@app.route('/load-data', methods=['GET'])
def load_data():
    try:
        # Memuat data dari file pickle menggunakan dill
        with open('model_rekomendasiskincare.pkl', 'rb') as f:
            model_data = dill.load(f)

        # Mengembalikan data sebagai response JSON
        return jsonify({"data": model_data}), 200

    except FileNotFoundError:
        return jsonify({"message": "File not found"}), 404
    except Exception as e:
        return jsonify({"message": f"Error loading data: {str(e)}"}), 500
    
# Endpoint untuk login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    # Periksa apakah username ada di database
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful', 'user_id': user['id']}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# Endpoint untuk registrasi
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    # Periksa apakah username sudah digunakan
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    if cursor.fetchone():
        return jsonify({'message': 'Username already exists'}), 400

    # Hash password sebelum disimpan
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Simpan user baru ke database
    insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(insert_query, (username, hashed_password))
    db.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Endpoint untuk reset password
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')

    if not username or not new_password:
        return jsonify({'message': 'Username and new password are required'}), 400

    # Fungsi untuk mengambil user berdasarkan username
    def get_user_by_username(username):
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        return cursor.fetchone()

    # Fungsi untuk menyimpan perubahan password ke database
    def save_user(user_id, new_password):
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        update_query = "UPDATE users SET password = %s WHERE id = %s"
        cursor.execute(update_query, (hashed_password, user_id))
        db.commit()

    user = get_user_by_username(username)
    if user:
        save_user(user['id'], new_password)  # Update password user
        return jsonify({"message": "Password successfully reset"}), 200
    return jsonify({"message": "User not found"}), 404

# Endpoint untuk mengambil profil user
@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    query = "SELECT username, email, no_telepon, alamat FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    if user:
        return jsonify(user), 200
    return jsonify({'message': 'User not found'}), 404

# Route untuk mengupdate profil
@app.route('/profile/<username>', methods=['PUT'])
def update_profile(username):
    if 'file' in request.files:  # Pastikan file diterima
        file = request.files['file']
        if file and allowed_file(file.filename):  # Validasi jenis file
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Simpan file

            # Path relatif untuk gambar
            avatar_url = f'/uploads/{filename}'  # Gambar dapat diakses dengan URL ini
        else:
            return jsonify({'message': 'Invalid file type'}), 400
    else:
        avatar_url = None  # Jika tidak ada gambar yang diupload

    # Ambil data lain (email, no_telepon, alamat)
    data = request.form if request.form else request.json
    email = data.get('email')
    no_telepon = data.get('no_telepon')
    alamat = data.get('alamat')

    # Periksa apakah pengguna ada
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update data pengguna di database
    update_query = """
        UPDATE users
        SET email = %s, no_telepon = %s, alamat = %s
    """
    params = (email, no_telepon, alamat)

    if avatar_url:
        update_query += ", avatar_path = %s"
        params += (avatar_url,)  # Simpan URL gambar di database

    update_query += " WHERE username = %s"
    params += (username,)

    cursor.execute(update_query, params)
    db.commit()

    return jsonify({'message': 'Profile updated successfully', 'avatar_url': avatar_url}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    print(f"Serving file: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/favorites/<username>', methods=['GET'])
def get_favorites(username):
    query = """
        SELECT article_id, product_name, product_image_url
        FROM favorites
        WHERE username = %s
    """
    cursor.execute(query, (username,))
    favorites = cursor.fetchall()

    if favorites:
        return jsonify({'favorites': favorites}), 200
    return jsonify({'message': 'No favorites found'}), 404

@app.route('/articles', methods=['GET'])
def get_articles():
    query = "SELECT title, content, image_path FROM articles"
    cursor.execute(query)
    articles = cursor.fetchall()
    return jsonify({'articles': articles}), 200

# Endpoint untuk menambah artikel
@app.route('/admin/articles', methods=['POST'])
def add_article():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    image_path = data.get('image_path')

    if not title or not content:
        return jsonify({'message': 'Title and content are required'}), 400

    query = "INSERT INTO articles (title, content, image_path) VALUES (%s, %s, %s)"
    cursor.execute(query, (title, content, image_path))
    db.commit()

    return jsonify({'message': 'Article added successfully'}), 201

# Endpoint untuk memperbarui artikel
@app.route('/admin/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    data = request.json
    title = data.get('title')
    content = data.get('content')
    image_path = data.get('image_path')

    # Periksa apakah artikel ada
    query = "SELECT * FROM articles WHERE id = %s"
    cursor.execute(query, (article_id,))
    article = cursor.fetchone()

    if not article:
        return jsonify({'message': 'Article not found'}), 404

    update_query = """
        UPDATE articles
        SET title = %s, content = %s, image_path = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (title, content, image_path, article_id))
    db.commit()

    return jsonify({'message': 'Article updated successfully'}), 200

# Endpoint untuk menghapus artikel
@app.route('/admin/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    query = "DELETE FROM articles WHERE id = %s"
    cursor.execute(query, (article_id,))
    db.commit()

    return jsonify({'message': 'Article deleted successfully'}), 200

# Endpoint untuk menambah produk
@app.route('/admin/products', methods=['POST'])
def add_product():
    data = request.json
    product_name = data.get('product_name')
    product_image_url = data.get('product_image_url')
    description = data.get('description')
    price = data.get('price')

    if not product_name or not price:
        return jsonify({'message': 'Product name and price are required'}), 400

    query = """
        INSERT INTO products (product_name, product_image_url, description, price)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (product_name, product_image_url, description, price))
    db.commit()

    return jsonify({'message': 'Product added successfully'}), 201

# Endpoint untuk memperbarui produk
@app.route('/admin/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    product_name = data.get('product_name')
    product_image_url = data.get('product_image_url')
    description = data.get('description')
    price = data.get('price')

    # Periksa apakah produk ada
    query = "SELECT * FROM products WHERE id = %s"
    cursor.execute(query, (product_id,))
    product = cursor.fetchone()

    if not product:
        return jsonify({'message': 'Product not found'}), 404

    update_query = """
        UPDATE products
        SET product_name = %s, product_image_url = %s, description = %s, price = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (product_name, product_image_url, description, price, product_id))
    db.commit()

    return jsonify({'message': 'Product updated successfully'}), 200

# Endpoint untuk menghapus produk
@app.route('/admin/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    query = "DELETE FROM products WHERE id = %s"
    cursor.execute(query, (product_id,))
    db.commit()

    return jsonify({'message': 'Product deleted successfully'}), 200

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html') 

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
