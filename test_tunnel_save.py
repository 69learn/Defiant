#!/usr/bin/env python3
import sys
from database import get_connection, add_vxlan_tunnel, get_user_tunnels, add_user

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    conn = get_connection()
    if conn:
        print("✅ Database connection successful")
        conn.close()
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_add_user():
    """Test adding a user"""
    print("\nTesting add user...")
    user_id = 123456789
    username = "testuser"
    first_name = "Test User"
    
    if add_user(user_id, username, first_name):
        print(f"✅ User {user_id} added successfully")
        return True
    else:
        print(f"❌ Failed to add user {user_id}")
        return False

def test_add_tunnel():
    """Test adding a tunnel"""
    print("\nTesting add tunnel...")
    tunnel_id = "TEST-12345678"
    user_id = 123456789
    iran_ip = "1.2.3.4"
    foreign_ip = "5.6.7.8"
    service_ports = "8080,8443"
    
    if add_vxlan_tunnel(tunnel_id, user_id, iran_ip, foreign_ip, service_ports):
        print(f"✅ Tunnel {tunnel_id} added successfully")
        return True
    else:
        print(f"❌ Failed to add tunnel {tunnel_id}")
        return False

def test_get_tunnels():
    """Test retrieving tunnels"""
    print("\nTesting get tunnels...")
    user_id = 123456789
    
    tunnels = get_user_tunnels(user_id)
    if tunnels is not None:
        print(f"✅ Retrieved {len(tunnels)} tunnels for user {user_id}")
        for tunnel in tunnels:
            print(f"  - Tunnel: {tunnel[0]} | Type: {tunnel[1]} | IPin: {tunnel[3]} | IPout: {tunnel[4]} | Ports: {tunnel[6]}")
        return True
    else:
        print(f"❌ Failed to retrieve tunnels")
        return False

if __name__ == "__main__":
    print("="*50)
    print("Database Connection Test")
    print("="*50)
    
    if not test_database_connection():
        print("\n❌ Please check your database configuration in .env file")
        sys.exit(1)
    
    test_add_user()
    test_add_tunnel()
    test_get_tunnels()
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)
