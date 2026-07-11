with open('sm_cov.txt', encoding='utf-16', errors='ignore') as f:
    lines = f.readlines()
    for line in lines[-20:]:
        print(line.strip())
