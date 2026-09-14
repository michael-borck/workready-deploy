"""Run the privileged UI and isolated static previews on loopback."""
import threading
import uvicorn
from app import app, preview_app, BOOTSTRAP_TOKEN

if __name__ == '__main__':
    print('Console: http://127.0.0.1:7788', flush=True)
    print('Local console key: ' + BOOTSTRAP_TOKEN, flush=True)
    print('Static previews: http://localhost:7789/<company>/', flush=True)
    threading.Thread(target=lambda: uvicorn.run(preview_app, host='127.0.0.1', port=7789, access_log=False), daemon=True).start()
    uvicorn.run(app, host='127.0.0.1', port=7788, access_log=False)
