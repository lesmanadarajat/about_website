import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'raport_secret_key_2024_secure_login'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

# Pastikan folder uploads ada
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buat tabel siswa jika belum ada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS siswa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            absen INTEGER UNIQUE,
            nama TEXT NOT NULL,
            foto TEXT,
            b_inggris INTEGER DEFAULT 0,
            b_indo INTEGER DEFAULT 0,
            b_sunda INTEGER DEFAULT 0,
            mtk INTEGER DEFAULT 0,
            fisika INTEGER DEFAULT 0,
            kimia INTEGER DEFAULT 0,
            coding INTEGER DEFAULT 0,
            pjok INTEGER DEFAULT 0,
            pkn INTEGER DEFAULT 0,
            agama INTEGER DEFAULT 0
        )
    ''')
    
    # Buat tabel admin jika belum ada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Tambahkan admin default jika belum ada
    cursor.execute("SELECT COUNT(*) as count FROM admin")
    count = cursor.fetchone()['count']
    if count == 0:
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', 
                      ('admin', hashed_password))
    
    conn.commit()
    conn.close()

# Login required decorator dengan functools.wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Silakan login terlebih dahulu!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Inisialisasi database saat aplikasi dimulai
with app.app_context():
    init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        absen = request.form.get('absen')
        if not absen:
            flash('Masukkan nomor absen!', 'error')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        siswa = conn.execute('SELECT * FROM siswa WHERE absen = ?', (absen,)).fetchone()
        conn.close()
        
        if siswa is None:
            flash('Data siswa tidak ditemukan!', 'error')
            return redirect(url_for('index'))
        
        # Hitung total nilai
        total_nilai = (
            siswa['b_inggris'] + siswa['b_indo'] + siswa['b_sunda'] +
            siswa['mtk'] + siswa['fisika'] + siswa['kimia'] +
            siswa['coding'] + siswa['pjok'] + siswa['pkn'] + siswa['agama']
        )
        
        # Dapatkan ranking
        conn = get_db_connection()
        all_siswa = conn.execute('''
            SELECT id, 
                   (b_inggris + b_indo + b_sunda + mtk + fisika + kimia + coding + pjok + pkn + agama) as total 
            FROM siswa 
            ORDER BY total DESC
        ''').fetchall()
        conn.close()
        
        # Temukan ranking siswa
        ranking = 1
        for s in all_siswa:
            if s['id'] == siswa['id']:
                break
            ranking += 1
        
        return render_template('result.html', 
                             siswa=siswa, 
                             total_nilai=total_nilai, 
                             ranking=ranking,
                             total_siswa=len(all_siswa))
    
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, redirect ke admin
    if 'admin_logged_in' in session:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    siswa_list = conn.execute('SELECT * FROM siswa ORDER BY absen').fetchall()
    conn.close()
    return render_template('admin.html', siswa_list=siswa_list)

@app.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        absen = request.form['absen']
        nama = request.form['nama']
        
        # Upload foto jika ada
        foto = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{absen}_{nama}.{ext}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto = filename
        
        # Ambil nilai dari form dengan default 0
        nilai_data = {}
        nilai_fields = ['b_inggris', 'b_indo', 'b_sunda', 'mtk', 'fisika',
                       'kimia', 'coding', 'pjok', 'pkn', 'agama']
        
        for field in nilai_fields:
            value = request.form.get(field, '0')
            # Convert to int, default to 0 if empty
            nilai_data[field] = int(value) if value and value.strip() != '' else 0
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO siswa (absen, nama, foto, b_inggris, b_indo, b_sunda, 
                                  mtk, fisika, kimia, coding, pjok, pkn, agama)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (absen, nama, foto,
                  nilai_data['b_inggris'], nilai_data['b_indo'], nilai_data['b_sunda'],
                  nilai_data['mtk'], nilai_data['fisika'], nilai_data['kimia'],
                  nilai_data['coding'], nilai_data['pjok'], nilai_data['pkn'],
                  nilai_data['agama']))
            conn.commit()
            conn.close()
            flash('Data siswa berhasil ditambahkan!', 'success')
            return redirect(url_for('admin'))
        except sqlite3.IntegrityError:
            flash('Nomor absen sudah terdaftar!', 'error')
            return redirect(url_for('tambah'))
        except Exception as e:
            flash(f'Terjadi kesalahan: {str(e)}', 'error')
            return redirect(url_for('tambah'))
    
    return render_template('tambah.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        absen = request.form['absen']
        nama = request.form['nama']
        
        # Upload foto baru jika ada
        foto = request.form.get('foto_lama')
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                # Hapus foto lama jika ada
                if foto and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], foto)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], foto))
                
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{absen}_{nama}.{ext}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto = filename
        
        # Ambil nilai dari form
        nilai_fields = [
            'b_inggris', 'b_indo', 'b_sunda', 'mtk', 'fisika',
            'kimia', 'coding', 'pjok', 'pkn', 'agama'
        ]
        nilai_data = {}
        for field in nilai_fields:
            value = request.form.get(field, '0')
            nilai_data[field] = int(value) if value and value.strip() != '' else 0
        
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE siswa 
            SET absen = ?, nama = ?, foto = ?, 
                b_inggris = ?, b_indo = ?, b_sunda = ?, 
                mtk = ?, fisika = ?, kimia = ?, 
                coding = ?, pjok = ?, pkn = ?, agama = ?
            WHERE id = ?
        ''', (absen, nama, foto,
              nilai_data['b_inggris'], nilai_data['b_indo'], nilai_data['b_sunda'],
              nilai_data['mtk'], nilai_data['fisika'], nilai_data['kimia'],
              nilai_data['coding'], nilai_data['pjok'], nilai_data['pkn'],
              nilai_data['agama'], id))
        
        conn.commit()
        conn.close()
        flash('Data siswa berhasil diupdate!', 'success')
        return redirect(url_for('admin'))
    
    siswa = conn.execute('SELECT * FROM siswa WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if siswa is None:
        flash('Data siswa tidak ditemukan!', 'error')
        return redirect(url_for('admin'))
    
    return render_template('edit.html', siswa=siswa)

@app.route('/hapus/<int:id>')
@login_required
def hapus(id):
    conn = get_db_connection()
    
    # Hapus foto jika ada
    siswa = conn.execute('SELECT foto FROM siswa WHERE id = ?', (id,)).fetchone()
    if siswa['foto'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], siswa['foto'])):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], siswa['foto']))
    
    conn.execute('DELETE FROM siswa WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Data siswa berhasil dihapus!', 'success')
    return redirect(url_for('admin'))

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Password baru tidak cocok!', 'error')
            return redirect(url_for('change_password'))
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', 
                           (session['admin_username'],)).fetchone()
        
        if admin and check_password_hash(admin['password'], current_password):
            hashed_password = generate_password_hash(new_password)
            conn.execute('UPDATE admin SET password = ? WHERE username = ?',
                        (hashed_password, session['admin_username']))
            conn.commit()
            conn.close()
            flash('Password berhasil diubah!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Password saat ini salah!', 'error')
            return redirect(url_for('change_password'))
    
    return render_template('change_password.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)