with open('pytest.txt', encoding='utf-16', errors='ignore') as f:
    for line in f:
        if 'FAILED' in line or 'ERROR' in line:
            print(line.strip()[:150])
