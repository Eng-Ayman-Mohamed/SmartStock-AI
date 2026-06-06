import requests, json

base = 'http://localhost:8000/api/inventory'

# Login with the user we just created
login_data = {'email': 'admin@test.com', 'password': '123'}
r = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
print(f'POST /auth/login/ (email): {r.status_code}')
if r.status_code == 200:
    token = r.json().get('access')
    print('  Login OK with email field')
else:
    # Try with username field
    login_data = {'username': 'admin@test.com', 'password': '123'}
    r = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
    print(f'POST /auth/login/ (username): {r.status_code}')
    if r.status_code == 200:
        token = r.json().get('access')
        print('  Login OK with username field')
    else:
        print(f'  Login failed: {r.text[:300]}')
        token = None

if not token:
    print('\nCannot proceed without token. Exiting.')
    exit()

headers = {'Authorization': f'Bearer {token}'}

# Test all endpoints
print('\n--- Testing Inventory Endpoints ---')

# List products
r = requests.get(f'{base}/products/', headers=headers)
print(f'GET /products/: {r.status_code}', end='')
data = r.json()
if r.status_code == 200:
    print(f' | count={len(data.get("results", []))} | pagination keys={list(data.keys())}')
else:
    print(f' | {data}')

# Create product
product = {'name': 'Test Product', 'description': 'Test desc', 'category': 'Electronics'}
r = requests.post(f'{base}/products/', json=product, headers=headers)
print(f'POST /products/: {r.status_code}', end='')
if r.status_code == 201:
    pid = r.json()['id']
    print(f' | id={pid}')
    
    # Retrieve
    r = requests.get(f'{base}/products/{pid}/', headers=headers)
    print(f'GET /products/{pid}/: {r.status_code}')
    
    # Update
    r = requests.patch(f'{base}/products/{pid}/', json={'name': 'Updated Product'}, headers=headers)
    print(f'PATCH /products/{pid}/: {r.status_code}')
    
    # Delete
    r = requests.delete(f'{base}/products/{pid}/', headers=headers)
    print(f'DELETE /products/{pid}/: {r.status_code}')
else:
    print(f' | {r.text[:200]}')

# SKUs
r = requests.get(f'{base}/skus/', headers=headers)
print(f'GET /skus/: {r.status_code}')

# Stock levels
r = requests.get(f'{base}/stock-levels/', headers=headers)
print(f'GET /stock-levels/: {r.status_code}')

# Low stock
r = requests.get(f'{base}/stock-levels/low_stock/', headers=headers)
print(f'GET /stock-levels/low_stock/: {r.status_code}')

# Sales records
r = requests.get(f'{base}/sales-records/', headers=headers)
print(f'GET /sales-records/: {r.status_code}')

# Pagination
r = requests.get(f'{base}/products/?page_size=5', headers=headers)
print(f'GET /products/?page_size=5: {r.status_code} | pagination OK')

# Search
r = requests.get(f'{base}/products/?search=Test', headers=headers)
print(f'GET /products/?search=Test: {r.status_code} | search OK')

# Filter
r = requests.get(f'{base}/products/?category=Electronics', headers=headers)
print(f'GET /products/?category=Electronics: {r.status_code} | filter OK')

print('\nAll endpoint tests complete.')
