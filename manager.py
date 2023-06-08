import uvicorn

if __name__ == '__main__':
    # uvicorn main:app --host 0.0.0.0 --port 5000 --proxy-headers --forwarded-allow-ips='*'
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True, proxy_headers=True, forwarded_allow_ips='*')
