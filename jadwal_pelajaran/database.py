import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('jadwal.db')
    cursor = conn.cursor()
    
    # Tabel untuk jadwal pelajaran
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jadwal_pelajaran (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hari TEXT NOT NULL,
        jam TEXT NOT NULL,
        mata_pelajaran TEXT NOT NULL,
        guru TEXT NOT NULL,
        ruangan TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabel untuk jadwal piket
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jadwal_piket (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hari TEXT NOT NULL,
        nama_siswa TEXT NOT NULL,
        tugas TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Trigger untuk update timestamp
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_jadwal_pelajaran_timestamp 
    AFTER UPDATE ON jadwal_pelajaran
    BEGIN
        UPDATE jadwal_pelajaran SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_jadwal_piket_timestamp 
    AFTER UPDATE ON jadwal_piket
    BEGIN
        UPDATE jadwal_piket SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('jadwal.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_stats():
    conn = get_db_connection()
    
    # Hitung total jadwal pelajaran
    total_pelajaran = conn.execute('SELECT COUNT(*) as count FROM jadwal_pelajaran').fetchone()['count']
    
    # Hitung total jadwal piket
    total_piket = conn.execute('SELECT COUNT(*) as count FROM jadwal_piket').fetchone()['count']
    
    # Hitung jadwal per hari
    pelajaran_per_hari = conn.execute('''
        SELECT hari, COUNT(*) as count 
        FROM jadwal_pelajaran 
        GROUP BY hari
        ORDER BY CASE hari 
            WHEN 'Senin' THEN 1
            WHEN 'Selasa' THEN 2
            WHEN 'Rabu' THEN 3
            WHEN 'Kamis' THEN 4
            WHEN 'Jumat' THEN 5
            WHEN 'Sabtu' THEN 6
            ELSE 7 END
    ''').fetchall()
    
    piket_per_hari = conn.execute('''
        SELECT hari, COUNT(*) as count 
        FROM jadwal_piket 
        GROUP BY hari
        ORDER BY CASE hari 
            WHEN 'Senin' THEN 1
            WHEN 'Selasa' THEN 2
            WHEN 'Rabu' THEN 3
            WHEN 'Kamis' THEN 4
            WHEN 'Jumat' THEN 5
            WHEN 'Sabtu' THEN 6
            ELSE 7 END
    ''').fetchall()
    
    conn.close()
    
    return {
        'total_pelajaran': total_pelajaran,
        'total_piket': total_piket,
        'pelajaran_per_hari': pelajaran_per_hari,
        'piket_per_hari': piket_per_hari
    }