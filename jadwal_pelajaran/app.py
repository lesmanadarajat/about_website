from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import init_db, get_db_connection
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Inisialisasi database
init_db()

# Helper function untuk mengubah Row menjadi dictionary
def row_to_dict(row):
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}

# Halaman utama
@app.route('/')
def index():
    return render_template('index.html')

# Halaman jadwal pelajaran
@app.route('/jadwal-pelajaran')
def jadwal_pelajaran():
    conn = get_db_connection()
    
    # Ambil data jadwal dan kelompokkan berdasarkan hari
    rows = conn.execute('''
        SELECT * FROM jadwal_pelajaran 
        ORDER BY CASE hari 
            WHEN 'Senin' THEN 1
            WHEN 'Selasa' THEN 2
            WHEN 'Rabu' THEN 3
            WHEN 'Kamis' THEN 4
            WHEN 'Jumat' THEN 5
            WHEN 'Sabtu' THEN 6
            ELSE 7 END, jam
    ''').fetchall()
    
    # Konversi Row objects ke list of dictionaries
    jadwal = [row_to_dict(row) for row in rows]
    
    # Kelompokkan berdasarkan hari
    jadwal_per_hari = {}
    for item in jadwal:
        hari = item['hari']
        if hari not in jadwal_per_hari:
            jadwal_per_hari[hari] = []
        jadwal_per_hari[hari].append(item)
    
    conn.close()
    return render_template('jadwal_pelajaran.html', jadwal_per_hari=jadwal_per_hari)

# Halaman detail hari untuk jadwal pelajaran
@app.route('/hari/<nama_hari>')
def hari_detail(nama_hari):
    conn = get_db_connection()
    
    # Ambil data jadwal untuk hari tertentu
    rows = conn.execute('''
        SELECT * FROM jadwal_pelajaran 
        WHERE hari = ?
        ORDER BY jam
    ''', (nama_hari,)).fetchall()
    
    jadwal = [row_to_dict(row) for row in rows]
    
    conn.close()
    return render_template('hari_detail.html', hari=nama_hari, jadwal=jadwal, tipe='pelajaran')

# API untuk menambah jadwal pelajaran (multiple entries)
@app.route('/api/tambah-pelajaran-batch', methods=['POST'])
def tambah_pelajaran_batch():
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    for item in data['items']:
        cursor.execute('''
            INSERT INTO jadwal_pelajaran (hari, jam, mata_pelajaran, guru, ruangan)
            VALUES (?, ?, ?, ?, ?)
        ''', (item['hari'], item['jam'], item['mata_pelajaran'], item['guru'], item['ruangan']))
        
        # Ambil data terbaru untuk dikembalikan
        new_id = cursor.lastrowid
        new_row = conn.execute('SELECT * FROM jadwal_pelajaran WHERE id = ?', (new_id,)).fetchone()
        results.append(row_to_dict(new_row))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'data': results
    })

# API untuk menghapus jadwal pelajaran
@app.route('/api/hapus-pelajaran/<int:id>', methods=['DELETE'])
def hapus_pelajaran(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM jadwal_pelajaran WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API untuk mengupdate jadwal pelajaran
@app.route('/api/update-pelajaran/<int:id>', methods=['PUT'])
def update_pelajaran(id):
    data = request.get_json()
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE jadwal_pelajaran 
        SET hari = ?, jam = ?, mata_pelajaran = ?, guru = ?, ruangan = ?
        WHERE id = ?
    ''', (data['hari'], data['jam'], data['mata_pelajaran'], data['guru'], data['ruangan'], id))
    conn.commit()
    
    # Ambil data yang sudah diupdate
    updated_row = conn.execute('SELECT * FROM jadwal_pelajaran WHERE id = ?', (id,)).fetchone()
    updated_data = row_to_dict(updated_row)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': updated_data
    })

# Halaman jadwal piket
@app.route('/jadwal-piket')
def jadwal_piket():
    conn = get_db_connection()
    
    # Ambil data piket dan kelompokkan berdasarkan hari
    rows = conn.execute('''
        SELECT * FROM jadwal_piket 
        ORDER BY CASE hari 
            WHEN 'Senin' THEN 1
            WHEN 'Selasa' THEN 2
            WHEN 'Rabu' THEN 3
            WHEN 'Kamis' THEN 4
            WHEN 'Jumat' THEN 5
            WHEN 'Sabtu' THEN 6
            ELSE 7 END
    ''').fetchall()
    
    # Konversi Row objects ke list of dictionaries
    piket = [row_to_dict(row) for row in rows]
    
    # Kelompokkan berdasarkan hari
    piket_per_hari = {}
    for item in piket:
        hari = item['hari']
        if hari not in piket_per_hari:
            piket_per_hari[hari] = []
        piket_per_hari[hari].append(item)
    
    conn.close()
    return render_template('jadwal_piket.html', piket_per_hari=piket_per_hari)

# Halaman detail hari untuk jadwal piket
@app.route('/hari-piket/<nama_hari>')
def hari_piket_detail(nama_hari):
    conn = get_db_connection()
    
    # Ambil data piket untuk hari tertentu
    rows = conn.execute('''
        SELECT * FROM jadwal_piket 
        WHERE hari = ?
    ''', (nama_hari,)).fetchall()
    
    piket = [row_to_dict(row) for row in rows]
    
    conn.close()
    return render_template('hari_detail.html', hari=nama_hari, jadwal=piket, tipe='piket')

# API untuk menambah jadwal piket (multiple entries)
@app.route('/api/tambah-piket-batch', methods=['POST'])
def tambah_piket_batch():
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    for item in data['items']:
        cursor.execute('''
            INSERT INTO jadwal_piket (hari, nama_siswa, tugas)
            VALUES (?, ?, ?)
        ''', (item['hari'], item['nama_siswa'], item['tugas']))
        
        # Ambil data terbaru untuk dikembalikan
        new_id = cursor.lastrowid
        new_row = conn.execute('SELECT * FROM jadwal_piket WHERE id = ?', (new_id,)).fetchone()
        results.append(row_to_dict(new_row))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'data': results
    })

# API untuk menghapus jadwal piket
@app.route('/api/hapus-piket/<int:id>', methods=['DELETE'])
def hapus_piket(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM jadwal_piket WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API untuk mengupdate jadwal piket
@app.route('/api/update-piket/<int:id>', methods=['PUT'])
def update_piket(id):
    data = request.get_json()
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE jadwal_piket 
        SET hari = ?, nama_siswa = ?, tugas = ?
        WHERE id = ?
    ''', (data['hari'], data['nama_siswa'], data['tugas'], id))
    conn.commit()
    
    # Ambil data yang sudah diupdate
    updated_row = conn.execute('SELECT * FROM jadwal_piket WHERE id = ?', (id,)).fetchone()
    updated_data = row_to_dict(updated_row)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': updated_data
    })

# API untuk mendapatkan data berdasarkan hari
@app.route('/api/jadwal-hari/<nama_hari>/<tipe>')
def get_jadwal_by_hari(nama_hari, tipe):
    conn = get_db_connection()
    
    if tipe == 'pelajaran':
        rows = conn.execute('SELECT * FROM jadwal_pelajaran WHERE hari = ? ORDER BY jam', (nama_hari,)).fetchall()
    else:  # piket
        rows = conn.execute('SELECT * FROM jadwal_piket WHERE hari = ?', (nama_hari,)).fetchall()
    
    data = [row_to_dict(row) for row in rows]
    
    conn.close()
    return jsonify({
        'success': True,
        'data': data
    })

if __name__ == '__main__':

    app.run(debug=True, port=5000)
