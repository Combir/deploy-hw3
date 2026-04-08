import requests

BASE_URL = "http://127.0.0.1:8000" 

def test_idor():
    headers = {"X-User": "alice"}
    response = requests.get(f"{BASE_URL}/files/2", headers=headers)
    assert response.status_code == 404
    print("Test 1 (IDOR): Passed")

def test_access():
    headers = {"X-User": "alice"}
    response = requests.get(f"{BASE_URL}/files/1", headers=headers)
    assert response.status_code == 200
    print("Test 2 (Access): Passed")

def test_admin_delete():
    headers = {"X-User": "admin"}
    response = requests.delete(f"{BASE_URL}/files/2", headers=headers)
    assert response.status_code == 200
    print("Test 3 (Admin Delete): Passed")

if __name__ == "__main__":
    print(f"Connecting to {BASE_URL}...")
    try:
        test_idor()
        test_access()
        test_admin_delete()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")