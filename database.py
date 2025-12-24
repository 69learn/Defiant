import mysql.connector
from mysql.connector import Error
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
        return connection
    except Error as e:
        print(f"خطا در اتصال به دیتابیس: {e}")
        return None

def init_database():
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول تانل‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tunnels (
                tunnel_id VARCHAR(255) PRIMARY KEY,
                user_id BIGINT NOT NULL,
                tunnel_type VARCHAR(50),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول کانفیگ‌های تانل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tunnel_configs (
                config_id INT AUTO_INCREMENT PRIMARY KEY,
                tunnel_id VARCHAR(255) NOT NULL,
                iran_ip VARCHAR(50),
                iran_port INT,
                iran_username VARCHAR(255),
                iran_password VARCHAR(255),
                foreign_ip VARCHAR(50),
                foreign_port INT,
                foreign_username VARCHAR(255),
                foreign_password VARCHAR(255),
                transport_type VARCHAR(50),
                subdomain VARCHAR(255),
                tunnel_ports VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tunnel_id) REFERENCES tunnels(tunnel_id)
            )
        ''')
        
        # جدول پنل‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS panels (
                panel_id VARCHAR(255) PRIMARY KEY,
                user_id BIGINT NOT NULL,
                panel_type VARCHAR(50),
                server_ip VARCHAR(50),
                server_port INT,
                username VARCHAR(255),
                password VARCHAR(255),
                web_path VARCHAR(255),
                server_username VARCHAR(255),
                server_password VARCHAR(255),
                ssh_port INT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subdomain VARCHAR(255),
                db_password VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول مدیریت دسترسی‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_access (
                access_id INT AUTO_INCREMENT PRIMARY KEY,
                owner_id BIGINT NOT NULL,
                admin_id BIGINT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(user_id),
                FOREIGN KEY (admin_id) REFERENCES users(user_id),
                UNIQUE KEY unique_access (owner_id, admin_id)
            )
        ''')
        
        # Migration for panels table
        try:
            cursor.execute('''
                ALTER TABLE panels 
                ADD COLUMN IF NOT EXISTS web_path VARCHAR(255) AFTER password
            ''')
            print("[v0] ✓ Migration: web_path column checked/added to panels table")
        except Error as migration_error:
            if migration_error.errno == 1060:
                print("[v0] ✓ Migration: web_path column already exists")
            else:
                print(f"[v0] Migration warning: {migration_error}")
        
        try:
            cursor.execute('''
                ALTER TABLE panels 
                ADD COLUMN subdomain VARCHAR(255) AFTER ssh_port
            ''')
            print("[v0] ✓ Migration: subdomain column added to panels table")
        except Error as migration_error:
            if migration_error.errno == 1060:
                print("[v0] ✓ Migration: subdomain column already exists")
            else:
                print(f"[v0] Migration warning: {migration_error}")
        
        try:
            cursor.execute('''
                ALTER TABLE panels 
                ADD COLUMN db_password VARCHAR(255) AFTER subdomain
            ''')
            print("[v0] ✓ Migration: db_password column added to panels table")
        except Error as migration_error:
            if migration_error.errno == 1060:
                print("[v0] ✓ Migration: db_password column already exists")
            else:
                print(f"[v0] Migration warning: {migration_error}")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS force_join_channels (
                channel_id VARCHAR(255) PRIMARY KEY,
                channel_username VARCHAR(255),
                channel_title VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS force_join_settings (
                id INT PRIMARY KEY DEFAULT 1,
                is_enabled BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default settings if not exists
        cursor.execute('''
            INSERT IGNORE INTO force_join_settings (id, is_enabled) VALUES (1, FALSE)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wallets (
                user_id BIGINT PRIMARY KEY,
                balance DECIMAL(15, 2) DEFAULT 0.00,
                phone_number VARCHAR(20),
                phone_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount DECIMAL(15, 2) NOT NULL,
                payment_method ENUM('card_to_card', 'crypto_gateway') NOT NULL,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                receipt_photo VARCHAR(500),
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        connection.commit()
        print("دیتابیس با موفقیت ایجاد شد")
        return True
        
    except Error as e:
        print(f"خطا در ایجاد جداول: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_user(user_id, username, first_name):
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT IGNORE INTO users (user_id, username, first_name)
            VALUES (%s, %s, %s)
        ''', (user_id, username, first_name))
        connection.commit()
        return True
    except Error as e:
        print(f"خطا: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_backhaul_tunnel(tunnel_id, user_id, iran_ip, iran_port, iran_username, iran_password,
                        foreign_ip, foreign_port, foreign_username, foreign_password,
                        transport_type, subdomain=None, tunnel_ports=None):
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        # Insert into tunnels table
        cursor.execute('''
            INSERT INTO tunnels (tunnel_id, user_id, tunnel_type, status)
            VALUES (%s, %s, %s, %s)
        ''', (tunnel_id, user_id, 'backhaul', 'active'))
        
        # Insert into tunnel_configs table with all details
        cursor.execute('''
            INSERT INTO tunnel_configs 
            (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
             foreign_ip, foreign_port, foreign_username, foreign_password,
             transport_type, subdomain, tunnel_ports)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
              foreign_ip, foreign_port, foreign_username, foreign_password,
              transport_type, subdomain, tunnel_ports))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره تانل: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_vxlan_tunnel(tunnel_id, user_id, iran_ip, iran_port, iran_username, iran_password,
                     foreign_ip, foreign_port, foreign_username, foreign_password, service_ports):
    """Add Vxlan tunnel to database with SSH credentials"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO tunnels (tunnel_id, user_id, tunnel_type, status)
            VALUES (%s, %s, %s, %s)
        ''', (tunnel_id, user_id, 'vxlan', 'active'))
        
        cursor.execute('''
            INSERT INTO tunnel_configs 
            (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
             foreign_ip, foreign_port, foreign_username, foreign_password, tunnel_ports)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
              foreign_ip, foreign_port, foreign_username, foreign_password, service_ports))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره تانل Vxlan: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_mux_tunnel(tunnel_id, user_id, iran_ip, iran_port, iran_username, iran_password,
                   foreign_ip, foreign_port, foreign_username, foreign_password, ports):
    """Add Mux tunnel to database with SSH credentials"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO tunnels (tunnel_id, user_id, tunnel_type, status)
            VALUES (%s, %s, %s, %s)
        ''', (tunnel_id, user_id, 'mux', 'active'))
        
        cursor.execute('''
            INSERT INTO tunnel_configs 
            (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
             foreign_ip, foreign_port, foreign_username, foreign_password, tunnel_ports)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
              foreign_ip, foreign_port, foreign_username, foreign_password, ports))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره تانل Mux: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_chisel_tunnel(tunnel_id, user_id, iran_ip, iran_port, iran_username, iran_password,
                      foreign_ip, foreign_port, foreign_username, foreign_password, config_ports):
    """Add Chisel tunnel to database with SSH credentials"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO tunnels (tunnel_id, user_id, tunnel_type, status)
            VALUES (%s, %s, %s, %s)
        ''', (tunnel_id, user_id, 'chisel', 'active'))
        
        cursor.execute('''
            INSERT INTO tunnel_configs 
            (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
             foreign_ip, foreign_port, foreign_username, foreign_password, tunnel_ports)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (tunnel_id, iran_ip, iran_port, iran_username, iran_password,
              foreign_ip, foreign_port, foreign_username, foreign_password, config_ports))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره تانل Chisel: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_user_tunnels(user_id):
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT t.tunnel_id, t.tunnel_type, t.status, tc.iran_ip, tc.foreign_ip, 
                   tc.transport_type, tc.tunnel_ports, t.created_at
            FROM tunnels t
            LEFT JOIN tunnel_configs tc ON t.tunnel_id = tc.tunnel_id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
        ''', (user_id,))
        
        tunnels = cursor.fetchall()
        return tunnels
    except Error as e:
        print(f"خطا: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_user_panels(user_id):
    """Get all panels for a specific user"""
    print(f"[v0] get_user_panels called for user_id={user_id}")
    
    connection = get_connection()
    if connection is None:
        print(f"[v0] ✗ Database connection failed in get_user_panels!")
        return None
    
    print(f"[v0] ✓ Database connection established in get_user_panels")
    
    cursor = connection.cursor()
    try:
        print(f"[v0] Executing SELECT query for user_id={user_id}...")
        cursor.execute('''
            SELECT panel_id, panel_type, server_ip, server_port, 
                   username, password, web_path, status, created_at, subdomain, db_password
            FROM panels
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', (user_id,))
        
        panels = cursor.fetchall()
        print(f"[v0] Query executed, fetched {len(panels) if panels else 0} panels")
        if panels:
            for i, panel in enumerate(panels):
                print(f"[v0]   Panel {i+1}: panel_id={panel[0]}, type={panel[1]}, ip={panel[2]}")
        else:
            print(f"[v0]   No panels found for user_id={user_id}")
        
        return panels
    except Error as e:
        print(f"[v0] ✗ Database error in get_user_panels:")
        print(f"[v0]   Error message: {str(e)}")
        return None
    finally:
        cursor.close()
        connection.close()
        print(f"[v0] Database connection closed in get_user_panels")

def get_tunnel_config(tunnel_id):
    """Get tunnel configuration details"""
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT t.tunnel_type, tc.iran_ip, tc.iran_port, tc.iran_username, tc.iran_password,
                   tc.foreign_ip, tc.foreign_port, tc.foreign_username, tc.foreign_password
            FROM tunnels t
            LEFT JOIN tunnel_configs tc ON t.tunnel_id = tc.tunnel_id
            WHERE t.tunnel_id = %s
        ''', (tunnel_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'tunnel_type': result[0],
                'iran_ip': result[1],
                'iran_port': result[2],
                'iran_username': result[3],
                'iran_password': result[4],
                'foreign_ip': result[5],
                'foreign_port': result[6],
                'foreign_username': result[7],
                'foreign_password': result[8]
            }
        return None
    except Error as e:
        print(f"خطا در دریافت کانفیگ تانل: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def delete_tunnel(tunnel_id):
    """Delete tunnel and its configs from database"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        # Delete from tunnel_configs first (foreign key constraint)
        cursor.execute('DELETE FROM tunnel_configs WHERE tunnel_id = %s', (tunnel_id,))
        
        # Delete from tunnels
        cursor.execute('DELETE FROM tunnels WHERE tunnel_id = %s', (tunnel_id,))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در حذف تانل: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_3xui_panel(panel_id, user_id, server_ip, server_port, username, password, web_path, server_username, server_password, ssh_port):
    """Add 3x-ui panel to database"""
    print(f"[v0] add_3xui_panel called with:")
    print(f"[v0]   panel_id={panel_id}")
    print(f"[v0]   user_id={user_id}")
    print(f"[v0]   server_ip={server_ip}")
    print(f"[v0]   server_port={server_port}")
    print(f"[v0]   username={username}")
    print(f"[v0]   web_path={web_path}")
    print(f"[v0]   server_username={server_username}")
    print(f"[v0]   ssh_port={ssh_port}")
    
    connection = get_connection()
    if connection is None:
        print(f"[v0] ✗ Database connection failed!")
        return False
    
    print(f"[v0] ✓ Database connection established")
    
    cursor = connection.cursor()
    try:
        print(f"[v0] Executing INSERT query...")
        cursor.execute('''
            INSERT INTO panels (panel_id, user_id, panel_type, server_ip, server_port, 
                               username, password, web_path, server_username, server_password, ssh_port, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (panel_id, user_id, '3x-ui', server_ip, server_port, username, password, web_path, 
              server_username, server_password, ssh_port, 'active'))
        
        print(f"[v0] INSERT query executed, affected rows: {cursor.rowcount}")
        
        connection.commit()
        print(f"[v0] ✓ Transaction committed successfully")
        return True
    except Error as e:
        print(f"[v0] ✗ Database error in add_3xui_panel:")
        print(f"[v0]   Error code: {e.errno if hasattr(e, 'errno') else 'N/A'}")
        print(f"[v0]   Error message: {str(e)}")
        return False
    finally:
        cursor.close()
        connection.close()
        print(f"[v0] Database connection closed")

def get_panel_config(panel_id):
    """Get panel configuration details"""
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT panel_type, server_ip, ssh_port, server_username, server_password, subdomain, db_password
            FROM panels
            WHERE panel_id = %s
        ''', (panel_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'panel_type': result[0],
                'server_ip': result[1],
                'ssh_port': result[2],
                'server_username': result[3],
                'server_password': result[4],
                'subdomain': result[5],
                'db_password': result[6]
            }
        return None
    except Error as e:
        print(f"خطا در دریافت کانفیگ پنل: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def delete_panel(panel_id):
    """Delete panel from database"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('DELETE FROM panels WHERE panel_id = %s', (panel_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در حذف پنل: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_marzban_panel(panel_id, user_id, server_ip, server_port, username, password, subdomain, panel_url, server_username, server_password, ssh_port):
    """Add Marzban panel to database"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO panels (panel_id, user_id, panel_type, server_ip, server_port, 
                               username, password, web_path, server_username, server_password, ssh_port, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (panel_id, user_id, 'marzban', server_ip, server_port, username, password, panel_url, 
              server_username, server_password, ssh_port, 'active'))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره پنل Marzban: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_pasarguard_panel(panel_id, user_id, server_ip, server_port, username, password, subdomain, panel_url, server_username, server_password, ssh_port, db_password=None):
    """Add Pasarguard panel to database"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO panels (panel_id, user_id, panel_type, server_ip, server_port, 
                               username, password, web_path, server_username, server_password, ssh_port, subdomain, db_password, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (panel_id, user_id, 'pasarguard', server_ip, server_port, username, password, panel_url, 
              server_username, server_password, ssh_port, subdomain, db_password, 'active'))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره پنل Pasarguard: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_marzneshin_panel(panel_id, user_id, server_ip, server_port, username, password, subdomain, panel_url, server_username, server_password, ssh_port):
    """Add Marzneshin panel to database"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO panels (panel_id, user_id, panel_type, server_ip, server_port, 
                               username, password, web_path, server_username, server_password, ssh_port, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (panel_id, user_id, 'marzneshin', server_ip, server_port, username, password, panel_url, 
              server_username, server_password, ssh_port, 'active'))
        
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در ذخیره پنل Marzneshin: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_all_users():
    """Get all users with their service counts"""
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT 
                u.user_id, 
                u.username, 
                u.first_name,
                u.created_at,
                COUNT(DISTINCT t.tunnel_id) as tunnel_count,
                COUNT(DISTINCT p.panel_id) as panel_count
            FROM users u
            LEFT JOIN tunnels t ON u.user_id = t.user_id
            LEFT JOIN panels p ON u.user_id = p.user_id
            GROUP BY u.user_id, u.username, u.first_name, u.created_at
            ORDER BY u.created_at DESC
        ''')
        
        users = cursor.fetchall()
        return users
    except Error as e:
        print(f"خطا: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_user_info(user_id):
    """Get detailed info for a specific user"""
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT user_id, username, first_name, created_at
            FROM users
            WHERE user_id = %s
        ''', (user_id,))
        
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"خطا: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_all_users_basic():
    """Get all users basic info for broadcasting"""
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT user_id, username, first_name
            FROM users
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        return users
    except Error as e:
        print(f"خطا: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def add_shared_access(owner_id, admin_id):
    """Add shared access for an admin to manage owner's services"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO shared_access (owner_id, admin_id, is_active) VALUES (%s, %s, TRUE) ON DUPLICATE KEY UPDATE is_active = TRUE, updated_at = CURRENT_TIMESTAMP",
            (owner_id, admin_id)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"خطا در افزودن دسترسی: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def remove_shared_access(owner_id, admin_id):
    """Remove shared access for an admin"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM shared_access WHERE owner_id = %s AND admin_id = %s",
            (owner_id, admin_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"خطا در حذف دسترسی: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def toggle_shared_access(owner_id, admin_id):
    """Toggle active status of shared access"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "UPDATE shared_access SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP WHERE owner_id = %s AND admin_id = %s",
            (owner_id, admin_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"خطا در تغییر وضعیت دسترسی: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_shared_admins(owner_id):
    """Get list of admins who have access to owner's account"""
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    try:
        cursor.execute('''
            SELECT sa.access_id, sa.admin_id, u.username, u.first_name, sa.is_active, sa.created_at
            FROM shared_access sa
            JOIN users u ON sa.admin_id = u.user_id
            WHERE sa.owner_id = %s
            ORDER BY sa.created_at DESC
        ''', (owner_id,))
        
        return cursor.fetchall()
    except Error as e:
        print(f"خطا در دریافت لیست ادمین‌ها: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_accessible_accounts(admin_id):
    """Get list of accounts that admin has access to"""
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    try:
        cursor.execute('''
            SELECT sa.access_id, sa.owner_id, u.username, u.first_name, sa.is_active, sa.created_at
            FROM shared_access sa
            JOIN users u ON sa.owner_id = u.user_id
            WHERE sa.admin_id = %s AND sa.is_active = TRUE
            ORDER BY sa.created_at DESC
        ''', (admin_id,))
        
        return cursor.fetchall()
    except Error as e:
        print(f"خطا در دریافت لیست اکانت‌ها: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def check_access_permission(admin_id, owner_id):
    """Check if admin has active access to owner's account"""
    if admin_id == owner_id:
        return True
    
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "SELECT is_active FROM shared_access WHERE owner_id = %s AND admin_id = %s",
            (owner_id, admin_id)
        )
        result = cursor.fetchone()
        return result and result[0] == 1
    except Error as e:
        print(f"خطا در بررسی دسترسی: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_user_tunnels_with_access(user_id):
    """Get tunnels that user owns or has access to"""
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    try:
        cursor.execute('''
            SELECT t.tunnel_id, t.tunnel_type, t.status, 
                   tc.iran_ip, tc.foreign_ip, tc.transport_type, tc.tunnel_ports, t.created_at,
                   t.user_id
            FROM tunnels t
            LEFT JOIN tunnel_configs tc ON t.tunnel_id = tc.tunnel_id
            WHERE t.user_id = %s
               OR t.user_id IN (
                   SELECT owner_id FROM shared_access 
                   WHERE admin_id = %s AND is_active = TRUE
               )
            ORDER BY t.created_at DESC
        ''', (user_id, user_id))
        
        return cursor.fetchall()
    except Error as e:
        print(f"خطا در دریافت تانل‌ها: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_user_panels_with_access(user_id):
    """Get panels that user owns or has access to"""
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    try:
        cursor.execute('''
            SELECT panel_id, panel_type, server_ip, server_port, username, password, 
                   web_path, status, created_at, subdomain, db_password, user_id
            FROM panels
            WHERE user_id = %s
               OR user_id IN (
                   SELECT owner_id FROM shared_access 
                   WHERE admin_id = %s AND is_active = TRUE
               )
            ORDER BY created_at DESC
        ''', (user_id, user_id))
        
        return cursor.fetchall()
    except Error as e:
        print(f"خطا در دریافت پنل‌ها: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_user_by_id(user_id):
    """Get user info by user_id"""
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT user_id, username, first_name, created_at
            FROM users
            WHERE user_id = %s
        ''', (user_id,))
        
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"خطا: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_force_join_status():
    """Get force join enabled/disabled status"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT is_enabled FROM force_join_settings WHERE id = 1")
        result = cursor.fetchone()
        return result[0] if result else False
    except Error as e:
        print(f"Error getting force join status: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def set_force_join_status(is_enabled):
    """Enable or disable force join"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE force_join_settings SET is_enabled = %s WHERE id = 1",
            (is_enabled,)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error setting force join status: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_force_join_channel(channel_id, channel_username=None, channel_title=None):
    """Add a channel to force join list"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO force_join_channels (channel_id, channel_username, channel_title) 
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE channel_username = %s, channel_title = %s""",
            (channel_id, channel_username, channel_title, channel_username, channel_title)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error adding force join channel: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def remove_force_join_channel(channel_id):
    """Remove a channel from force join list"""
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM force_join_channels WHERE channel_id = %s", (channel_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"Error removing force join channel: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_all_force_join_channels():
    """Get all force join channels"""
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT channel_id, channel_username, channel_title FROM force_join_channels")
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting force join channels: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_user_wallet(user_id):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM user_wallets WHERE user_id = %s', (user_id,))
            wallet = cursor.fetchone()
            
            if not wallet:
                cursor.execute('''
                    INSERT INTO user_wallets (user_id, balance) 
                    VALUES (%s, 0.00)
                ''', (user_id,))
                connection.commit()
                cursor.execute('SELECT * FROM user_wallets WHERE user_id = %s', (user_id,))
                wallet = cursor.fetchone()
            
            if wallet and 'balance' in wallet:
                wallet['balance'] = float(wallet['balance'])
            
            return wallet
        except Error as e:
            print(f"Error getting user wallet: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None

def update_wallet_phone(user_id, phone_number):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE user_wallets 
                SET phone_number = %s, phone_verified = TRUE 
                WHERE user_id = %s
            ''', (phone_number, user_id))
            connection.commit()
            return True
        except Error as e:
            print(f"Error updating wallet phone: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def create_transaction(user_id, amount, payment_method, receipt_photo=None):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, payment_method, receipt_photo, status)
                VALUES (%s, %s, %s, %s, 'pending')
            ''', (user_id, amount, payment_method, receipt_photo))
            connection.commit()
            transaction_id = cursor.lastrowid
            return transaction_id
        except Error as e:
            print(f"Error creating transaction: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None

def get_transaction(transaction_id):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM transactions WHERE id = %s', (transaction_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting transaction: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None

def update_transaction_status(transaction_id, status, admin_note=None):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            if admin_note:
                cursor.execute('''
                    UPDATE transactions 
                    SET status = %s, admin_note = %s 
                    WHERE id = %s
                ''', (status, admin_note, transaction_id))
            else:
                cursor.execute('''
                    UPDATE transactions 
                    SET status = %s 
                    WHERE id = %s
                ''', (status, transaction_id))
            connection.commit()
            return True
        except Error as e:
            print(f"Error updating transaction status: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def add_balance(user_id, amount):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE user_wallets 
                SET balance = balance + %s 
                WHERE user_id = %s
            ''', (amount, user_id))
            connection.commit()
            return True
        except Error as e:
            print(f"Error adding balance: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def get_pending_transactions():
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT t.*, u.username, u.first_name 
                FROM transactions t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.status = 'pending'
                ORDER BY t.created_at DESC
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting pending transactions: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []
